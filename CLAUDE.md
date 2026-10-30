# Working in this repo

## Git

- Never push to `main`. Geoff merges and pushes to `main` himself.
- Do all work on a feature branch (e.g. `claude/<short-description>`), created from the latest `origin/main`.
- Committing to the feature branch and pushing the feature branch to GitHub is fine.
- Ask Geoff before opening a pull request. Don't open one unasked.

## Building

`python build.py narrow_gate` builds missions, maps, briefings, checks and tests. Commit the updated `dist/` files
with the source change that produced them. See README.md.
