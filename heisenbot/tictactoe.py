"""Pure tic-tac-toe rules and model-facing board descriptions."""

from __future__ import annotations

WIN_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


def winner(board: list[str | None]) -> str | None:
    """Return ``human``, ``bot``, ``draw``, or ``None`` for an active game."""
    if len(board) != 9:
        raise ValueError("tic-tac-toe boards must contain exactly nine cells")
    for first, second, third in WIN_LINES:
        if board[first] and board[first] == board[second] == board[third]:
            return board[first]
    return "draw" if all(cell is not None for cell in board) else None


def describe_board(
    board: list[str | None],
    human_marker: str,
    bot_marker: str,
) -> str:
    """Describe every cell with semantic ownership rather than ambiguous markers."""
    if len(board) != 9:
        raise ValueError("tic-tac-toe boards must contain exactly nine cells")
    cells: list[str] = []
    for index, owner in enumerate(board, start=1):
        if owner == "human":
            value = f"human player ({human_marker})"
        elif owner == "bot":
            value = f"Heisenbot ({bot_marker})"
        else:
            value = "empty"
        cells.append(f"cell {index}={value}")
    return "; ".join(cells)
