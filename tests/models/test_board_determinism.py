"""Regression tests for deterministic board move generation."""

from catanatron.models.board import Board
from catanatron.models.player import Color


def test_buildable_edges_are_returned_in_stable_sorted_order():
    """Equivalent components must not inherit set/hash iteration order."""
    board = Board()
    board.connected_components[Color.BLUE] = [{26}]

    edges = board.buildable_edges(Color.BLUE)

    assert edges == sorted(edges)
