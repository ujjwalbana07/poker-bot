# Local equity opponents

These opponents are frozen variants of the v1 bot at commit
`4d9016f8fd0d33d98d4f848a8dccb3e65f9c5141`.

- `benchmark.py`: exact copy of v1, including its independent memory and RNG.
- `tight_passive.py`: tighter preflop continuation, larger call margin, and
  substantially higher value-raise thresholds.
- `loose_aggressive.py`: wider preflop range, lower call margin, and lower
  value-raise thresholds.
- `pot_raiser_folder.py`: raises pot whenever possible but folds to large bets
  or reraises unless its underlying equity policy recommends a pot raise.

All four use the original feature-based preflop score and capped Monte Carlo
postflop equity. They are intentionally different policies, not claims about
how unseen tournament teams will play. Training screens used seeds 11 and 37;
the reported comparisons use seeds 1, 7, 21, and 99.

Run from the repository root, with the development dependencies installed in
`venv/`:

```sh
venv/bin/python local_opponents/validate.py --phase before
venv/bin/python local_opponents/validate.py --phase after
venv/bin/python local_opponents/validate.py --phase baselines
```

Each command uses 1,000 deals per half by default, restarts both HTTP servers
for every seed, and writes full judge reports, JSON with hand logs, and a
summary to `/tmp/poker-v2-<phase>/`. Both servers run on ports 5008 and 5009.
The before phase uses the frozen benchmark as agent1. The after and baselines
phases use the current root `agent.py`.

`RESULTS.md` records the final comparisons. The entire directory is excluded
from the tournament Docker image by `.dockerignore`.
