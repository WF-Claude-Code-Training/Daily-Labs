# WM-114 — Historical pricing for backdated statements

Advisors sometimes need to reissue a client statement as of a prior date (e.g. after a late
trade correction). Today `get_price` only returns today's price — it needs to accept an
`as_of_date` and return the price as of that day instead.

Before anyone touches `pricing.py`, we need to know everywhere in the codebase that change
reaches — a simple `grep` for `get_price(` will find the direct calls, but won't tell you which
other functions depend on it indirectly, or what breaks in a client-facing statement if it's
wrong.
