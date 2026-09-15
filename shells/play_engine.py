import cmd
import chess
import chess.pgn
from engine.engine_handler import StockfishHandler
from typing import Optional
import random
import time

from utils.helper import ensure_directory, print_move_history, render_board

SLEEP = 2
PGN_PATH = "data/game.pgn"

class PlayEngineShell(cmd.Cmd):
    intro = "placeholer" # I'll have to think of something for this or just leave it blank
    prompt = "play_engine> "

    def __init__(self):
        super().__init__()

        self.engine: Optional[StockfishHandler] = None
        self.board : Optional[chess.Board] = None

        self.needs_save : bool = False
        self.user_is_white: bool = False
        self.game_active: bool = False
        self.skill_level: int = 10
        self.move_history: list[chess.Move] = []

    def _engine_move(self):
        engine_move, _ = self.engine.get_engine_move(self.board, depth=12)
        if engine_move is None:
            print("Engine failed to produce a move.")
            self.game_active = False
            return

        time.sleep(SLEEP)

        engine_move_san = self.board.san(engine_move)
        self.board.push(engine_move)
        self.move_history.append(engine_move_san)
        self.needs_save = True

        self.onecmd("clear")
        print(f"Engine plays: {engine_move_san}")
        self.onecmd("board")

    def _end_game(self):

        if self.needs_save and self.move_history:
            choice = input("Would you like to save the game to a pgn (y/N)? ")
            if choice.lower() == "y":
                self.onecmd("save")

        if self.engine is not None:
            self.engine.stop()
        
        self.engine = None
        self.board = None
        self.needs_save = False
        self.game_active = False
        self.move_history = []

    def _result_message(self, result: str, user_is_white: bool) -> str:
        """PGN Style result to a message."""
        if result == "1-0":
            return "You win!" if user_is_white else "You lose."
        elif result == "0-1":
            return "You lose." if user_is_white else "You win!"
        else:
            return "Draw."

    def preloop(self):
        self.onecmd("clear")

    def postloop(self):
        self._end_game()
        return super().postloop()

    def do_start(self, arg):
        if self.game_active:
            print("There is already an active game.")
            return
        
        side = arg.strip().lower()

        if side in ("white", "w"):
            self.user_is_white = True
        elif side in ("black", "b"):
            self.user_is_white = False
        elif side == "":
            self.user_is_white = bool(random.getrandbits(1))
            print(f"No side specified. You have been assigned: {"white" if self.user_is_white else "black"}")
        else:
            print("Invalid side. Choose 'white' or 'black'.")
            return
        
        self.engine = StockfishHandler()
        if not self.engine.start(self.skill_level):
            print("Failed to start engine.")
            self.engine = None
            return
        
        self.board = chess.Board()
        self.move_history = []
        self.game_active = True

        input("Press Enter to continue..")
        self.onecmd("clear")
        self.onecmd("board")

        if not self.user_is_white:
            self._engine_move()

    def do_move(self, arg):
        """Make a move using SAN notation."""
        if not self.game_active:
            print("No active game. Start a game with: start [white|black]")
            return

        move_san = arg.strip()
        if move_san == "":
            print("Please enter a move.")
            return

        try:
            move = self.board.parse_san(move_san)
        except ValueError:
            print(f"Illegal move: {move_san}")
            return

        san = self.board.san(move)
        self.board.push(move)
        self.move_history.append(san)
        self.needs_save = True

        self.onecmd("clear")
        print(f"You played: {san}")
        self.onecmd("board")

        if self.board.is_game_over():
            result = self.board.result()
            print("Game over:", result)
            print(self._result_message(result, self.user_is_white))
            self._end_game()
            return

        self._engine_move()

        if self.board.is_game_over():
            result = self.board.result()
            print("Game over:", result)
            print(self._result_message(result, self.user_is_white))
            self._end_game()
            return

    def do_moves(self, arg):
        """Print move history."""
        print_move_history(self.move_history)

    def do_board(self, arg):
        """Display the board."""
        render_board(self.board, self.user_is_white)

    def do_resign(self, arg):
        if (arg.strip().lower() != "f"):
            choice = input("Resign (y/N)? ")
            if choice.lower() != "y":
                return

        self._end_game()

    def do_save(self, arg):
        """Save the current game to a pgn. (data/game.pgn)"""
        if not self.game_active and not self.move_history:
            print("No game to save.")
            return

        game = chess.pgn.Game()
        game.headers["Even"] = "Chess CLI Game"
        game.headers["White"] = "User" if self.user_is_white else "Engine"
        game.headers["Black"] = "Engine" if self.user_is_white else "User"

        node = game

        temp_board = chess.Board()
        for san in self.move_history:
            move = temp_board.parse_san(san)
            node = node.add_variation(move)
            temp_board.push(move)

        try:
            ensure_directory(PGN_PATH)
            with open(PGN_PATH, "w", encoding="utf-8") as f:
                print(game, file=f)
            print(f"Game saved to {PGN_PATH}")
            self.needs_save = False
        except Exception as e:
            print(f"Failed to save game: {e}")

    def do_difficulty(self, arg):
        """Set difficulty (1-20) or show difficulty by passing no argument."""
        diff = arg.strip().lower()
        if diff == "":
            print(f"Difficulty: {self.skill_level}")
            return

        try:
            diff = int(diff)
            if (1 > diff or diff > 20):
                print("Difficulty should be an integer from 1 to 20.")
                return
            self.skill_level = diff
            print(f"Difficulty set to: {diff}")
        except ValueError:
            print("Invalid difficulty setting.")
            return

    def do_clear(self, arg):
        """Clear the screen."""
        from utils.helper import clear_screen
        clear_screen()

    def do_exit(self, arg):
        """Exit the shell."""
        return True


if __name__ == "__main__":
    PlayEngineShell().cmdloop()
