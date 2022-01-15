import sys
import sqlite3
from time import time

C_YELLOW = r"[38;5;220m"
C_GREEN = r"[38;5;34m"
C_RESET = r"[0m"

DATABASE = "wordle.sqlite"


class Wordle:
    """
    This class holds a game session, with the name
    the words put in and the results
    """
    def __init__(self, word, player_name):
        self.player = player_name
        self.word = word
        # The board is a list of tuples with the
        # word the player has guessed that turn  and
        # the markings we have calculated as hints
        self.board = []

    def print_board(self):
        print("```")
        for word, markings in self.board:
            self.output_word(word, markings)
            print("")

        print("\n```\n")

    def output_word(self, word, markings):
        """
        Outputs the word with the correct colors
        """
        for letter, mark in zip(word, markings):
            if mark == "Y":
                print(C_YELLOW, end="")

            elif mark == "G":
                print(C_GREEN, end="")

            print(letter, end="")
            print(C_RESET, end="")


def check_word(word):
    """
    Makes sure the word is compliant with the game's word restrictions.

    - 5 letters long.
    - No letter repeats.
    """
    if len(word) != 5:
        return False

    correct = True
    for letter in word:
        correct = correct and (word.count(letter) == 1)

    return correct


def choose_random_word():
    """
    Chooses a new word from the list available
    """
    con = sqlite3.connect(DATABASE)
    cursor = con.cursor()

    current_word = ""
    new_word = ""

    cursor.execute("SELECT word FROM current_word")
    res = cursor.fetchone()

    if res:
        current_word = res[0]

    while new_word == current_word:
        cursor.execute("SELECT word FROM words ORDER BY RANDOM() LIMIT 1")
        res = cursor.fetchone()

        new_word = res[0]

    ts = int(time())
    cursor.execute("INSERT INTO current_word VALUES (?, ?)", (new_word, ts))
    con.commit()
    con.close()


def create_database(word_file):
    """
    Loads a word file and creates the database
    """
    con = sqlite3.connect(DATABASE)
    cursor = con.cursor()

    # This is the table holding all possible words
    cursor.execute("CREATE TABLE IF NOT EXISTS words (word text)")
    # This table holds all the sessions
    cursor.execute("""CREATE TABLE IF NOT EXISTS sessions
                   (id text, name text, words text,
                   goal_word text, timestamp integer)""")
    # Create this table so everyone gets the same word and we know how long its
    # been on
    cursor.execute("""CREATE TABLE IF NOT EXISTS current_word
                   (word text, timestamp integer)""")
    con.commit()

    # Make sure we clean the words table, we're loading the words!
    cursor.execute("DELETE FROM words")
    con.commit()

    count = 0
    inserted = 0
    rejected = 0
    with open(word_file, 'r') as f:
        for word in f:
            w = word.replace("\n", "")
            count += 1
            if check_word(w):
                inserted += 1
                cursor.execute("INSERT INTO words VALUES (?)", (w,))

            else:
                rejected += 1

            if count % 100 == 0:
                con.commit()
                print(f"Parsed {count} words.")
                print(f"Inserted {inserted} words into database.")
                print(f"Rejected {rejected} words.")

    con.commit()
    con.close()
    # With the database all created and ready, set a random word
    choose_random_word()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--load":
        if len(sys.argv) == 3:
            create_database(sys.argv[2])

        else:
            print("Usage: --load <word_text_filename>")
            sys.exit(1)

    word = "costa"
    markings = ["Y", "G", None, None, "Y", "G"]
    game_session = Wordle(word, "Reset")
    game_session.board = [
        ("pesto", [None, None, "G", "G", "Y"]),
        ("onsta", ["Y", None, "G", "G", "G"]),
        ("costa", ["G", "G", "G", "G", "G"]),
    ]
    game_session.print_board()
