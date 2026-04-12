# Memory Index

## Project docs
- [background.md](background.md) — stack, run command, key internals, constraints
- [roadmap.md](roadmap.md) — feature scope, priorities, what we're not building
- [claude_best_practices.md](claude_best_practices.md) — Claude Code workflow rules, prompting tips, portfolio standards

## Key decisions
- Single file app (`app.py`) — split into `audit.py` + `app.py` only if it exceeds ~600 lines
- API keys are session-only — never persist anywhere
- Dark theme is intentional and consistent across all prototypes — don't lighten it
- Always `python -m pip install -r requirements.txt` before running the app or create a virtual environment once and persists it
