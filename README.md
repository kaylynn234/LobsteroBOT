
# LobsteroBOT
A bad discord bot written by somebody with way too much time.
Lobstero is publicly available on discord already - invite it to your server using [this link](https://discordapp.com/api/oauth2/authorize?client_id=642538503711752234&scope=bot).

## Installation
I'm gonna level with you: I never actually used Poetry. It didn't play nice with a few of my dependencies, so I dropped it. Lobstero and Poetry have been a hoax all along.
Your parents have lied to you.

I can see almost no reason why you would want to self-host Lobstero.
The bot is available on discord already - see heading. Why are you doing this?
But if you really wanna take it upon yourself:

 - Don't use Python 2. I can only guarantee support for Python 3.7 and above, but in theory Lobstero should run on Python 3.6 as well.
 - Start by installing dependencies. These can be found in requirements.txt. I assume you know how pip works. Tough luck if you don't. Please use a venv.
 - Additionally, a few commands require the system package wkhtmltopdf. Get that all installed and set up.
 - Get a PostgreSQL server and optionally a Redis server running. PostgreSQL is used for persistent bot storage, and Redis is used for markov data. Keep track of the details for both.
 - Run the download_content script. This will download a bunch of images that you'll want to have around.
 - Copy lobstero_config_example.py, rename to lobstero_config.py, and edit it in your favorite text manipulation program. It should be easy enough to understand.
 - Run launcher.py to actually run the bot.

## Contributing
Feel free.


