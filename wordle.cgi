#!/usr/bin/python3.7

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
            gemcgi.request_auth("Necesitas un certificado para autenticarte")

    elif path == "/about":
        about()

    else:
        notfound()


def notfound():
    gemcgi.send_error("Path not found")


def about():
    gemcgi.send_text("""# Wordle Gemini

Pequeño juego de intentar adivinar la palabra.

## Instrucciones

Las palabras siempre serán de 5 letras. Puede haber palabras repetidas.
A cada turno, se mostrará la palabra introducida con un código de color
para dar pistas.

* Amarillo: La letra está presente, pero en una posición incorrecta.
* Verde: La letra está en la posición correcta.
* Sin color: La letra no está presente en la palabra.

Hay seis intentos para conseguir adivinar la palabla, buena suerte!
    """)


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
        gemcgi.send_input("Introduzca la palabra a buscar")
        return

    else:
        game_session.input_word(word)
        game_session.save_board(certid)
        text = "# Wordle Gemini\n\n"
        text += f"## {len(game_session.board)}/6 intentos\n\n"
        text += game_session.print_board()
        if game_session.is_completed:
            if game_session.is_win:
                text += "\n## Correcto!\nEnhorabuena, ha acertado la palabra!"

            else:
                text += "\n## Game over\nHa perdido, la "
                text += f"palabra era {game_session.goal_word}"

        else:
            text += f"\n=> gemini://{host}{script}/game/{session_id} Introducir otra palabra"

        gemcgi.send_text(text)


def new_game(player, serial):
    script = os.environ.get("SCRIPT_NAME")
    host = get_host()
    game_session = wordgemile.Wordle("", player)
    session_id = game_session.create_board(serial)
    text = ""

    if not session_id:
        text += "# Nueva palabra aún no disponible\n\n"
        text += "Cada 16 minutos aproximadamente, puedes "
        text += "venir a resolver una nueva palabra"

    else:
        text = "# Wordle Gemini\n\n"
        text += f"## {len(game_session.board)}/6 intentos\n\n"
        text += game_session.print_board()
        text += f"=> gemini://{host}{script}/game/{session_id} Introducir una palabra"

    gemcgi.send_text(text)


call_path()
