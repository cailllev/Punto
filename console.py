RESET = "\u001b[0m"


def black(t: str) -> str: return "\u001b[30;1m" + t + RESET
def red(t: str) -> str: return "\u001b[31;1m" + t + RESET
def green(t: str) -> str: return "\u001b[32;1m" + t + RESET
def yellow(t: str) -> str: return "\u001b[33;1m" + t + RESET
def blue(t: str) -> str: return "\u001b[34;1m" + t + RESET
def magenta(t: str) -> str: return "\u001b[35;1m" + t + RESET
def cyan(t: str) -> str: return "\u001b[36;1m" + t + RESET
def white(t: str) -> str: return "\u001b[37;1m" + t + RESET


def clear() -> str: return f"\u001b[2J\u001b[H"  # clear all and move cursor to 0, 0
