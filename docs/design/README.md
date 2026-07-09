# WOM Design Documents

This directory contains canonical WOM design intent.

Design documents describe why WOM is structured as it is.
They are AI-neutral and should be usable by Claude Code, ChatGPT Codex, and future AI development agents.

## Documents

```text
wom_canonical_concepts.md
  The design constitution of WOM.

demand_anchored_lot.md
  Demand Anchored Lot as the core traceable planning object.

psi_ppc_separation.md
  Separation between physical PSI planning and financial PPC evaluation.

scenario_modeling_principles.md
  How WOM scenarios should be modeled and documented.
```

## Canonical principle

WOM should remain:

```text
weekly
traceable
scenario-driven
capacity-aware
PSI/PPC-separated
AI-assisted but repository-grounded
```

## Maintenance rule

Design documents should not become scenario-specific manuals.

When a new scenario reveals a reusable WOM concept, update design documents.
When a detail belongs only to one scenario, update `docs/scenarios/`.
