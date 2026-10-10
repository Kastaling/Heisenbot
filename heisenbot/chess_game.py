"""Chess rules, board rendering, and a bounded local opponent."""

from __future__ import annotations

import chess
import chess.engine

PIECE_SYMBOLS = {
    "P": "♙",
    "N": "♘",
    "B": "♗",
    "R": "♖",
    "Q": "♕",
    "K": "♔",
    "p": "♟",
    "n": "♞",
    "b": "♝",
    "r": "♜",
    "q": "♛",
    "k": "♚",
}
PIECE_NAMES = {
    chess.PAWN: "Pawn",
    chess.KNIGHT: "Knight",
    chess.BISHOP: "Bishop",
    chess.ROOK: "Rook",
    chess.QUEEN: "Queen",
    chess.KING: "King",
}
PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}


def render_board(board: chess.Board, human_color: chess.Color) -> str:
    """Show the board from the human player's side."""
    ranks = range(7, -1, -1) if human_color == chess.WHITE else range(8)
    files = range(8) if human_color == chess.WHITE else range(7, -1, -1)
    lines = []
    for rank in ranks:
        cells = []
        for file in files:
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            cells.append(PIECE_SYMBOLS[piece.symbol()] if piece else "·")
        lines.append(f"{rank + 1}  {' '.join(cells)}")
    labels = " ".join(chess.FILE_NAMES[file] for file in files)
    return "```\n" + "\n".join(lines) + f"\n   {labels}\n```"


def legal_origins(board: chess.Board) -> list[chess.Square]:
    return sorted({move.from_square for move in board.legal_moves}, key=chess.square_name)


def legal_destinations(board: chess.Board, origin: chess.Square) -> list[chess.Move]:
    return sorted(
        (move for move in board.legal_moves if move.from_square == origin),
        key=lambda move: (chess.square_name(move.to_square), move.promotion or 0),
    )


def notable_move(board: chess.Board, move: chess.Move, actor: str) -> str | None:
    """Describe a major capture or promotion before the move is pushed."""
    events = []
    captured = board.piece_at(move.to_square)
    if captured and captured.piece_type in {chess.QUEEN, chess.ROOK}:
        events.append(f"{actor} captured a {PIECE_NAMES[captured.piece_type].lower()}")
    if move.promotion:
        events.append(f"{actor} promoted a pawn to a {PIECE_NAMES[move.promotion].lower()}")
    return "; ".join(events) or None


def fallback_move(board: chess.Board) -> chess.Move | None:
    """Select a legal tactical move if the installed engine is unavailable."""
    moves = list(board.legal_moves)
    if not moves:
        return None

    def score(move: chess.Move) -> tuple[float, str]:
        captured = board.piece_at(move.to_square)
        if captured is None and board.is_en_passant(move):
            capture_value = PIECE_VALUES[chess.PAWN]
        else:
            capture_value = PIECE_VALUES[captured.piece_type] if captured else 0
        moving = board.piece_at(move.from_square)
        moving_value = PIECE_VALUES[moving.piece_type] if moving else 0
        value = capture_value * 10 - moving_value if capture_value else 0
        value += PIECE_VALUES.get(move.promotion, 0) * 2
        if board.gives_check(move):
            value += 2
        board.push(move)
        if board.is_checkmate():
            value += 1000
        board.pop()
        # Stable tie break makes failures easy to reproduce.
        return (value, move.uci())

    return max(moves, key=score)


def choose_bot_move(
    board: chess.Board,
    *,
    skill_level: int = 3,
    think_seconds: float = 0.15,
    engine_path: str = "/usr/games/stockfish",
) -> chess.Move | None:
    """Use Stockfish with a strict time limit; return a legal fallback on failure."""
    if board.outcome(claim_draw=True) is not None:
        return None
    try:
        with chess.engine.SimpleEngine.popen_uci(engine_path, timeout=5.0) as engine:
            if "Skill Level" in engine.options:
                engine.configure({"Skill Level": skill_level})
            result = engine.play(board, chess.engine.Limit(time=think_seconds))
        if result.move in board.legal_moves:
            return result.move
    except (OSError, chess.engine.EngineError, TimeoutError):
        pass
    return fallback_move(board)


def outcome_text(board: chess.Board, human_color: chess.Color) -> str | None:
    outcome = board.outcome(claim_draw=True)
    if outcome is None:
        return None
    if outcome.winner == human_color:
        return "**You win by checkmate!**"
    if outcome.winner == (not human_color):
        return "**Heisenbot wins by checkmate!**"
    reasons = {
        chess.Termination.STALEMATE: "stalemate",
        chess.Termination.INSUFFICIENT_MATERIAL: "insufficient material",
        chess.Termination.FIVEFOLD_REPETITION: "fivefold repetition",
        chess.Termination.THREEFOLD_REPETITION: "threefold repetition",
        chess.Termination.SEVENTYFIVE_MOVES: "75-move rule",
        chess.Termination.FIFTY_MOVES: "50-move rule",
    }
    reason = reasons.get(outcome.termination, "draw")
    return f"**Draw by {reason}.**"
