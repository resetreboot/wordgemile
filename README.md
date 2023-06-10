# Wordgemile: A Wordle for Gemini servers

This is my stab at creating a Wordle that can be used by any CGI and Python enabled
gemini server. At the moment, this code has been running under Python 3.7 and above
and a Jetforce gemini server.

## Usage

### Creating the database

For the correct functioning of this code, you need to generate a database, with the
words. At this moment, it is designed to work with an SQLite database but if you
expect much traffic that can be a bit undesirable. Future improvement!

```bash

$ python3 wordgemile.py --load [word list file]

``` 

With that command, the script will load a new-line separated word list and create
a database ready for your server. 

You can also run the script to play on the command line and test it out. 

### Running on your server

The main entry point is the wordle.cgi file. Feel free to edit it to adjust the messaging
to the language of preference. Please follow the conventions on your Gemini server
to install and make sure the script runs. All the files (gemcgi.py, wordgemile.py and
__init__.py) should be visible to the .cgi file. 
