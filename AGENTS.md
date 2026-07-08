# AGENTS.md

# WOM AI Development Guide

This file is the common entry point for AI coding agents working on WOM.
It is intended for Claude Code, ChatGPT Codex, and other AI-assisted development environments.

WOM stands for Weekly Operation Model.
WOM is a weekly supply chain planning and simulation tool for PSI and PPC.

## 1. Read this first

Before editing code, read the following documents.

1. `README.md`
2. `docs/development/README.md`
3. `docs/architecture/README.md`
4. `docs/design/README.md`
5. `docs/scenarios/README.md`

If `CLAUDE.md` exists, it may contain Claude-specific context.
However, the canonical WOM knowledge should be maintained under `docs/`.

## 2. Repository knowledge policy

WOM development knowledge should be accumulated in the repository, not only in chat logs.

Important design decisions should be recorded as Markdown files under `docs/`.
Implementation changes should be traceable by Git commit.
Behavior changes should be validated by tests or reproducible sample scenarios.

Chat logs are useful for exploration.
Repository documents are the source of truth.

## 3. Core WOM concepts

WOM is based on the following core concepts.

- Weekly planning bucket
- PSI: Production or Purchase, Ship or Sales, Inventory
- Demand Anchored Lot
- Inbound Tree and Outbound Tree
- MOM node as Mother Plant or main supply node
- DAD node as distribution allocation or decoupling node
- Capacity-aware planning
- PPC: Price, Profit, Cost simulation
- Scenario-based supply chain modeling

Do not change these core concepts casually.
If a change is necessary, update the relevant design document first.

## 4. Development rules

When modifying code:

1. Keep existing sample models runnable.
2. Do not break `python -m main`.
3. Prefer small, reviewable changes.
4. Update documents when behavior or assumptions change.
5. Add or update tests when planning logic changes.
6. Do not mix unrelated refactoring with scenario changes.

## 5. Scenario rules

Sample scenarios under `data/sample/` are educational models.
They may use fictional companies, locations, prices, and capacities.

When adding or modifying a scenario:

1. Document the scenario intent.
2. Clearly separate fictional data from real-world references.
3. Keep CSV structure compatible with the existing engine.
4. Verify GUI and CLI execution where possible.

## 6. Planning Engine rule

The Planning Engine should remain as general and canonical as possible.

Scenario-specific behavior should be expressed by:

- input CSV files
- plugin layer
- scenario generator scripts
- parameter files
- documented assumptions

Avoid hard-coding scenario-specific logic inside the canonical engine.

## 7. PPC rule

PPC means Price, Profit, and Cost.

PPC changes should preserve the separation between:

- physical flow
- price propagation
- cost structure
- profit zone
- node-level P&L
- scenario-specific economic assumptions

## 8. AI agent behavior

AI agents should behave as careful development partners.

Before editing:

1. Inspect the existing files.
2. Understand the current branch and target release.
3. Propose the smallest safe change.
4. Explain assumptions.
5. Avoid destructive commands unless explicitly requested.

Never delete or rewrite large parts of the repository without clear instruction.

## 9. Current release intent

This branch prepares WOM v1r1m5 as an AI-neutral Vibe Coding Ready Release.

The goal is to make WOM development accessible from multiple AI coding environments by introducing:

- `AGENTS.md`
- structured `docs/`
- AI-neutral development guidance
- repository-based knowledge continuity