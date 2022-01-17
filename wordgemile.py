import sys
import sqlite3
import uuid
from time import time

C_YELLOW = r"[38;5;220m"
C_GREEN = r"[38;5;34m"
C_RESET = r"[0m"

DATABASE = "wordle.sqlite"
ROTATION_TIME = 960


class Wordle:
    """
    This class holds a game session, with the name
    the words put in and the results
    """
    def __init__(self, goal_word, player_name):
        self.player = player_name
        self.goal_word = goal_word
        self.sess_id = None
        self.cert_id = None
        # The board is a list of tuples with the
        # word the player has guessed that turn  and
        # the markings we have calculated as hints
        self.board = []

    def load_board(self, sess_id, cert_id):
        self.sess_id = sess_id
        self.cert_id = cert_id
        con = sqlite3.connect(DATABASE)
        cursor = con.cursor()

        cursor.execute("SELECT name, words, goal_word from sessions")
        res = cursor.fetchone()
        self.player = res[0]  # Load the player's name
        self.goal_word = res[2]    # Load the goal word
        words = res[1]        # Load the tried words

        con.close()
        self._generate_board(words.split(","))

    def _generate_session_id(self):
        sess_id = str(uuid.uuid4())
        sess_id = sess_id.replace("-", "")
        return sess_id

    def save_board(self, cert_id):
        if not self.sess_id:
            self.sess_id = self._generate_session_id()

        self.cert_id = cert_id

        words = ",".join([word[0] for word in self.board])

        con = sqlite3.connect(DATABASE)
        cursor = con.cursor()
        cursor.execute("INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?)",
                       (self.sess_id, self.cert_id, self.name,
                        words, self.goal_word, int(time())))
        con.commit()
        con.close()

    def _generate_board(self, words):
        """
        Given a list of words, generates the board
        """
        for word in words:
            markings = self._generate_markings(word)
            self.board.append((word, markings))

    def _generate_markings(self, word):
        markings = []
        parsed_letters = []
        for letter_pair in zip(word, self.goal_word):
            if letter_pair[0] not in self.goal_word or \
                    letter_pair[0] in parsed_letters:
                markings.append(None)

            elif letter_pair[0] == letter_pair[1]:
                markings.append("G")

            else:
                markings.append("Y")

            parsed_letters.append(letter_pair[0])

        return markings

    def input_word(self, word):
        if check_word(word, check_repeats=False):
            markings = self._generate_markings(word)
            self.board.append((word, markings))

            return True

        return False

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

    @property
    def is_completed(self):
        """
        If the word has been discovered, return True
        """
        if len(self.board) > 0:
            last_game = self.board[-1]
            marks = "".join([elem for elem in last_game[1] if elem])
            return marks == "GGGGG"

        return False


def check_word(word, check_repeats=True):
    """
    Makes sure the word is compliant with the game's word restrictions.

    - 5 letters long.
    - No letter repeats.
    """
    if len(word) != 5:
        return False

    correct = True
    if check_repeats:
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

    if res and res[0]:
        current_word = res[0]

    while new_word == current_word:
        cursor.execute("SELECT word FROM words ORDER BY RANDOM() LIMIT 1")
        res = cursor.fetchone()

        new_word = res[0]

    cursor.execute("DELETE FROM current_word")
    con.commit()

    ts = int(time())
    cursor.execute("INSERT INTO current_word VALUES (?, ?)", (new_word, ts))
    con.commit()
    con.close()


def get_current_word():
    """
    Fetches the current word, if it's old, generates a new one
    """
    con = sqlite3.connect(DATABASE)
    cursor = con.cursor()

    cursor.execute("SELECT word, timestamp FROM current_word")
    res = cursor.fetchone()

    if res and res[0]:
        word = res[0]
        timestamp = res[1]

    else:
        timestamp = 0

    if (int(time()) - timestamp) > ROTATION_TIME:
        con.close()
        choose_random_word()
        return get_current_word()

    return word


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
                   (id text, certid text, name text, words text,
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

    word = get_current_word()
    game_session = Wordle(word, "Reset")
    game_session.print_board()

    while not game_session.is_completed:
        new_word = input("Enter word: ")
        if game_session.input_word(new_word):
            game_session.print_board()

        else:
            print("Not a valid word, try again.")
