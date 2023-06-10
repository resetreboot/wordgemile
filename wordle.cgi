#!/usr/bin/python3

import os
import gemcgi
import wordgemile


def get_host():
    """
    Get the host and optionally the port
    """
    host = os.environ.get("SERVER_NAME")
    host = host.replace("/", "")
    port = os.environ.get("SERVER_PORT")

    if port != "1965":
        return f"{host}:{port}"

    else:
        return host


def call_path():
    path = os.environ.get('PATH_INFO')
    auth_type = os.environ.get('AUTH_TYPE')
    tls_serial = os.environ.get('TLS_CLIENT_SERIAL_NUMBER')
    tls_name = os.environ.get('REMOTE_USER')

    if "/game" in path:
        route = path.split("/")
        if len(route) > 2 and auth_type:
            game(route[2], tls_name, tls_serial)

        elif auth_type:
            new_game(tls_name, tls_serial)

        else:
            gemcgi.request_auth("A client certificate is required to play.")

    elif path == "/about":
        about()

    else:
        notfound()


def notfound():
    gemcgi.send_error("Path not found")


def about():
    script = os.environ.get("SCRIPT_NAME")
    host = get_host()

    text = """# Wordle Gemini

Small game to try to guess the word.

## Instructions

All words are composed of 5 letters. There can be repeated letters.
At each turn you will be shown the input word with a color code or a
mark that can be circular or square to give hints.

* Yellow - Circled: The letter is present, but the position is not correct.
* Green - Squared: The letter is in the correct place.
* No color, no marks: The letter is not present in the word to guess.

You have six tries to guess the word, good luck!

=> """

    text += f"gemini://{host}{script}/game Play"

    gemcgi.send_text(text)


def game(session_id, player, certid):
    word = os.environ.get("QUERY_STRING")
    script = os.environ.get("SCRIPT_NAME")
    host = get_host()

    game_session = wordgemile.Wordle("", player)

    try:
        game_session.load_board(session_id, certid)

    except wordgemile.GameNotFoundException:
        text = """# Game not found!

This game does not exist, start a new one here:

=> """
        text += f"gemini://{host}{script}/game New Game"
        gemcgi.send_text(text)
        return

    if word == "":
        gemcgi.send_input("Input your word guess")
        return

    else:
        text = "# Wordle Gemini\n\n"
        accept = game_session.input_word(word)
        game_session.save_board(certid)
        text += f"## {len(game_session.board)}/6 tries\n\n"
        text += game_session.print_board()
        if game_session.is_completed:
            if game_session.is_win:
                text += "\n## Correct!\nCongratulations, you guessed the word!"

            else:
                text += "\n## Game over\nYou lose, the "
                text += f"word was {game_session.goal_word}"

            if not accept:
                text += "\n\nThis game is over, won't accept more words."

        else:
            text += f"\n=> gemini://{host}{script}/game/{session_id} Input new word"

        gemcgi.send_text(text)


def new_game(player, serial):
    script = os.environ.get("SCRIPT_NAME")
    host = get_host()
    game_session = wordgemile.Wordle("", player)
    session_id = game_session.create_board(serial)
    text = ""

    if not session_id:
        text += "# New word not available\n\n"
        text += "Every about 16 minutes, you can "
        text += "try to guess a new word."

    else:
        text = "# Wordle Gemini\n\n"
        text += f"## {len(game_session.board)}/6 tries\n\n"
        text += game_session.print_board()
        text += f"=> gemini://{host}{script}/game/{session_id} Input new word"

    gemcgi.send_text(text)


call_path()
