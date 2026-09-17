# WM-103 — Market data client drops quotes during feed hiccups

Add retry logic to the market data client so a transient feed drop doesn't fail the
end-of-day pricing run. Run the existing marketdata tests after.
