# Poker bot v2 validation

Each individual match uses 1,000 duplicate deals (2,000 hands), fresh HTTP servers, and seed 1, 7, 21, or 99. Agent1 is the root bot; before measurements use the frozen v1 benchmark instead. Confidence intervals use the judge's normal approximation with z=1.96. Some individual variant matches may remain CHOP; baseline matches must all be AGENT1_WIN.

## Pooled comparison

Each row pools the four seeds: 4,000 independent duplicate deals, 8,000 hands per version. These pooled verdicts are computed from the judge's paired_bb data; they are separate from individual match verdicts.

| Opponent | Before bb/deal (95% CI) | Before verdict | After bb/deal (95% CI) | After verdict | Worst seed, before / after |
|---|---|---|---|---|---|
| tight_passive | +0.205 [-0.038, +0.448] | CHOP | +0.825 [+0.578, +1.071] | AGENT1_WIN | -0.006 / +0.523 |
| loose_aggressive | +0.531 [+0.122, +0.939] | AGENT1_WIN | +1.555 [+1.137, +1.973] | AGENT1_WIN | +0.002 / +1.253 |
| pot_raiser_folder | +0.618 [-0.182, +1.418] | CHOP | +6.389 [+5.888, +6.890] | AGENT1_WIN | -0.761 / +5.949 |
| benchmark | +0.183 [-0.053, +0.419] | CHOP | +1.151 [+0.861, +1.440] | AGENT1_WIN | -0.280 / +0.813 |

## Every local opponent match

| Opponent | Seed | Before bb/deal | Before 95% CI | Before verdict | After bb/deal | After 95% CI | After verdict |
|---|---|---|---|---|---|---|---|
| tight_passive | 1 | +0.357 | [-0.173, +0.887] | CHOP | +0.523 | [+0.004, +1.042] | AGENT1_WIN |
| tight_passive | 7 | +0.021 | [-0.477, +0.519] | CHOP | +1.089 | [+0.595, +1.583] | AGENT1_WIN |
| tight_passive | 21 | +0.447 | [-0.010, +0.904] | CHOP | +1.113 | [+0.632, +1.594] | AGENT1_WIN |
| tight_passive | 99 | -0.006 | [-0.458, +0.446] | CHOP | +0.574 | [+0.100, +1.048] | AGENT1_WIN |
| loose_aggressive | 1 | +0.899 | [+0.083, +1.715] | AGENT1_WIN | +1.925 | [+1.074, +2.776] | AGENT1_WIN |
| loose_aggressive | 7 | +0.002 | [-0.794, +0.798] | CHOP | +1.721 | [+0.897, +2.545] | AGENT1_WIN |
| loose_aggressive | 21 | +0.383 | [-0.457, +1.223] | CHOP | +1.320 | [+0.490, +2.150] | AGENT1_WIN |
| loose_aggressive | 99 | +0.839 | [+0.022, +1.656] | AGENT1_WIN | +1.253 | [+0.414, +2.092] | AGENT1_WIN |
| pot_raiser_folder | 1 | +1.061 | [-0.553, +2.675] | CHOP | +6.665 | [+5.728, +7.602] | AGENT1_WIN |
| pot_raiser_folder | 7 | -0.761 | [-2.355, +0.833] | CHOP | +6.446 | [+5.433, +7.459] | AGENT1_WIN |
| pot_raiser_folder | 21 | +1.100 | [-0.510, +2.710] | CHOP | +5.949 | [+4.916, +6.982] | AGENT1_WIN |
| pot_raiser_folder | 99 | +1.072 | [-0.509, +2.653] | CHOP | +6.496 | [+5.474, +7.518] | AGENT1_WIN |
| benchmark | 1 | +0.261 | [-0.234, +0.756] | CHOP | +1.436 | [+0.822, +2.050] | AGENT1_WIN |
| benchmark | 7 | +0.367 | [-0.113, +0.847] | CHOP | +1.005 | [+0.435, +1.575] | AGENT1_WIN |
| benchmark | 21 | -0.280 | [-0.701, +0.141] | CHOP | +0.813 | [+0.290, +1.336] | AGENT1_WIN |
| benchmark | 99 | +0.384 | [-0.103, +0.871] | CHOP | +1.348 | [+0.743, +1.953] | AGENT1_WIN |

## Final timing and baseline results

Times are judge-charged thinking seconds for half 1 / half 2. Average request wall time includes HTTP and serialization. Errors are summed over both halves. Flags include forfeits and exhausted banks on either bot.

| Group | Opponent | Seed | bb/deal | 95% CI | Verdict | Errors | Thinking H1 / H2 (s) | Average request (ms) | Flags |
|---|---|---|---|---|---|---|---|---|---|
| after | tight_passive | 1 | +0.523 | [+0.004, +1.042] | AGENT1_WIN | 0 | 1.339 / 1.493 | 1.278 | None |
| after | tight_passive | 7 | +1.089 | [+0.595, +1.583] | AGENT1_WIN | 0 | 0.977 / 1.175 | 1.150 | None |
| after | tight_passive | 21 | +1.113 | [+0.632, +1.594] | AGENT1_WIN | 0 | 1.227 / 1.100 | 1.183 | None |
| after | tight_passive | 99 | +0.574 | [+0.100, +1.048] | AGENT1_WIN | 0 | 1.063 / 1.029 | 1.132 | None |
| after | loose_aggressive | 1 | +1.925 | [+1.074, +2.776] | AGENT1_WIN | 0 | 1.185 / 1.250 | 1.126 | None |
| after | loose_aggressive | 7 | +1.721 | [+0.897, +2.545] | AGENT1_WIN | 0 | 1.368 / 1.050 | 1.124 | None |
| after | loose_aggressive | 21 | +1.320 | [+0.490, +2.150] | AGENT1_WIN | 0 | 1.090 / 1.047 | 1.077 | None |
| after | loose_aggressive | 99 | +1.253 | [+0.414, +2.092] | AGENT1_WIN | 0 | 1.112 / 1.099 | 1.081 | None |
| after | pot_raiser_folder | 1 | +6.665 | [+5.728, +7.602] | AGENT1_WIN | 0 | 0.043 / 0.025 | 0.344 | None |
| after | pot_raiser_folder | 7 | +6.446 | [+5.433, +7.459] | AGENT1_WIN | 0 | 0.044 / 0.056 | 0.360 | None |
| after | pot_raiser_folder | 21 | +5.949 | [+4.916, +6.982] | AGENT1_WIN | 0 | 0.123 / 0.086 | 0.472 | None |
| after | pot_raiser_folder | 99 | +6.496 | [+5.474, +7.518] | AGENT1_WIN | 0 | 0.038 / 0.043 | 0.359 | None |
| after | benchmark | 1 | +1.436 | [+0.822, +2.050] | AGENT1_WIN | 0 | 1.086 / 1.132 | 1.117 | None |
| after | benchmark | 7 | +1.005 | [+0.435, +1.575] | AGENT1_WIN | 0 | 1.371 / 1.152 | 1.174 | None |
| after | benchmark | 21 | +0.813 | [+0.290, +1.336] | AGENT1_WIN | 0 | 1.108 / 1.064 | 1.110 | None |
| after | benchmark | 99 | +1.348 | [+0.743, +1.953] | AGENT1_WIN | 0 | 1.217 / 1.138 | 1.141 | None |
| baselines | random | 1 | +8.370 | [+7.017, +9.722] | AGENT1_WIN | 0 | 0.867 / 0.979 | 1.023 | None |
| baselines | random | 7 | +8.438 | [+7.098, +9.779] | AGENT1_WIN | 0 | 1.245 / 0.964 | 1.091 | None |
| baselines | random | 21 | +7.641 | [+6.263, +9.018] | AGENT1_WIN | 0 | 0.948 / 1.038 | 1.050 | None |
| baselines | random | 99 | +7.513 | [+6.149, +8.877] | AGENT1_WIN | 0 | 0.948 / 0.953 | 1.035 | None |
| baselines | always_half | 1 | +11.530 | [+10.267, +12.793] | AGENT1_WIN | 0 | 0.852 / 0.794 | 0.936 | None |
| baselines | always_half | 7 | +10.726 | [+9.434, +12.018] | AGENT1_WIN | 0 | 0.807 / 0.830 | 0.935 | None |
| baselines | always_half | 21 | +10.802 | [+9.515, +12.089] | AGENT1_WIN | 0 | 0.790 / 0.803 | 0.931 | None |
| baselines | always_half | 99 | +10.572 | [+9.272, +11.872] | AGENT1_WIN | 0 | 0.765 / 0.828 | 0.931 | None |
| baselines | always_pot | 1 | +8.368 | [+6.863, +9.873] | AGENT1_WIN | 0 | 0.979 / 1.029 | 0.989 | None |
| baselines | always_pot | 7 | +7.140 | [+5.640, +8.640] | AGENT1_WIN | 0 | 1.031 / 0.989 | 0.998 | None |
| baselines | always_pot | 21 | +5.810 | [+4.239, +7.381] | AGENT1_WIN | 0 | 1.077 / 1.057 | 1.013 | None |
| baselines | always_pot | 99 | +5.611 | [+4.091, +7.131] | AGENT1_WIN | 0 | 3.677 / 1.959 | 1.565 | None |
| baselines | calling_station | 1 | +9.322 | [+8.467, +10.177] | AGENT1_WIN | 0 | 0.920 / 0.824 | 1.063 | None |
| baselines | calling_station | 7 | +9.367 | [+8.482, +10.252] | AGENT1_WIN | 0 | 0.804 / 0.965 | 1.058 | None |
| baselines | calling_station | 21 | +8.811 | [+7.964, +9.658] | AGENT1_WIN | 0 | 1.545 / 1.543 | 1.264 | None |
| baselines | calling_station | 99 | +9.620 | [+8.754, +10.486] | AGENT1_WIN | 0 | 0.833 / 0.841 | 1.032 | None |

## Implementation and validation

- Separate raise and fold-to-raise rates by street, plus a distinct fold-to-reraise statistic.
- Infer missing terminal opponent responses from HandResult and our last action.
- Score revealed showdown hands against eight legal random holdings; weak raised showdowns reduce value-range discounts.
- Use stronger range selection for river bets, and half-pot bluffs against observed over-folders.
- Preserve feature-only preflop decisions, legal action validation, and all three callback exception fallbacks.
- Cap postflop sampling at 1.35 ms per decision, with an internal 3.3-second budget and a reserve for remaining hands.
- Threshold screens used separate seeds 11 and 37 (300 deals each); the final selected candidate was frozen for the reported after/baseline runs. Equity-sample accumulation was screened and rejected.
- pytest: 16 passed, including four opponent-model/budget/fallback regression cases.
- Docker check: ALL CHECKS PASSED; 2.1-second startup; added image size rounds down to 0 MB.
- Only the marked strategy block changed in agent.py; identity, server plumbing, game.py, evaluator.py, judge_engine.py, and requirements.txt are unchanged.

Full judge reports, JSON hand logs, and server logs are under `/tmp/poker-v2-before/`, `/tmp/poker-v2-after/`, and `/tmp/poker-v2-baselines/` on the validation machine. The full Docker log is `/tmp/poker-v2-build-check.log`. Time-capped Monte Carlo can vary with machine load even when deal seeds match.
