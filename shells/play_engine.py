import cmd
import chess
from engine.engine_handler import StockfishHandler
from typing import Optional
import random
import time

from utils.helper import print_move_history, render_board

SLEEP = 2

class PlayEngineShell(cmd.Cmd):
    intro = "placeholer" # I'll have to think of something for this or just leave it blank
    prompt = "play_engine> "

    def __init__(self):
        super().__init__()

        self.engine: Optional[StockfishHandler] = None
        self.board : Optional[chess.Board] = None

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

        self.onecmd("clear")
        print(f"Engine plays: {engine_move_san}")
        self.onecmd("board")

    def _end_game(self):

        if self.engine is not None:
            self.engine.stop()
        self.engine = None
        self.board = None

        self.game_active = False
        self.move_history = []

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
        # TODO: This should allow the user to make a move.
        pass

    def do_moves(self, arg):
        """Print move history."""
        print_move_history(self.move_history)

    def do_board(self, arg):
        """Display the board."""
        render_board(self.board, self.user_is_white)

    def do_resign(self, arg):
        # TODO: Allow the user to resign. Ask for confirmation.
        pass

    def do_save(self, arg):
        # TODO: Save the game as a pgn to a file. This can be implemented later.
        pass

    def do_difficulty(self, arg):
        # TODO: Adjust the difficulty of the engine.
        pass

    def do_clear(self, arg):
        """Clear the screen."""
        from utils.helper import clear_screen
        clear_screen()

    def do_exit(self, arg):
        """Exit the shell."""
        return True


if __name__ == "__main__":
    PlayEngineShell().cmdloop()
