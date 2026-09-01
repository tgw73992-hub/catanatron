"""Tests for isolated, serializable game randomness."""

import random

import pytest

from catanatron.apply_action import roll_dice
from catanatron.game import Game
from catanatron.models.player import Color, RandomPlayer
from catanatron.rng import ENVIRONMENT_EVENT_NAMES, EnvironmentRngs


def _players():
    return [
        RandomPlayer(Color.RED),
        RandomPlayer(Color.BLUE),
        RandomPlayer(Color.WHITE),
        RandomPlayer(Color.ORANGE),
    ]


def test_environment_streams_are_reproducible_and_independent():
    first = EnvironmentRngs.from_seed(42)
    second = EnvironmentRngs.from_seed(42)

    assert first.state_dict() == second.state_dict()
    first.development.random()
    first.robber.random()
    assert roll_dice(Game(_players(), rngs=first).state) == roll_dice(
        Game(_players(), rngs=second).state
    )


def test_game_does_not_consume_or_reseed_process_global_randomness():
    random.seed(123)
    before = random.getstate()
    game = Game(_players(), seed=42)

    game.play_tick()

    assert random.getstate() == before


def test_game_copy_clones_every_environment_stream_without_aliasing():
    game = Game(_players(), seed=42)
    copied = game.copy()

    for name in ENVIRONMENT_EVENT_NAMES:
        original_stream = getattr(game.state.rngs, name)
        copied_stream = getattr(copied.state.rngs, name)
        assert copied_stream is not original_stream
        assert copied_stream.getstate() == original_stream.getstate()


def test_injected_rng_root_is_the_recorded_game_seed():
    rngs = EnvironmentRngs.from_seed(42)

    assert Game(_players(), rngs=rngs).seed == 42
    with pytest.raises(ValueError, match="root seed differ"):
        Game(_players(), seed=7, rngs=rngs)
