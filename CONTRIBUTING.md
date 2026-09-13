# Contributing to UNLOOP

Thanks for helping build a healthier music discovery loop.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e '.[dev]'
pytest
ruff check .
mypy src
```

## Principles

1. Keep the recommendation engine independent of playback providers.
2. Never commit API keys, OAuth tokens, listening exports, or user identifiers.
3. Prefer explainable ranking signals over opaque magic numbers.
4. New provider integrations must degrade gracefully when unavailable.
5. Tests are required for scoring changes.

## Pull requests

Keep PRs focused. Explain the user-visible behavior change and include tests where applicable.
