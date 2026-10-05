import pytest

from heisenbot.tictactoe import describe_board, winner


def test_winner_uses_semantic_ownership():
    board = ["human", "human", "human", None, "bot", None, "bot", None, None]
    assert winner(board) == "human"


def test_draw_is_detected():
    board = ["human", "bot", "human", "human", "bot", "bot", "bot", "human", "human"]
    assert winner(board) == "draw"


def test_board_description_never_guesses_custom_markers():
    board = ["human", "bot", None, None, None, None, None, None, None]
    description = describe_board(board, "🔥", "🧊")
    assert "cell 1=human player (🔥)" in description
    assert "cell 2=Heisenbot (🧊)" in description
    assert "cell 3=empty" in description


def test_invalid_board_size_is_rejected():
    with pytest.raises(ValueError, match="nine cells"):
        winner([None])
