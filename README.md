
# LobsteroBOT
A discord bot badly written by somebody with way too much time.
Lobstero is publicly available on discord already - invite it to your server using [this link](https://discordapp.com/api/oauth2/authorize?client_id=642538503711752234&scope=bot).

## Bugs
There will be plenty of these. Open an issue and I'll get to it as soon as possible.

## Contributing
Any and all pull requests are welcomed. However, before diving head-first into a big rewrite, open an issue or talk it out with me on Discord - you can find me at Kaylynn#4444. I'm happy to help with anything you may want to do, but I need to be told for that to happen.

## Installation
 I would really, really prefer if you did not run an instance of Lobstero. One is enough. However, I can't stop you, so if you're that type:

 - You'll need Poetry to install dependencies. This is to save everyone an aneurysm.
 - You'll need git. On windows, GitHub Desktop or the (much better) Git Bash will suffice. If you're on Linux I don't need to explain this to you. 
 - Python 3.7+ is required. While technically compatible with Python 3.6, the bot has only been tested with 3.7.6 and above. Use Python 3.6 at your own peril!
 - With all of this in hand, use [Poetry](https://python-poetry.org/) to install required dependencies and then continue from there. It's rather simple:

```sh
poetry install
# "copy" on windows, instead of "cp"
cp lobstero_config.example.py  lobstero_config.py
# read and edit to taste in your favorite editor
# "python" on windows, instead of "python3"
poetry run python3 launcher.py
```

## Additional notes

Make sure to have a Redis database running as well. Lobstero's markov functionality depends on this, and active learning can be turned on through the config file.
Database schema for everything *should* be handled automatically. No guarantees, though.


