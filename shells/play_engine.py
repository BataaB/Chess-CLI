import cmd
from datetime import datetime
import chess
import chess.pgn
from engine.engine_handler import StockfishHandler
from typing import Optional
import random
import time

from utils.helper import ensure_directory, print_move_history, render_board

SLEEP = 2
PGN_PATH = "data/game.pgn"
ENGINE_DEPTH = 12
DEFAULT_ENGINE = "stockfish"
DEFAULT_SKILL_LEVEL = 10

class PlayEngineShell(cmd.Cmd):
    intro = "placeholer" # I'll have to think of something for this or just leave it blank
    prompt = "play_engine> "

    def __init__(self):
        super().__init__()

        self.engine: Optional[StockfishHandler] = None
        self.board : Optional[chess.Board] = None
        self.engine_type: str = DEFAULT_ENGINE

        self.game_result : Optional[str] = None
        self.needs_save : bool = False
        self.user_is_white: bool = False
        self.game_active: bool = False
        self.skill_level: int = DEFAULT_SKILL_LEVEL
        self.move_history: list[str] = []

    def _engine_move(self):
        engine_move = self.engine.get_engine_move(self.board, depth=ENGINE_DEPTH)
        
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
        render_board(self.board, self.user_is_white)


    def _end_game(self):

        if self.needs_save and self.move_history:
            choice = input("Would you like to save the game to a pgn (y/N)? ")
            if choice.lower() == "y":
                self.onecmd("save")

        if self.engine is not None:
            self.engine.stop()
        
        self.engine = None
        self.board = None
        self.game_result = None
        self.needs_save = False
        self.game_active = False
        self.move_history = []

    def _result_message(self, result: str) -> str:
        """PGN Style result to a message."""
        if result == "1-0":
            return "You win!" if self.user_is_white else "You lose."
        elif result == "0-1":
            return "You lose." if self.user_is_white else "You win!"
        else:
            return "Draw."

    def preloop(self):
        self.onecmd("clear")

    def postloop(self):
        if self.game_active:
            self._end_game()
        return super().postloop()

    def do_engine(self, arg):
        choice = arg.strip().lower()
        if choice in ("stockfish", "sf", "s"):
            self.engine_type = "stockfish"
            print("Engine set to Stockfish.")
        elif choice in ("maia", "lc0", "m"):
            self.engine_type = "maia"
            print("Engine set to Maia (Lc0).")
        elif choice == "":
            print("Engine:", self.engine_type)
        else:
            print("Unknown engine. Use 'stockfish' or 'maia'.")

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
            print(f"No side specified. You have been assigned: {'white' if self.user_is_white else 'black'}")
        else:
            print("Invalid side. Choose 'white' or 'black'.")
            return

        if self.engine_type == "stockfish":
            self.engine = StockfishHandler()
            if not self.engine.start(self.skill_level):
                print("Failed to start engine.")
                self.engine = None
                return
        else:
            from engine.engine_handler import Lc0Handler
            self.engine = Lc0Handler()
            if not self.engine.start():
                print("Failed to start Maia (Lc0).")
                self.engine = None
                return

            
        self.board = chess.Board()
        self.move_history = []
        self.game_active = True
        self.game_result = None
        self.needs_save = True

        input("Press Enter to continue..")
        self.onecmd("clear")
        render_board(self.board, self.user_is_white)


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
        render_board(self.board, self.user_is_white)


        if self.board.is_game_over():
            result = self.board.result()
            print("Game over:", result)
            print(self._result_message(result))
            self._end_game()
            return

        self._engine_move()

        if self.board.is_game_over():
            result = self.board.result()
            print("Game over:", result)
            print(self._result_message(result))
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

        self.game_result = "0-1" if self.user_is_white else "1-0"
        self.needs_save = True
        print("You resigned.")
        self._end_game()

    def do_save(self, arg):
        """Save the current game to a pgn. (data/game.pgn)"""
        if not self.game_active and not self.move_history:
            print("No game to save.")
            return

        game = chess.pgn.Game()
        game.headers["Event"] = "Chess CLI Game"
        game.headers["White"] = "User" if self.user_is_white else "Engine"
        game.headers["Black"] = "Engine" if self.user_is_white else "User"
        game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        if self.game_result is not None:
            game.headers["Result"] = self.game_result
            game.headers["Termination"] = "resignation"
        else:
            game.headers["Result"] = self.board.result() if self.board.is_game_over() else "*"

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
