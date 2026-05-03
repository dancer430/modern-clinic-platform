# Internal Docs

This directory holds internal-team-only documentation: change governance,
the active change roadmap, and the product overview. New hires can skip
this directory until they need to make a non-trivial change or want the
high-level product picture.

## Index

- [`change-governance.md`](change-governance.md) — when an OpenSpec
  change is required, what artifacts each change must contain, and the
  readiness gate before implementation begins.
- [`change-roadmap.md`](change-roadmap.md) — current ordered chain of
  OpenSpec changes and the recommended reading order.
- [`PRODUCT_OVERVIEW.md`](PRODUCT_OVERVIEW.md) — product positioning,
  target users, core modules, and current product status.
- [`../superpowers/specs/`](../superpowers/specs/) — design specs for
  the active full-stack refactor program.

## When to read what

- Onboarding a new module / first PR → start at the root
  [`README.md`](../../README.md), then [`../setup.md`](../setup.md).
- Proposing a non-trivial change → `change-governance.md`, then create
  an entry under `openspec/changes/<change-name>/`.
- Picking up the next refactor task → `change-roadmap.md` + the active
  spec under `../superpowers/specs/`.
- Explaining the product to a stakeholder → `PRODUCT_OVERVIEW.md`.
