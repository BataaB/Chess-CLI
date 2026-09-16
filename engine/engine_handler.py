import subprocess

import chess
import chess.engine
from typing import Optional


class StockfishHandler:
    def __init__(self, engine_path: Optional[str] = "engine/stockfish/stockfish.exe"):
        self.engine_path = engine_path
        self.engine : Optional[chess.engine.SimpleEngine] = None

    def start(self, skill_level: Optional[int] = None) -> bool:
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)

            if skill_level is not None:
                self.engine.configure({"Skill Level": skill_level})

            return True
        except FileNotFoundError:
            return False

    def get_engine_move(
            self,
            board: chess.Board,
            depth: Optional[int] = None,
            multipv: int = 1,
            limit_time: Optional[float] = None
        ) -> Optional[chess.Move]:

        if not self.engine:
            raise RuntimeError("Engine process has not been started.")

        if depth is not None:
            limit = chess.engine.Limit(depth=depth)
        elif limit_time is not None:
            limit = chess.engine.Limit(time=limit_time)
        else:
            raise ValueError("Either depth or limit_time must be provided.")

        info = self.engine.analyse(board, limit, multipv=multipv)

        pv_lines = []
        for entry in info:
            pv = entry.get("pv", [])
            pv_lines.append(pv)

        best_move = pv_lines[0][0] if pv_lines and pv_lines[0] else None

        return best_move, pv_lines


    def get_evaluation(
            self,
            board: chess.Board,
            depth: Optional[int] = None,
            limit_time: Optional[float] = None
        ) -> chess.engine.PovScore:

        if not self.engine:
            raise RuntimeError("Engine process has not been started.")

        if depth is not None:
            limit = chess.engine.Limit(depth=depth)
        elif limit_time is not None:
            limit = chess.engine.Limit(time=limit_time)
        else:
            raise ValueError("Either depth or limit_time must be provided.")

        info = self.engine.analyse(board, limit)
        return info["score"]

    def stop(self):
        """Terminate the engine."""
        if self.engine:
            self.engine.quit()
            self.engine = None
            print("Engine terminated.")

class Lc0Handler():
    def __init__(self,
                 engine_path: str = "engine/maia/lc0.exe",
                 weights_path: str = "engine/maia/weights/maia-1100.pb"):
        self.engine_path = engine_path
        self.weights_path = weights_path
        self.process: Optional[chess.engine.SimpleEngine] = None

    def start(self) -> bool:
        try:
            self.process = chess.engine.SimpleEngine.popen_uci(self.engine_path, stderr=subprocess.DEVNULL)
            self.process.configure({"WeightsFile": self.weights_path})
            return True
        except Exception as e:
            print(f"Failed to start Lc0: {e}")
            self.process = None
            return False

    def stop(self) -> None:
        if self.process is not None:
            try:
                self.process.quit()
            except Exception:
                pass
            self.process = None

    def get_engine_move(self, board: chess.Board, depth: int = 1) -> tuple[Optional[chess.Move], Optional[float]]:
        if self.process is None:
            return None, None

        try:
            limit = chess.engine.Limit(nodes=1)
            info = self.process.play(board, limit)
            return info.move, None
        except Exception as e:
            print(f"Lc0 failed to produce a move: {e}")
            return None, None