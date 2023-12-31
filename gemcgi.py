"""
Library to respond correctly Gemini protocol over
a CGI connection
"""


def send_text(text, coding="text/gemini;charset=utf-8"):
    print(f"20 {coding}\r\n")
    parsed_text = text.replace("\n", "\r\n")
    print(f"{parsed_text}\r\n")


def send_error(error):
    print(f"40 {error}\r\n")


def send_input(prompt):
    print(f"10 {prompt}\r\n")


def request_auth(prompt):
    print(f"60 {prompt}\r\n")
