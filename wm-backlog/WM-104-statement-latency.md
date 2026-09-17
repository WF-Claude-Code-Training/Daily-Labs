# WM-104 — Quarterly statement job is slow for large households

The statement job in `statements/` times out for households with 200+ positions. Profile
it and speed up the hot path, but keep the rendered statement byte-for-byte identical —
validate against the golden-file tests in `tests/statements/`. Don't change the output
format. Report the before/after timings and a diff of what you changed.
