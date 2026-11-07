# Poker bot v3: time safety

Before: v2 at `9f9babcae8acff32f313588a2daaa41a500c62d3`. After: the production v3 governor, with preflop scoring, call margins, raise thresholds, and bluff rules unchanged. Each match uses 1,000 deals per half (2,000 hands), seed 1 or 7, fresh servers on ports 5008/5009, and full judge JSON hand logs.

## Governor

Decision and hand-end work is charged through `time.perf_counter()` into half-local `memory["used"]`. The internal allowance is capped at 5.8 seconds or the configured bank, whichever is smaller. New Monte Carlo work is disabled from 5.0 seconds of internal use (or when at most 0.8 seconds remains), reserving time for cheap decisions and HTTP/JSON overhead. A smaller bank or a faster-than-planned burn rate reduces work earlier.

| Trigger (stronger limits override weaker ones) | Maximum samples | Simulation time cap |
|---|---:|---:|
| Healthy bank | 40 | Up to 1.9 ms |
| At least 4.5 s used, or less than 1.3 s left | 24 | Up to 1.0 ms |
| At least 4.8 s used, or less than 1.0 s left | 8 | Up to 0.4 ms |
| At least 5.0 s used, or at most 0.8 s left | 0 | 0 |

These are upper bounds, not minimum sample counts; every sample also checks a deadline. Optional showdown sampling stops from 4.8 seconds used or earlier if the configured bank requires it. The actual deadline is also reduced by (allowance remaining minus 0.8 s) / (remaining hands times 2.8), clamped at zero. When no samples fit, the bot reuses a raw equity estimate only for the same hand and board; otherwise it uses static made-hand estimates from the warmed evaluator table, with exactly two hole cards and three visible board cards. It never samples a hidden hand or runout in this emergency mode.

The previous 3.3-second internal allowance was already time-safe in these tests, but its fixed 0.42 fallback sacrificed strength under slowdown. A conservative candidate retained 3.3 seconds and passed all deadline-scaled matches, but chopped tight-passive seed 1 and both benchmark seeds in the callback-delay sweep. The selected governor preserves the full 40-sample policy while the measured bank can afford it, then reduces work near its five-second internal cutoff. It allows more capped sampling time and passes every requested deadline-scaled 2x CPU match without changing call, raise, preflop, or bluff thresholds. Independent screening on seeds 11 and 37 (1,000 deals per half, four local variants) found similar weakest-opponent means for the two candidates (+0.763 and +0.794 bb/deal); a third screen retained full sampling longer and achieved +1.31 bb/deal against the benchmark, with a +0.794 weakest-opponent mean and less than four seconds of slowed decision time per half. The full requested sweeps were the final quality gate.

## Slow-machine models

- **Deadline-scaled 2x CPU model (primary):** a temporary external server wrapper gives only the agent a clock running at twice real speed. Its Monte Carlo deadlines therefore allow half as much real computation. Decision and hand-end callbacks then wait for the same real duration as their computation, making their actual wall cost approximately double. The virtual clock already charges that doubled work to memory, so delay is not charged twice. Uvicorn and the judge retain normal clocks.
- **Callback-delay model (additional):** an external wrapper adds a busy delay equal to decision and hand-end computation. Decision delay runs within the callback accounting; added hand-end delay is charged explicitly. This independently checks bank depletion while keeping the ordinary per-decision sample allowance. Because delay is added after sampling, it does not consume the sampling loop deadline. It therefore changes the effective work allocation differently from a slower CPU; it is an additional diagnostic, not the requested CPU-clock acceptance test.

Only agent1 is slowed; opponents remain at normal speed. Startup and network transport are not artificially delayed. All wrappers and frozen temporary server files lived in `/tmp`, were never imported by the production bot, and were removed before committing.

## Before and after: deadline-scaled 2x CPU

Thinking times are judge-charged seconds for half 1 / half 2. WIN means the exact judge verdict `AGENT1_WIN`; CHOP is unchanged from the judge. Errors and flags refer to both bots, and were zero/absent in every match.

| Opponent | Seed | Before thinking H1 / H2 | Before verdict | After thinking H1 / H2 | After verdict | After bb/deal | After 95% CI |
|---|---:|---|---|---|---|---:|---|
| random | 1 | 1.240 / 1.277 | WIN | 2.523 / 2.898 | WIN | +8.203 | [+6.824, +9.582] |
| random | 7 | 1.355 / 1.415 | WIN | 2.428 / 2.338 | WIN | +7.264 | [+5.962, +8.566] |
| always_half | 1 | 0.719 / 0.753 | WIN | 2.669 / 2.536 | WIN | +11.914 | [+10.649, +13.179] |
| always_half | 7 | 0.842 / 1.036 | WIN | 2.535 / 2.749 | WIN | +10.708 | [+9.374, +12.042] |
| always_pot | 1 | 1.206 / 1.184 | WIN | 2.771 / 2.681 | WIN | +7.309 | [+5.794, +8.824] |
| always_pot | 7 | 1.244 / 1.182 | WIN | 2.954 / 4.274 | WIN | +5.366 | [+3.763, +6.969] |
| calling_station | 1 | 0.721 / 0.765 | WIN | 3.050 / 2.783 | WIN | +9.507 | [+8.674, +10.340] |
| calling_station | 7 | 0.672 / 0.687 | WIN | 2.854 / 2.850 | WIN | +8.954 | [+8.069, +9.839] |
| tight_passive | 1 | 1.446 / 1.338 | WIN | 3.051 / 2.661 | WIN | +0.757 | [+0.238, +1.276] |
| tight_passive | 7 | 1.297 / 1.294 | WIN | 2.343 / 2.724 | WIN | +0.800 | [+0.325, +1.275] |
| loose_aggressive | 1 | 1.453 / 1.311 | WIN | 2.653 / 2.539 | WIN | +1.928 | [+1.128, +2.728] |
| loose_aggressive | 7 | 1.378 / 1.235 | WIN | 3.219 / 2.611 | WIN | +1.599 | [+0.797, +2.401] |
| pot_raiser_folder | 1 | 0.075 / 0.024 | WIN | 0.088 / 0.035 | WIN | +6.588 | [+5.632, +7.544] |
| pot_raiser_folder | 7 | 0.041 / 0.044 | WIN | 0.118 / 0.147 | WIN | +6.483 | [+5.490, +7.476] |
| benchmark | 1 | 1.281 / 1.259 | WIN | 2.820 / 2.604 | WIN | +1.348 | [+0.731, +1.965] |
| benchmark | 7 | 1.369 / 1.258 | WIN | 2.501 / 2.897 | WIN | +1.211 | [+0.612, +1.810] |

## Additional callback-delay comparison

| Opponent | Seed | Before thinking H1 / H2 | Before verdict | After thinking H1 / H2 | After verdict | After bb/deal | After 95% CI |
|---|---:|---|---|---|---|---:|---|
| random | 1 | 1.481 / 1.876 | WIN | 3.012 / 3.164 | WIN | +7.510 | [+6.093, +8.926] |
| random | 7 | 1.555 / 1.533 | WIN | 3.390 / 3.550 | WIN | +7.723 | [+6.330, +9.116] |
| always_half | 1 | 1.253 / 1.426 | WIN | 2.957 / 2.948 | WIN | +11.070 | [+9.829, +12.311] |
| always_half | 7 | 1.463 / 1.271 | WIN | 3.157 / 3.162 | WIN | +10.416 | [+9.130, +11.702] |
| always_pot | 1 | 1.435 / 1.635 | WIN | 3.193 / 3.283 | WIN | +8.153 | [+6.655, +9.651] |
| always_pot | 7 | 1.596 / 1.565 | WIN | 3.398 / 3.228 | WIN | +5.915 | [+4.382, +7.448] |
| calling_station | 1 | 1.287 / 1.316 | WIN | 2.850 / 2.833 | WIN | +9.601 | [+8.757, +10.445] |
| calling_station | 7 | 1.261 / 1.582 | WIN | 3.001 / 2.896 | WIN | +9.091 | [+8.202, +9.980] |
| tight_passive | 1 | 1.552 / 1.718 | WIN | 3.414 / 3.512 | WIN | +1.024 | [+0.501, +1.547] |
| tight_passive | 7 | 1.651 / 1.631 | WIN | 3.555 / 4.305 | WIN | +0.547 | [+0.076, +1.018] |
| loose_aggressive | 1 | 1.514 / 1.463 | WIN | 4.334 / 3.950 | CHOP | +0.664 | [-0.257, +1.585] |
| loose_aggressive | 7 | 1.604 / 1.470 | WIN | 4.093 / 3.436 | WIN | +1.598 | [+0.783, +2.413] |
| pot_raiser_folder | 1 | 0.109 / 0.111 | WIN | 0.074 / 0.048 | WIN | +6.752 | [+5.813, +7.691] |
| pot_raiser_folder | 7 | 0.147 / 0.182 | WIN | 0.510 / 0.048 | WIN | +6.008 | [+4.972, +7.044] |
| benchmark | 1 | 1.772 / 1.747 | CHOP | 3.467 / 3.601 | CHOP | +0.475 | [-0.111, +1.061] |
| benchmark | 7 | 1.511 / 2.099 | WIN | 3.319 / 3.405 | WIN | +1.024 | [+0.486, +1.562] |

## Validation

- Requested deadline-scaled 2x CPU sweep: all 16 matches AGENT1_WIN. Additional post-decision-delay diagnostic: 14 AGENT1_WIN and 2 CHOP (loose_aggressive seed 1 and benchmark seed 1). The latter had positive bb/deal but confidence intervals spanning zero. All 32 final stress matches / 64 halves had 0 errors, no forfeits, and no TIME BANK EMPTY flags.
- Zero judge errors and zero timeouts confirm all observed requests completed inside the one-second request limit.
- `python -m pytest -q`: 19 passed, including governor stages, no-MC behavior, same-board cache reuse, optional-showdown cutoff, legal fallbacks, and opponent tracking.
- `./tools/check_build.sh`: ALL CHECKS PASSED, including network-disabled/read-only smoke testing. See `/tmp/poker-v3-build-check.log` for startup and request timings.
- Production strategy edits are confined to the marked block in `agent.py`; game.py, evaluator.py, judge_engine.py, requirements.txt, identity, and server plumbing are unchanged.

Machine-readable match summaries are in `time_safety_results.json`. Full raw reports, server logs, and judge JSON with hand logs remain in `/tmp/poker-v3-cpu2x-before/`, `/tmp/poker-v3-cpu2x-after/`, `/tmp/poker-v3-stress-before/`, and `/tmp/poker-v3-stress-after/` on the validation machine. The Docker log is `/tmp/poker-v3-build-check.log`. Time-capped samples and wall-clock measurements vary with machine load.
