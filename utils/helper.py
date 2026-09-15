import subprocess
import platform
import chess
import os

def clear_screen():
    subprocess.run("cls" if platform.system() == "Windows" else "clear", shell=True)

def print_move_history(move_history):
    n = len(move_history)
    if n == 0:
        print("The move history is empty.")
    for i in range(n):
        if i % 2 == 0:
            print(f"{int(i / 2) + 1}. {move_history[i]}", end="")
        else:
            print(f" {move_history[i]}")
    if n % 2 == 1:
        print()


RESET = "\033[0m"
BOLD = "\033[1m"

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"

SHOW_FILES_AND_RANKS = False
HIGHLIGHT_MOVES = True

PIECE_UNICODES = {
    "k": '\u2654', "q": '\u2655', "r": '\u2656', "b": '\u2657', "n": '\u2658', "p": '\u2659',
    "K": '\u265A', "Q": '\u265B', "R": '\u265C', "B": '\u265D', "N": '\u265E', "P": '\u265F'
}

# ANSI colors
HIGHLIGHT = BLUE
CHECK = RED

def render_board(board, side):
    # return True
    if not side:
        board = board.transform(chess.flip_horizontal).transform(chess.flip_vertical) 

    last_move = board.peek() if board.move_stack else None
    last_from = last_to = check_square = None

    if HIGHLIGHT_MOVES:
        if last_move:
            last_from = last_move.from_square
            last_to = last_move.to_square
        if board.is_check():
            check_square = board.king(board.turn)

    rows = []
    for rank in range(8):
        row = ""
        for file in range(8):
            square = chess.square(file, 7 - rank)
            piece = board.piece_at(square)
            symbol = piece.symbol() if piece else "."
            symbol = PIECE_UNICODES.get(symbol, symbol) + "\uFE0E"

            if HIGHLIGHT_MOVES:
                if square in (last_from, last_to):
                    symbol = f"{HIGHLIGHT}{symbol}{RESET}"
                elif square == check_square:
                    symbol = f"{CHECK}{symbol}{RESET}"

            row += symbol + " "
        rows.append(row.strip())

    if not SHOW_FILES_AND_RANKS:
        print("\n".join(rows))
        return

    print()
    if side:
        ranks = range(8, 0, -1)
        for i, row in enumerate(rows):
            print(f"{ranks[i]} {row}")
        print("  a b c d e f g h")
    else:
        ranks = range(1, 9)
        print("h g f e d c b a")
        for i, row in enumerate(rows):
            print(f"{row} {ranks[i]}")
    print()


def ensure_directory(path: str):
    """Ensure the directory for a file path exists."""
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
