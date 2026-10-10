import chess

from heisenbot.chess_game import (
    choose_bot_move,
    fallback_move,
    legal_destinations,
    legal_origins,
    outcome_text,
    render_board,
)


def test_initial_selection_and_board_orientation():
    board = chess.Board()
    assert len(legal_origins(board)) == 10
    assert {move.uci() for move in legal_destinations(board, chess.E2)} == {"e2e3", "e2e4"}
    assert render_board(board, chess.WHITE).splitlines()[1].startswith("8  ♜")
    assert render_board(board, chess.BLACK).splitlines()[1].startswith("1  ♖")


def test_promotion_offers_all_four_choices():
    board = chess.Board("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
    assert {move.uci() for move in legal_destinations(board, chess.A7)} == {
        "a7a8q",
        "a7a8r",
        "a7a8b",
        "a7a8n",
    }


def test_full_rules_include_castling_and_en_passant():
    castle = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    assert {move.uci() for move in legal_destinations(castle, chess.E1)} >= {
        "e1g1",
        "e1c1",
    }
    en_passant = chess.Board("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1")
    assert chess.Move.from_uci("e5d6") in legal_destinations(en_passant, chess.E5)


def test_checkmate_and_draw_outcomes():
    mate = chess.Board()
    for san in ("f3", "e5", "g4", "Qh4#"):
        mate.push_san(san)
    assert outcome_text(mate, chess.WHITE) == "**Heisenbot wins by checkmate!**"
    stalemate = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    assert outcome_text(stalemate, chess.WHITE) == "**Draw by stalemate.**"


def test_engine_failure_keeps_move_legal_and_does_not_mutate_board():
    board = chess.Board()
    initial_fen = board.fen()
    move = choose_bot_move(board, engine_path="/definitely/missing/stockfish")
    assert move in board.legal_moves
    assert fallback_move(board) in board.legal_moves
    assert board.fen() == initial_fen
