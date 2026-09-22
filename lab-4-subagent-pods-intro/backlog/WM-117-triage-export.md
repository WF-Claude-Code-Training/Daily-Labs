# WM-117: Ops is copy-pasting the triage report into a spreadsheet

The nightly reconciliation prints a nice report for humans. Ops needs it as data. They're
currently screen-scraping our stdout into Excel, which broke the first time we changed a
heading.

Give them a real export.

---

*Reframe this before you write code. "A real export" is not an outcome. Which format, which
columns, and which property of WM-106 must survive the translation?*
