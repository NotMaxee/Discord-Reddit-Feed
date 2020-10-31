"""
MIT License

Copyright (c) 2020 Maxee (maxee.dev@gmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import datetime
import io
import json
import logging
import logging.handlers
import os
import sys
import time
import traceback

import discord
import requests


def setup_logging():
    """Set up the logging module."""
    path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(path, "logs")

    if not os.path.exists(path):
        os.mkdir(path)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    streamHandler = logging.StreamHandler(stream=sys.stdout)

    fileHandler = logging.handlers.TimedRotatingFileHandler(
        os.path.join(path, "log.txt"),
        when="midnight",
        backupCount=7,
        encoding="utf-8",
        utc=True,
    )

    fmt = "{asctime} | {levelname:<8} | {name}: {message}"
    date = "%d.%m.%Y %H:%M:%S"
    formatter = logging.Formatter(fmt, date, style="{")

    for handler in (streamHandler, fileHandler):
        handler.setFormatter(formatter)
        logger.addHandler(handler)


def truncate(string, length=100):
    """
    Truncate a string to the given length.

    Parameters
    ----------
    string: str
        The string to truncate.
    length: Optional[int]
        The length to trucate the string to.

    Returns
    -------
    str
        The truncated string.
    """
    if len(string) <= length:
        return string

    return string[length - 1 :] + "…"


class DiscordRedditFeed:
    """Sends new posts on a given subreddit through a Discord webhook."""

    def __init__(self):
        self.logger = logging.getLogger("poster")
        self.logger.info("Setting up poster.")

        self._headers = {"User-Agent": "RedditPoster/1.0"}
        self._embed_colour = 0xFF4500  # Reddit brand colour.
        self._webhook_args = dict()
        self._post_webhook = None
        self._error_webhook = None

    @property
    def post_webhook(self):
        """discord.Webhook: The webhook to send new posts through."""
        if self._post_webhook is None:
            url = self.config.post_webhook
            adapter = discord.RequestsWebhookAdapter()

            try:
                self._post_webhook = discord.Webhook.from_url(url, adapter=adapter)
            except Exception as e:
                self.logger.exception("Could not create post webhook!", exc_info=e)
                sys.exit(1)

        return self._post_webhook

    @property
    def error_webhook(self):
        """Optional[discord.Webhook]: Webhook to send errors through."""
        if self.config.error_webhook is None:
            return None

        if self._error_webhook is None:
            url = self.config.error_webhook
            adapter = discord.RequestsWebhookAdapter()
            try:
                self._error_webhook = discord.Webhook.from_url(url, adapter=adapter)
            except Exception as e:
                self.logger.exception("Could not create error webhook!", exc_info=e)
                sys.exit(1)

        return self._error_webhook

    @property
    def config(self):
        """The configuration object."""
        return __import__("config")

    def fetch_about(self):
        """
        Dict[str, Any]: The about.json data of the subreddit.
        """
        # See: https://www.reddit.com/dev/api#GET_about
        url = f"https://www.reddit.com/r/{self.config.subreddit}/about.json"
        resp = requests.get(url, headers=self._headers)

        try:
            resp.raise_for_status()
        except Exception as e:
            self.send_error("Could not fetch about.json!", e)
            return None
        else:
            data = resp.json()
            return data["data"]

    def fetch_posts(self, before=None, limit=10):
        """
        Fetch the latest posts from the subreddit.

        Parameters
        ----------
        before: Optional[str]
            The fullname of the post to use as an anchor point.
            When this is not specified, posts are fetched by their
            age instead.
        limit: Optional[int]
            The maximum amount of posts to fetch.

        Returns
        -------
        Optional[List[Dict[str, Any]]]
            A list of post data. Returns ``None`` when an error
            occured and the list could not be fetched.
        """
        # See: https://www.reddit.com/dev/api#GET_new
        url = f"https://www.reddit.com/r/{self.config.subreddit}/new.json"
        params = {"limit": limit}
        if before:
            params["before"] = before

        resp = requests.get(url, headers=self._headers, params=params)

        try:
            resp.raise_for_status()
        except Exception as e:
            self.send_error("Could not fetch new.json!", e)
            return None
        else:
            data = resp.json()
            return data["data"]["children"]

    def send_post(self, data):
        """
        Send a reddit post through the posts webhook.

        Parameters
        ----------
        data: Dict[str, Any]
            The post data.
        """
        title = data["title"]
        selftext = data["selftext"]

        author = data["author"]
        author_url = f"https://www.reddit.com/user/{author}"
        permalink = "https://www.reddit.com" + data["permalink"]
        created_at = datetime.datetime.fromtimestamp(data["created_utc"])
        created_at = created_at.replace(tzinfo=datetime.timezone.utc)
        post_hint = data.get("post_hint", None)

        is_spoiler = data["spoiler"]
        is_nsfw = data["over_18"]

        # Build the embed...
        embed = discord.Embed()
        embed.url = permalink
        embed.title = truncate(title, 256)
        embed.timestamp = created_at
        embed.colour = self._embed_colour

        embed_author = f"New post on /r/{self.config.subreddit}"

        if post_hint == "image":
            embed_author = f"New image post on /r/{self.config.subreddit}"
        elif post_hint == "link":
            embed_author = f"New link post on /r/{self.config.subreddit}"

        embed.set_author(name=truncate(embed_author, 256), url=permalink)

        image = None

        if not (is_spoiler or is_nsfw):
            thumbnail = data["thumbnail"]

            if post_hint == "image":
                image = data["url"]
            elif thumbnail not in (None, "spoiler", "self"):
                image = thumbnail

        if image:
            embed.set_image(url=image)

        if selftext:
            embed.description = truncate(selftext, 2048)

        embed.add_field(name="Post Author", value=f"[{author}]({author_url})")

        content_warnings = []
        if is_spoiler:
            content_warnings.append("spoiler")
        if is_nsfw:
            content_warnings.append("nsfw")

        if content_warnings:
            content_warning = ", ".join(content_warnings)
        else:
            content_warning = "none"

        embed.add_field(name="Content Warning", value=content_warning)

        # ... and send it.
        self.post_webhook.send(embed=embed, **self._webhook_args)

    def send_error(self, message, error):
        """
        Log an error and attempt to send it through the error webhook.

        Parameters
        ----------
        message: str
            The log message to include.
        error: Exception
            The error to log.
        """
        self.logger.exception(message, exc_info=error)

        webhook = self.error_webhook
        if webhook is None:
            return

        # Build an embed for the error...
        embed = discord.Embed(title="Error Report", description=message)
        embed.timestamp = datetime.datetime.utcnow()

        trace = traceback.format_exception(None, error, error.__traceback__)
        trace = "".join(trace)

        if len(trace) > 1024:
            shown = truncate(trace, 1024)
        else:
            shown = trace

        embed.add_field(name="Traceback", value=f"```\n{shown}```", inline=False)

        buffer = io.BytesIO(trace.encode("utf-8"))
        file = discord.File(buffer, f"traceback.txt")

        webhook.send(embed=embed, file=file, **self._webhook_args)

    def run(self):
        """
        Start fetching posts from the subreddit.
        """
        # Set up the webhook avatar and username if enabled.
        if self.config.subreddit_username:
            self._webhook_args["username"] = "r/" + self.config.subreddit

        if self.config.subreddit_avatar or self.config.subreddit_colour:
            data = self.fetch_about()

            if self.config.subreddit_avatar:
                icon_img = data["icon_img"]
                if icon_img:  # icon_img can be ""
                    self._webhook_args["avatar_url"] = icon_img

            if self.config.subreddit_colour:
                colour = data["key_color"]
                if colour:  # key_color can be ""
                    self._embed_colour = int(colour[1:], 16)

        # Prepare fetch loop.
        before = None  # Full name of a post to use as an anchor.
        limit = 100  # The maximum is 100.

        # As we do not want to retroactively post things from the subreddit,
        # we fetch the newest post and use it as the anchor point.
        posts = self.fetch_posts(limit=1)
        if len(posts) == 1:
            before = posts[0]["data"]["name"]

        # Start fetch loop.
        self.logger.info("Starting fetch loop.")
        while True:
            fetch = True
            while fetch:
                self.logger.debug(f"Fetching posts (before={before}, limit={limit})")
                posts = self.fetch_posts(before=before, limit=limit)
                self.logger.debug(f"Fetched {len(posts)} post(s).")
                if len(posts) == 0:
                    break

                # Sort posts by date so that newest appear last.
                posts = sorted(posts, key=lambda d: d["data"]["created_utc"])

                for post in posts:
                    try:
                        self.send_post(post["data"])
                    except Exception as e:
                        url = "https://www.reddit.com" + post["data"]["permalink"]
                        name = post["data"]["name"]
                        self.send_error(f"Could not send post [{name}]({url})!", e)
                        return

                    before = post["data"]["name"]

                    # Slow down if we are sending a lot of posts. This is not
                    # going to prevent an eventual 429 if you are spamming the
                    # webhook with up to 100 posts. Thankfully, discord.py
                    # handles the ratelimit for us.
                    if len(posts) > 30:
                        time.sleep(1)

                # If we reached the post limit, we may be further behind.
                # No subreddit should be this busy, but hey. Edge cases!
                fetch = len(posts) == limit

            # Wait a bit between fetches.
            time.sleep(self.config.fetch_interval)


if __name__ == "__main__":
    setup_logging()
    poster = DiscordRedditFeed()
    poster.run()
