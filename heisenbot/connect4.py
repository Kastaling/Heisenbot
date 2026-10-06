"""Pure Connect Four rules and a bounded local computer player."""

from __future__ import annotations

ROWS = 6
COLUMNS = 7
CONNECT = 4
PLAYERS = frozenset({"human", "bot"})
_COLUMN_ORDER = (3, 2, 4, 1, 5, 0, 6)

Board = list[list[str | None]]


def new_board() -> Board:
    """Return an empty standard 6-by-7 Connect Four board."""
    return [[None for _ in range(COLUMNS)] for _ in range(ROWS)]


def _validate_board(board: Board) -> None:
    if len(board) != ROWS or any(len(row) != COLUMNS for row in board):
        raise ValueError("Connect Four boards must be 6 rows by 7 columns")
    if any(cell not in PLAYERS | {None} for row in board for cell in row):
        raise ValueError("Connect Four cells must be human, bot, or empty")

    for column in range(COLUMNS):
        found_empty = False
        for row in range(ROWS - 1, -1, -1):
            if board[row][column] is None:
                found_empty = True
            elif found_empty:
                raise ValueError("Connect Four pieces cannot float above empty cells")


def valid_columns(board: Board) -> tuple[int, ...]:
    """Return zero-based columns that can accept another piece."""
    _validate_board(board)
    return tuple(column for column in range(COLUMNS) if board[0][column] is None)


def _drop_unchecked(board: Board, column: int, player: str) -> int:
    for row in range(ROWS - 1, -1, -1):
        if board[row][column] is None:
            board[row][column] = player
            return row
    raise ValueError("that column is full")


def drop_piece(board: Board, column: int, player: str) -> int:
    """Drop a piece using gravity and return the zero-based row it occupies."""
    _validate_board(board)
    if isinstance(column, bool) or not isinstance(column, int) or not 0 <= column < COLUMNS:
        raise ValueError("column must be an integer from 0 through 6")
    if player not in PLAYERS:
        raise ValueError("player must be human or bot")
    return _drop_unchecked(board, column, player)


def _windows(board: Board):
    for row in range(ROWS):
        for column in range(COLUMNS - CONNECT + 1):
            yield [board[row][column + offset] for offset in range(CONNECT)]
    for row in range(ROWS - CONNECT + 1):
        for column in range(COLUMNS):
            yield [board[row + offset][column] for offset in range(CONNECT)]
    for row in range(ROWS - CONNECT + 1):
        for column in range(COLUMNS - CONNECT + 1):
            yield [board[row + offset][column + offset] for offset in range(CONNECT)]
            yield [board[row + CONNECT - 1 - offset][column + offset] for offset in range(CONNECT)]


def _winner_unchecked(board: Board) -> str | None:
    for window in _windows(board):
        if window[0] is not None and all(cell == window[0] for cell in window[1:]):
            return window[0]
    return "draw" if all(cell is not None for row in board for cell in row) else None


def winner(board: Board) -> str | None:
    """Return ``human``, ``bot``, ``draw``, or ``None`` for an active game."""
    _validate_board(board)
    return _winner_unchecked(board)


def describe_board(board: Board) -> str:
    """Return a compact, unambiguous description suitable for an LLM prompt."""
    _validate_board(board)
    symbols = {None: ".", "human": "H", "bot": "B"}
    rows = ["".join(symbols[cell] for cell in row) for row in board]
    return "columns 1-7; rows top-to-bottom: " + "/".join(rows) + "; H=human, B=Heisenbot"


def _score_window(window: list[str | None]) -> int:
    bot_count = window.count("bot")
    human_count = window.count("human")
    empty_count = window.count(None)
    if bot_count == CONNECT:
        return 100_000
    if human_count == CONNECT:
        return -100_000
    if bot_count == 3 and empty_count == 1:
        return 120
    if human_count == 3 and empty_count == 1:
        return -150
    if bot_count == 2 and empty_count == 2:
        return 12
    if human_count == 2 and empty_count == 2:
        return -15
    return 0


def _score_position(board: Board) -> int:
    center = [board[row][COLUMNS // 2] for row in range(ROWS)]
    score = 6 * (center.count("bot") - center.count("human"))
    return score + sum(_score_window(window) for window in _windows(board))


def _ordered_valid_columns(board: Board) -> list[int]:
    return [column for column in _COLUMN_ORDER if board[0][column] is None]


def _minimax(board: Board, depth: int, maximizing: bool, alpha: int, beta: int) -> int:
    result = _winner_unchecked(board)
    if result == "bot":
        return 1_000_000 + depth
    if result == "human":
        return -1_000_000 - depth
    if result == "draw":
        return 0
    if depth == 0:
        return _score_position(board)

    columns = _ordered_valid_columns(board)
    if maximizing:
        value = -(10**9)
        for column in columns:
            row = _drop_unchecked(board, column, "bot")
            value = max(value, _minimax(board, depth - 1, False, alpha, beta))
            board[row][column] = None
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value

    value = 10**9
    for column in columns:
        row = _drop_unchecked(board, column, "human")
        value = min(value, _minimax(board, depth - 1, True, alpha, beta))
        board[row][column] = None
        beta = min(beta, value)
        if alpha >= beta:
            break
    return value


def choose_bot_move(board: Board, depth: int = 5) -> int | None:
    """Choose a legal move using tactical checks plus bounded alpha-beta search.

    The input board is validated and is never mutated.
    """
    _validate_board(board)
    if isinstance(depth, bool) or not isinstance(depth, int) or not 1 <= depth <= 7:
        raise ValueError("search depth must be an integer from 1 through 7")
    if _winner_unchecked(board) is not None:
        return None

    working = [row.copy() for row in board]
    columns = _ordered_valid_columns(working)

    for player in ("bot", "human"):
        for column in columns:
            row = _drop_unchecked(working, column, player)
            result = _winner_unchecked(working)
            working[row][column] = None
            if result == player:
                return column

    best_column = columns[0]
    best_score = -(10**9)
    for column in columns:
        row = _drop_unchecked(working, column, "bot")
        score = _minimax(working, depth - 1, False, -(10**9), 10**9)
        working[row][column] = None
        if score > best_score:
            best_score = score
            best_column = column
    return best_column
