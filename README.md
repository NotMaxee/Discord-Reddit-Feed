<h1 align="center">Reddit to Discord Webhook Poster</h1>

<p align="center">
  <a href="#overview">Overview</a>
  •
  <a href="#setup">Setup</a>
  •
  <a href="#license">License</a>
  <br>
</p>

<!-- Content -->

## Overview

This is a simple script that allows you to track new posts for one subreddit
at a time and send them through a Discord webhook. While this script is only
fit for a single subreddit, I am sure if you wanted to, you could easily
modify it to support multiple.

While this script works fine for me, there may be some issues with more active
subreddits. When observing those, please make sure you watch out for any
ratelimits that you might hit on both the ends of Discord and Reddit.

That being said, feel free to adapt this script to your needs. There should be
enough documentation in the code to let you get started without much trouble.

## Setup

For starters, clone or download the repository. Depending on where you place
the files, you may need to adjust the service file (see
[Setting up a Service](#setting-up-a-service)).

To run this script you will need a Python version that is compatible with the
required versions of ``discord.py`` and ``requests``. Anything starting from
3.6 should be fine.

Install the requirements using ``pip install -r requirements.txt``.

### Configuration

Create a new ``config.py`` file using the ``config.py.template`` and update it
according to your needs. For your convenience, all available settings are also
listed below:

| Field                     | Type      | Description                                                               |
| :-                        | :-        | :-                                                                        |
| ``subreddit``             | ``str``   | Name of the tracked subreddit.                                            |
| ``fetch_interval``        | ``str``   | Interval in seconds in which to check for new posts.                      |
| ``subreddit_avatar``      | ``bool``  | Whether to use the subreddit icon as the webhook avatar.                  |
| ``subreddit_username``    | ``bool``  | Whether to use the subreddit name as the webhook username.                |
| ``subreddit_colour``      | ``bool``  | Whether to use the subreddit theme colour as the colour for post embeds.  |
| ``post_webhook``          | ``str``   | The URL of the webhook through which to send posts.                       |
| ``error_webhook``         | ``str``   | The URL of the webhook through which to send errors. Optional.            |

### Setting up a Service

If you want to set up the script to run as a service on Linux, you can use the
``discord-reddit-feed.service.template`` file to create a new systemd service.
Remove the ``.template`` extension and modify it according to your needs, then
copy it to ``/etc/systemd/system``.

| Field                 | Description                                         |
| :-                    | :-                                                  |
| ``User``              | Name of the user to run the script as.              |
| ``Group``             | Group of the user to run the script as.             |
| ``WorkingDirectory``  | Working directory of the script.                    |
| ``ExecStart``         | Path to the Python executable and the script file.  |

Reload the service list using ``sudo systemctl daemon-reload``, enable the
service using ``sudo systemctl enable discord-reddit-feed.service`` and start
the service using ``sudo systemctl start discord-reddit-feed.service``.

## License

This repository is released under the [MIT License](LICENSE). 
