# Local model benchmark logs

`make test-local-models` (or `python3 scripts/smoke_local_models.py`) writes a
`local_models_<date>.md` log here. Each log records the Ollama version, host,
and per-model latency, token counts, and whether the answer was valid JSON in
the expected shape.

Only commit logs from real runs. A model counts as run for the submission only
when its row says `Passed: yes` in a committed log.
