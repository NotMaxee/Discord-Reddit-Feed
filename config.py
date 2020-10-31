# Configuration for the Discord Reddit Feed

# The name of the tracked subreddit.
subreddit = "SUBREDDIT NAME"

# The interval in seconds in which to check for new posts.
# Do not set this too low, or you might spam reddit until you hit a ratelimit.
fetch_interval = 300

# Set to True to fetch the subreddit icon and use it as the webhook avatar.
subreddit_avatar = True

# Set to True to use the subreddit name as the webhook username.
subreddit_username = True

# Set to True to fetch the subreddit colour and use it as the webhook avatar.
subreddit_colour = True

# The URL of the webhook through which posts should be sent.
post_webhook = "WEBHOOK URL"

# An optional URL of a webhook through which errors should be sent.
error_webhook = "WEBHOOK URL"
