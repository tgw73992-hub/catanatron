"""Serializable, event-specific random streams for Catan game mechanics."""

from __future__ import annotations

import hashlib
import random
import secrets
from dataclasses import dataclass
from typing import Any


ENVIRONMENT_RNG_SCHEMA_VERSION = "catanatron.environment-rng.v1"
ENVIRONMENT_EVENT_NAMES = ("setup", "dice", "development", "robber")


def derive_seed(root_seed: int, name: str) -> int:
    """Derive a stable 256-bit child seed without consuming another stream."""
    material = f"{ENVIRONMENT_RNG_SCHEMA_VERSION}:{root_seed}:{name}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest(), "big")


@dataclass
class EnvironmentRngs:
    """Independent random streams for setup, dice, development, and robber events."""

    root_seed: int
    setup: random.Random
    dice: random.Random
    development: random.Random
    robber: random.Random
    schema_version: str = ENVIRONMENT_RNG_SCHEMA_VERSION

    @classmethod
    def from_seed(cls, root_seed: int | None = None) -> "EnvironmentRngs":
        seed = secrets.randbits(63) if root_seed is None else int(root_seed)
        streams = {
            name: random.Random(derive_seed(seed, name))
            for name in ENVIRONMENT_EVENT_NAMES
        }
        return cls(root_seed=seed, **streams)

    def copy(self) -> "EnvironmentRngs":
        copied = EnvironmentRngs.from_seed(self.root_seed)
        copied.load_state_dict(self.state_dict())
        return copied

    def state_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "root_seed": self.root_seed,
            "streams": {
                name: getattr(self, name).getstate()
                for name in ENVIRONMENT_EVENT_NAMES
            },
        }

    def load_state_dict(self, state: dict[str, Any]) -> None:
        if state.get("schema_version") != ENVIRONMENT_RNG_SCHEMA_VERSION:
            raise ValueError(
                "Unsupported environment RNG schema: "
                f"{state.get('schema_version')}"
            )
        if int(state["root_seed"]) != self.root_seed:
            raise ValueError("Environment RNG root seed does not match")
        for name in ENVIRONMENT_EVENT_NAMES:
            getattr(self, name).setstate(state["streams"][name])
