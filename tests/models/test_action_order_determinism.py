"""Regression tests for process-independent playable-action ordering."""

import os
import subprocess
import sys
from pathlib import Path

CATANATRON_ROOT = Path(__file__).resolve().parents[2]


def _trajectory(hash_seed):
    script = """
import random

from catanatron.game import Game
from catanatron.models.player import Color, SimplePlayer

colors = (Color.BLUE, Color.RED, Color.WHITE, Color.ORANGE)
game = Game([SimplePlayer(color) for color in colors], seed=20260901)
selection_rng = random.Random(20260901)
trajectory = []
for _ in range(250):
    if game.winning_color() is not None:
        break
    action = selection_rng.choice(game.playable_actions)
    trajectory.append(repr(action))
    trajectory.append(repr(game.execute(action)))
print("\\n".join(trajectory))
"""
    environment = os.environ.copy()
    environment["PYTHONHASHSEED"] = str(hash_seed)
    environment["PYTHONPATH"] = os.pathsep.join(
        (str(CATANATRON_ROOT / "catanatron"), environment.get("PYTHONPATH", ""))
    )
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=CATANATRON_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def test_seeded_random_trajectory_is_independent_of_python_hash_seed():
    """A random index must identify the same action in every process."""
    trajectories = [_trajectory(seed) for seed in (0, 1, 7, 12345)]

    assert trajectories[1:] == trajectories[:-1]
