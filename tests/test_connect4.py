import pytest

from heisenbot.connect4 import (
    choose_bot_move,
    describe_board,
    drop_piece,
    new_board,
    valid_columns,
    winner,
)


def test_drop_piece_applies_gravity_and_reports_row():
    board = new_board()
    assert drop_piece(board, 3, "human") == 5
    assert drop_piece(board, 3, "bot") == 4
    assert board[5][3] == "human"
    assert board[4][3] == "bot"


@pytest.mark.parametrize(
    "moves",
    [
        [(0, "human"), (1, "human"), (2, "human"), (3, "human")],
        [(2, "bot"), (2, "bot"), (2, "bot"), (2, "bot")],
        [
            (0, "bot"),
            (1, "human"),
            (1, "bot"),
            (2, "human"),
            (2, "human"),
            (2, "bot"),
            (3, "human"),
            (3, "human"),
            (3, "human"),
            (3, "bot"),
        ],
    ],
)
def test_winner_detects_horizontal_vertical_and_diagonal(moves):
    board = new_board()
    for column, player in moves:
        drop_piece(board, column, player)
    assert winner(board) == moves[-1][1]


def test_full_column_is_not_valid_and_rejects_another_piece():
    board = new_board()
    for index in range(6):
        drop_piece(board, 0, "human" if index % 2 == 0 else "bot")
    assert 0 not in valid_columns(board)
    with pytest.raises(ValueError, match="full"):
        drop_piece(board, 0, "human")


def test_ai_takes_a_win_and_blocks_an_immediate_loss_without_mutating_board():
    winning_board = new_board()
    blocking_board = new_board()
    for column in range(3):
        drop_piece(winning_board, column, "bot")
        drop_piece(blocking_board, column, "human")

    winning_snapshot = [row.copy() for row in winning_board]
    blocking_snapshot = [row.copy() for row in blocking_board]
    assert choose_bot_move(winning_board) == 3
    assert choose_bot_move(blocking_board) == 3
    assert winning_board == winning_snapshot
    assert blocking_board == blocking_snapshot


def test_empty_board_prefers_the_center_column():
    assert choose_bot_move(new_board()) == 3


def test_full_board_without_four_in_a_row_is_a_draw():
    rows = (
        "BBHBHHH",
        "HHBBHHH",
        "HHBHBBH",
        "HHBHBHB",
        "BBHBHBB",
        "HHHBHHB",
    )
    board = [["human" if cell == "H" else "bot" for cell in row] for row in rows]
    assert winner(board) == "draw"
    assert choose_bot_move(board) is None


def test_invalid_floating_board_is_rejected():
    board = new_board()
    board[0][0] = "human"
    with pytest.raises(ValueError, match="float"):
        winner(board)


def test_board_description_is_semantic_and_compact():
    board = new_board()
    drop_piece(board, 0, "human")
    drop_piece(board, 1, "bot")
    description = describe_board(board)
    assert description.endswith("H=human, B=Heisenbot")
    assert "HB....." in description
