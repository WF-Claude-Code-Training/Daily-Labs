# WM-110 — Drift alert false positives

Brief drift spikes can trigger noisy alerts even when a portfolio quickly returns within
its target band. Add hysteresis so an alert fires only when the breach lasts at least
`min_duration_minutes`.
