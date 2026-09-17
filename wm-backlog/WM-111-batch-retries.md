# WM-111 — Nightly batch job fails without retrying

The nightly pricing batch in `ops/batch` should retry once on a transient database
timeout before failing the run. Validate against the existing batch test suite so
successful runs aren't affected.
