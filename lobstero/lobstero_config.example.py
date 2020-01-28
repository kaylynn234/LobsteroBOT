"""This is the configuration file for Lobstero."""
from unittest import mock


class LobsteroCredentials():

    def __init__(self):

        self.auth, self.config = mock.Mock(), mock.Mock()

        # Welcome to Lobstero's configuration file!
        # The fields below are what you'll need to edit for Lobstero to function properly.
        # Turn on Developer Mode in discord settings to retrieve IDs.

        # Strings should be encompassed by double quotes, like so:
        # "This is an example string!"
        # Integers are just numbers and don't need anything special around them:
        # 1234567890

        # Token: Should be a string. This is your bot's token.
        # NEVER give this out to ANYBODY.
        # It gives them complete control of the bot.
        # Think of it like a password.
        self.auth.token = ""

        # Owner Name: Should be a string.
        # This appears in the information commands and some other places.
        self.config.owner_name = "Kaylynn#4444"

        # Owner ID: Should be a list of integers.
        # This dictates who can use the Owner commands.
        self.config.owner_id = [123456789]

        # Image Channel: Should be an integer.
        # This is the ID for the channel images used for embeds will be sent to.
        # I suggest making a private/hidden channel in a disposable server for this
        # Will be removed later.
        self.config.image_channel = 123456789

        # Home Channel: Should be an integer.
        # This is the ID for the channel where messages about bot status are sent.
        self.config.home_channel = 123456789

        # Database Address: Should be a string.
        # This is what is used to connect to the markov database.
        # See readme for more info on this.
        # Generally all you need to do here is change the port (7379) to something else.
        self.auth.database_address = "redis_async://localhost:7379;db=0"

        # Cat API key: Should be a string. Get a key from https://thecatapi.com/
        # You'll need this if you want <cat to work.
        # Set it to "None" to disable the cat command.
        self.auth.cat_api_key = "xxxx"

        # Spotify Web API client ID: Should be a string.
        # Get this from https://developer.spotify.com/documentation/web-api/
        # You'll need this if you want <suggestmusic to work.
        # Set it to "None" to disable the suggestmusic command.
        self.auth.spotify_client_id = "xxxx"

        # Spotify Web API client secret: Should be a string.
        # Get this from https://developer.spotify.com/documentation/web-api/
        # You'll need this if you want <suggestmusic to work.
        self.auth.spotify_client_secret = "xxxx"

        # Spotify user URI: Should be a string.
        # Get this by going to your profile, clicking the three-dot menu and "share"
        # Than click "copy Spotify URI." Put that value here.
        self.config.spotify_user_uri = "xxxx"

        # Spotify playlist URI: Should be a string.
        # Get this by going to your playlist, clicking the three-dot menu and "share"
        # Than click "copy Spotify URI." Put that value here.
        self.config.spotify_playlist_uri = "xxxx"

        # Support server invite: Should be a string.
        # An invite link that allows people to join the support server for the bot.
        self.config.support_server_url = "https://discord.gg/"

        # WKHtmlToImage path: SHould be a string.
        # This is what makes garkov work.
        # Download a https://wkhtmltopdf.org/ binary and put it somewhere.
        # Put the path directly to wkhtmltoimage.exe here.
        # If you're on Linux, set this to None - you don't need to provide a path to a binary.
        self.config.wkhtmltoimage_path = 'C:/Program Files/wkhtmltopdf/bin/wkhtmltoimage.exe'

        # These are the default prefixes if a server-specific prefix isn't set.
        self.config.prefixes = [
            "<@!642538503711752234> command ",
            "<@642538503711752234> command ",
            "<<"]

        # You probably don't want to change this.
        self.config.case_insensitive = True

        # FFMPEG path: SHould be a string
        self.config.ffmpeg = "..."

        # The section below is used directly by the bot.
        # It shouldn't be changed unless you know what you're doing.
        # Editing some of these these will almost certainly break things!

        # Only change this if you're a masochist.
        self.config.cogs_to_load = [
            "base",
            "moderation",
            "fun",
            "owner",
            "utility",
            # "editing",
            "customization",
            "eco",
            "customreacts"
        ]
