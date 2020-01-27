
# LobsteroBOT
A discord bot badly written by somebody with way too much time.
Lobstero is publicly available on discord already - invite it to your server using [this link](https://discordapp.com/api/oauth2/authorize?client_id=642538503711752234&scope=bot).

## Bugs
There will be plenty of these. Open an issue and I'll get to it as soon as possible.

## Contributing
Any and all pull requests are welcomed. However, before diving head-first into a big rewrite, open an issue or talk it out with me on Discord - you can find me at Kaylynn#4444. I'm happy to help with anything you may want to do, but I need to be told for that to happen.

## Installation
 I would really, really prefer if you did not run an instance of Lobstero. One is enough. However, I can't stop you, so if you're that type:

 - You'll need git. On windows, GitHub Desktop or the (much better) Git Bash will suffice. If you're on Linux I don't need to explain this to you. 
 - Python 3.6+ is required, but the bot has only been tested with 3.7.6 and above. Use Python 3.6 at your own peril!
 - The experimental discord.py extension [ext.menus](https://github.com/Rapptz/discord-ext-menus) is required.
 - Use [Poetry](https://python-poetry.org/) to install other required dependencies:
 - (something about using poetry here)

## After installation
Copy lobstero_config.example.py, rename to lobstero_config.py and edit. It's a lengthy config file, and I recommend taking your time filling everything in. I've tried to document what everything does as much as possible, but you'll have to figure out parts of it yourself.
Make sure to have a Redis database running as well. Lobstero's markov functionality depends on this, and active learning can be turned on through the config file.
Once you've got all of this running, run launcher.py. Everything should be automatic from there.


