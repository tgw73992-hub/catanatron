"""Regression tests for bounded directed domestic-trade engine support."""

from catanatron.game import Game, is_valid_action
from catanatron.gym.envs.action_space import get_action_array
from catanatron.gym.envs.catanatron_env import CatanatronEnv
from catanatron.models.enums import RESOURCES, Action, ActionPrompt, ActionType
from catanatron.models.player import Color, SimplePlayer
from catanatron.state_functions import player_key

COLORS = (Color.BLUE, Color.RED, Color.WHITE, Color.ORANGE)


def _game():
    game = Game([SimplePlayer(color) for color in COLORS], seed=20260902)
    state = game.state
    proposer = state.current_color()
    state.current_player_index = state.color_to_index[proposer]
    state.current_turn_index = state.color_to_index[proposer]
    state.current_prompt = ActionPrompt.PLAY_TURN
    state.is_initial_build_phase = False
    state.player_state[f"{player_key(state, proposer)}_HAS_ROLLED"] = True
    state.player_state[f"{player_key(state, proposer)}_{RESOURCES[0]}_IN_HAND"] = 1
    return game


def test_directed_offer_is_valid_only_for_an_opponent():
    game = _game()
    proposer = game.state.current_color()
    recipient = next(color for color in game.state.colors if color != proposer)
    trade = (1, 0, 0, 0, 0, 0, 1, 0, 0, 0)

    assert is_valid_action(
        game.playable_actions,
        game.state,
        Action(proposer, ActionType.OFFER_TRADE, (*trade, recipient)),
    )
    assert not is_valid_action(
        game.playable_actions,
        game.state,
        Action(proposer, ActionType.OFFER_TRADE, (*trade, proposer)),
    )


def test_directed_trade_prompts_only_recipient_and_returns_to_proposer():
    game = _game()
    proposer = game.state.current_color()
    recipient = next(color for color in game.state.colors if color != proposer)
    trade = (1, 0, 0, 0, 0, 0, 1, 0, 0, 0)
    game.state.player_state[
        f"{player_key(game.state, recipient)}_{RESOURCES[1]}_IN_HAND"
    ] = 1

    game.execute(Action(proposer, ActionType.OFFER_TRADE, (*trade, recipient)))
    assert game.state.current_color() == recipient
    assert all(action.value is None for action in game.playable_actions)

    game.execute(Action(recipient, ActionType.ACCEPT_TRADE, None))
    assert game.state.current_color() == proposer
    confirm = next(
        action
        for action in game.playable_actions
        if action.action_type == ActionType.CONFIRM_TRADE
    )
    assert confirm.value == recipient
    game.execute(confirm)
    assert game.state.current_color() == proposer
    assert game.state.current_prompt == ActionPrompt.PLAY_TURN


def test_domestic_gym_catalogue_is_opt_in_and_compact():
    baseline = get_action_array(COLORS, "BASE")
    domestic = get_action_array(COLORS, "BASE", domestic_trade=True)

    assert len(domestic) == len(baseline) + 66
    assert not any(action_type == ActionType.OFFER_TRADE for action_type, _ in baseline)
    assert sum(
        action_type == ActionType.OFFER_TRADE for action_type, _ in domestic
    ) == 60


def test_domestic_gym_mask_exposes_only_affordable_offers():
    environment = CatanatronEnv(
        {
            "enemies": [SimplePlayer(color) for color in COLORS[1:]],
            "domestic_trade": True,
        }
    )
    environment.reset(seed=20260902)
    state = environment.game.state
    focal = environment.p0.color
    state.current_player_index = state.color_to_index[focal]
    state.current_turn_index = state.color_to_index[focal]
    state.current_prompt = ActionPrompt.PLAY_TURN
    state.is_initial_build_phase = False
    state.player_state[f"{player_key(state, focal)}_HAS_ROLLED"] = True
    state.player_state[f"{player_key(state, focal)}_{RESOURCES[0]}_IN_HAND"] = 1

    valid = [environment.action_array[index] for index in environment.get_valid_actions()]
    offers = [value for action_type, value in valid if action_type == ActionType.OFFER_TRADE]

    assert len(offers) == 12
    assert all(value[:5] == (1, 0, 0, 0, 0) for value in offers)
