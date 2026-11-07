"""Regressions for observations that omit an opponent's terminal response."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import agent
from evaluator import cards_from_str
from game import Action, AgentConfig, Game, Street, make_deal


@pytest.mark.parametrize("reraise", [False, True])
def test_terminal_fold_is_attributed_to_our_raise(reraise):
    memory = {}
    agent.new_half(AgentConfig(), memory)
    game = Game(make_deal("model-regression", 0), 0)
    strong = tuple(cards_from_str("Ac Ad Kc Kd Qh"))
    action = agent.choose_action(replace(game.observation(0), hole_cards=strong), memory)
    assert action == Action.RAISE_POT
    game.apply(action)
    if reraise:
        game.apply(Action.RAISE_POT)
        action = agent.choose_action(replace(game.observation(0), hole_cards=strong), memory)
        assert action == Action.RAISE_POT
        game.apply(action)
    game.apply(Action.FOLD)
    agent.on_hand_end(game.hand_result(0), memory)
    assert memory["faced_raises"] == 1 + reraise
    assert memory["folded_to_raise"] == 1
    assert memory["faced_reraises"] == int(reraise)
    assert memory["folded_to_reraise"] == int(reraise)
    assert memory["street_stats"][Street.PREFLOP][2:] == [1 + reraise, 1]
    assert not memory["histories"]


def test_exhausted_internal_budget_stops_simulation():
    memory = {}
    agent.new_half(AgentConfig(), memory)
    memory["used"] = memory["bank"]
    game = Game(make_deal("no-simulation", 0), 0)
    game.apply(Action.CHECK_CALL)
    game.apply(Action.CHECK_CALL)
    obs = game.observation(game.to_act)
    assert obs.street == Street.FLOP
    with patch.object(agent, "omaha_score") as score:
        action = agent.choose_action(obs, memory)
    score.assert_not_called()
    assert action in obs.legal_actions


def test_callback_exceptions_use_check_call_fallback():
    class BrokenMemory(dict):
        def setdefault(self, *args):
            raise RuntimeError("injected")

    obs = Game(make_deal("fallback", 0), 0).observation(0)
    assert agent.choose_action(obs, BrokenMemory()) == Action.CHECK_CALL
    assert agent.new_half(None, {}) == Action.CHECK_CALL
    assert agent.on_hand_end(None, {}) == Action.CHECK_CALL


def test_governor_scales_samples_and_deadline_with_used_time():
    memory = {}
    agent.new_half(AgentConfig(), memory)
    obs = replace(Game(make_deal("governor", 0), 0).observation(0), hand_index=900)
    allowances = []
    limits = []
    for step in range(int((memory["bank"] + 0.1) * 100)):
        memory["used"] = step / 100
        budget, samples = agent._simulation_budget(obs, memory)
        assert samples in (0, 8, 24, 40)
        assert 0 <= budget <= 0.002
        allowances.append(budget)
        limits.append(samples)
    assert allowances == sorted(allowances, reverse=True)
    assert limits == sorted(limits, reverse=True)
    assert set(limits) == {0, 8, 24, 40}
    memory["bank"] = 0.3
    memory["used"] = 0.0
    assert agent._simulation_budget(obs, memory) == (0.0, 0)


def test_stopped_simulations_reuse_same_board_estimate():
    memory = {}
    agent.new_half(AgentConfig(), memory)
    game = Game(make_deal("cached-equity", 0), 0)
    game.apply(Action.CHECK_CALL)
    game.apply(Action.CHECK_CALL)
    obs = game.observation(game.to_act)
    key = tuple(obs.board)
    memory["histories"][obs.hand_index] = {"equities": {key: 0.77}}
    memory["used"] = memory["bank"]
    with patch.object(agent, "omaha_score") as score, patch.object(agent, "_static_equity") as static:
        action = agent.choose_action(obs, memory)
    score.assert_not_called()
    static.assert_not_called()
    assert memory["histories"][obs.hand_index]["equities"][key] == 0.77
    assert action in obs.legal_actions


def test_stopped_governor_skips_optional_showdown_sampling():
    memory = {}
    agent.new_half(AgentConfig(), memory)
    game = Game(make_deal("no-showdown-samples", 0), 0)
    memory["used"] = memory["bank"]
    while not game.is_terminal:
        if game.to_act == 0:
            agent.choose_action(game.observation(0), memory)
            memory["histories"][game.hand_index]["last_action"] = Action.CHECK_CALL
        game.apply(Action.CHECK_CALL)
    with patch.object(agent, "omaha_score") as score:
        agent.on_hand_end(game.hand_result(0), memory)
    score.assert_not_called()
    assert memory["hands_played"] == 1
    assert not memory["histories"]
