# Pom Bot

The default pom bot.

## Installation

You will need to install:

1. Python 3.8 or newer.
2. The Python dependencies (`pip install -r requirements.txt`).
3. MySQL database running on the default port (3306/tcp).

## Usage

Clone the repository and copy `.env.example` to `.env` and customize to match
your system, then open a terminal in the project directory and run `make`.

This will run unit tests and start the bot with Python optimizations applied
(NB: On Windows, you may need to install MinGW or MinGW64 to use the `make`
command).

## Related Projects

* Originally inspired by [Python Pom Bot][python-pom-bot] and the amazing KOA
  community.

[python-pom-bot]: https://github.com/Moesgaarda/python-pom-bot
