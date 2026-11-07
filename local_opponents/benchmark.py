"""
agent.py - YOUR poker bot. This one file is a complete web server.

Run it:
    python agent.py                  # listens on port 5008
    PORT=5010 python agent.py        # or pick a port

Play a match against a baseline (three windows):
    python agent.py                                 # your bot on port 5008
    python baseline-bots/baseline_random.py         # opponent on port 5009
    python judge_engine.py                          # judge: both halves (uses those two ports)

Check that the tournament can run it:
    python -m pytest -q              # tests in test_agent.py
    ./tools/check_build.sh           # builds and smoke-tests it like the tournament

TODO:
    1. Assign your agent a unique PARTICIPANT and AGENT_NAME below.
    2. Implement the three functions between "YOUR CODE HERE" and "END OF YOUR CODE".

Everything under "SERVER PLUMBING" talks to the judge. You normally never
need to change it, and if you break it the judge can't talk to your bot.
"""

import os
import traceback

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from evaluator import card_rank, card_suit, cards_to_str, omaha_score, warmup  # handy helpers, see evaluator.py
from game import Action, AgentConfig, HandResult, Observation, Street

# Build omaha_score's lookup table now, while the server starts, instead of
# during your first decision (where it would eat into your time bank).
# Do any other slow setup (loading a model, ...) here too: the server must
# answer within 15 seconds of starting.
warmup()

# rename as your team/bot's name
PARTICIPANT = "YOUR EXACT TEAM NAME"
AGENT_NAME = "UjjwalBot"


# ===== YOUR CODE HERE =====

import random
import time
from collections import Counter


def _fallback(legal):
    return Action.CHECK_CALL if Action.CHECK_CALL in legal else Action.FOLD


def new_half(config: AgentConfig, memory: dict) -> None:
    try:
        memory.update(hands_played=0, used=0.0, bank=min(8.0, config.time_bank_seconds),
                      num_hands=config.num_hands, rng=random.Random(71823),
                      opp_actions=0, opp_raises=0, opp_folds=0, histories={})
    except Exception:
        return _fallback((Action.CHECK_CALL, Action.FOLD))


def _preflop(cards):
    ranks = Counter(c >> 2 for c in cards)
    suits = Counter(c & 3 for c in cards)
    score = sum((r / 8) ** 2 for r in ranks) * 0.10
    for r, n in ranks.items():
        if n >= 2:
            score += 0.15 + r * 0.025
        if n >= 3:
            score -= 0.22 * (n - 2)
    score += sum(0.10 for n in suits.values() if n >= 2)
    score -= sum(0.06 * (n - 2) for n in suits.values() if n > 2)
    unique = sorted(ranks)
    score += sum(0.035 if y - x == 1 else 0.015 if y - x == 2 else 0
                 for i, x in enumerate(unique) for y in unique[i + 1:])
    return score


def choose_action(obs: Observation, memory: dict) -> Action:
    try:
        started = time.perf_counter()
        try:
            legal = obs.legal_actions
            # Save the longest observed history; HandResult has no action history.
            memory.setdefault("histories", {})[obs.hand_index] = tuple(obs.action_history)
            rate = (memory.get("opp_raises", 0) + 2) / (memory.get("opp_actions", 0) + 8)
            if obs.street == Street.PREFLOP:
                strength = _preflop(obs.hole_cards)
                # Large reraises need a stronger range, even against maniacs.
                pressure = obs.to_call / max(1, obs.big_blind)
                threshold = 0.34 + min(0.24, pressure * 0.012)
                if rate > 0.65:
                    threshold -= 0.09
                if pressure > 1 and strength < threshold:
                    action = Action.FOLD
                elif strength > (0.77 if pressure > 2 else 0.63):
                    action = Action.RAISE_POT
                else:
                    action = Action.CHECK_CALL
            else:
                left = memory.get("bank", 8.0) - memory.get("used", 0.0)
                remaining = max(1, memory.get("num_hands", 1000) - obs.hand_index)
                # Reserve time for parsing/HTTP overhead and later decisions.
                budget = min(0.0025, max(0.0, (left - 0.8) / (remaining * 3.5)))
                if left < 0.9:
                    budget = 0.0
                deadline = started + budget
                known = set(obs.hole_cards) | set(obs.board)
                deck = [c for c in range(36) if c not in known]
                missing = 5 - len(obs.board)
                rng = memory["rng"]
                wins = 0.0
                samples = 0
                hero_river = omaha_score(obs.hole_cards, obs.board) if not missing else None
                for _ in range(40):
                    if time.perf_counter() >= deadline:
                        break
                    draw = rng.sample(deck, 5 + missing)
                    board = tuple(obs.board) + tuple(draw[5:])
                    hero = hero_river if hero_river is not None else omaha_score(obs.hole_cards, board)
                    villain = omaha_score(draw[:5], board)
                    wins += (hero > villain) + 0.5 * (hero == villain)
                    samples += 1
                equity = (wins + 1) / (samples + 2) if samples else 0.42
                raised = any(not h.is_me and h.street == obs.street and
                             h.action in (Action.RAISE_HALF, Action.RAISE_POT)
                             for h in obs.action_history)
                if raised:
                    equity *= 0.98 if rate > 0.65 else 0.91 if rate > 0.3 else 0.83
                odds = obs.to_call / max(1, obs.pot + obs.to_call)
                if obs.to_call and equity < odds + (0.015 if rate > 0.65 else 0.04):
                    action = Action.FOLD
                elif equity > (0.62 if rate > 0.65 else 0.68):
                    action = Action.RAISE_POT
                elif equity > 0.58 and not raised:
                    action = Action.RAISE_HALF
                else:
                    action = Action.CHECK_CALL
            return action if action in legal else _fallback(legal)
        finally:
            memory["used"] = memory.get("used", 0.0) + time.perf_counter() - started
    except Exception:
        return _fallback(obs.legal_actions)


def on_hand_end(result: HandResult, memory: dict) -> None:
    try:
        started = time.perf_counter()
        history = memory.setdefault("histories", {}).pop(result.hand_index, ())
        opponent = [h for h in history if not h.is_me]
        memory["opp_actions"] = memory.get("opp_actions", 0) + len(opponent)
        memory["opp_raises"] = memory.get("opp_raises", 0) + sum(
            h.action in (Action.RAISE_HALF, Action.RAISE_POT) for h in opponent)
        # A terminal opponent fold is absent from our final observation.
        memory["opp_folds"] = memory.get("opp_folds", 0) + int(
            not result.went_to_showdown and result.winner == "me")
        memory["hands_played"] = memory.get("hands_played", 0) + 1
        memory["opp_fold_rate"] = memory["opp_folds"] / memory["hands_played"]
        memory["used"] = memory.get("used", 0.0) + time.perf_counter() - started
    except Exception:
        return _fallback((Action.CHECK_CALL, Action.FOLD))

# ===== END OF YOUR CODE =====


# ===== SERVER PLUMBING (you normally don't need to edit below) =====
# The judge calls these routes:
#   GET  /           -> who you are (also used as the health check)
#   POST /new-half   -> start a fresh half: memory is wiped
#   POST /act        -> the judge sends any finished hands plus an Observation;
#                       on_hand_end() runs for each hand, then you answer an action
#   POST /hand-end   -> the judge sends the last finished hands of a half
#
# Why "async def"? The routes run on one thread and call your functions
# directly, so your functions never run twice at once. Your own functions
# stay normal "def" (don't make them async).
#
# Keep your per-half state in `memory`. In the tournament every half runs in
# a fresh server process, so everything starts over. When you test locally,
# though, one process can play both halves and only `memory` is wiped, NOT
# other global variables. Using `memory` makes your bot behave the same way
# in both places.

app = FastAPI()
MEMORY: dict = {}                                   # your memory for this half
STATUS = {"started": False}                         # has /new-half been called?
TOKEN = os.environ.get("AGENT_TOKEN") or None       # set by the tournament


async def _read_request(request: Request, path: str) -> tuple[dict, JSONResponse | None]:
    """Check the token (and that the half has started) BEFORE reading the body.

    Checking first means a request without the right token costs your bot
    almost nothing, so nobody else can slow it down by sending junk.
    Returns (body, None) when the request is fine, or ({}, error response).
    """
    if TOKEN and request.headers.get("x-agent-token") != TOKEN:
        return {}, JSONResponse({"error": "bad or missing X-Agent-Token"}, status_code=401)
    if not STATUS["started"] and path != "/new-half":
        return {}, JSONResponse({"error": "call /new-half first"}, status_code=409)
    try:
        body = await request.json()
    except ValueError:
        body = None
    if not isinstance(body, dict):
        return {}, JSONResponse({"error": "the request body must be a JSON object"}, status_code=400)
    return body, None


def _error_info(exc: Exception) -> dict:
    """Describe an exception from your code (call this inside `except`)."""
    return {"error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()}


def _crash(exc: Exception, hand_end_errors: list | None = None) -> JSONResponse:
    """Report an exception from your code to the judge (with traceback)."""
    return JSONResponse({**_error_info(exc), "hand_end_errors": hand_end_errors or []},
                        status_code=500)


def _deliver_results(raw_results) -> list:
    """Call on_hand_end() for each finished hand the judge sent.
    Returns a list of error reports (one per hand that crashed)."""
    errors = []
    for raw in raw_results or []:
        try:
            on_hand_end(HandResult.from_dict(raw), MEMORY)
        except Exception as exc:
            errors.append(_error_info(exc))
    return errors


@app.get("/")
async def info():
    """Health check: tells the judge who this bot is."""
    return {"participant": PARTICIPANT, "agent_name": AGENT_NAME}


@app.post("/new-half")
async def route_new_half(request: Request):
    """Wipe memory and call your new_half(). The body is {"config": {...}}."""
    body, refused = await _read_request(request, "/new-half")
    if refused:
        return refused
    MEMORY.clear()
    STATUS["started"] = True
    try:
        new_half(AgentConfig.from_dict(body.get("config", {})), MEMORY)
    except Exception as exc:
        return _crash(exc)
    return {"ok": True}


@app.post("/act")
async def route_act(request: Request):
    """Deliver finished hands, then turn the JSON into an Observation, call
    choose_action(), and send the answer back."""
    body, refused = await _read_request(request, "/act")
    if refused:
        return refused
    hand_end_errors = _deliver_results(body.get("hand_results"))
    try:
        obs = Observation.from_dict(body["observation"])
        action = choose_action(obs, MEMORY)
    except Exception as exc:
        return _crash(exc, hand_end_errors)
    # Send the action's name; anything strange is passed on for the judge to reject.
    if isinstance(action, Action):
        answer = action.name
    elif action is None or isinstance(action, (str, int, float, bool)):
        answer = action
    else:
        answer = repr(action)
    return {"action": answer, "hand_end_errors": hand_end_errors}


@app.post("/hand-end")
async def route_hand_end(request: Request):
    """Call on_hand_end() for the last finished hands of a half."""
    body, refused = await _read_request(request, "/hand-end")
    if refused:
        return refused
    return {"ok": True, "hand_end_errors": _deliver_results(body.get("results"))}


if __name__ == "__main__":
    # The tournament sets PORT as an environment variable, so each bot is compliant to our evaluation platform
    # Locally it defaults to 5008 for your own testing convenience
    port = int(os.environ.get("PORT", "5008"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info", access_log=False)
