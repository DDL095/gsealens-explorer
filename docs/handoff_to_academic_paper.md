# Handoff to academic-paper

> **Status**: Placeholder. Will be written in v0.8.1.
>
> This document will describe the field mapping and format conventions for
> handing off a gsealens-explorer report to the
> [academic-research-skills](https://github.com/Imbad0202/academic-research-skills)
> `academic-paper` mode.

## Planned scope (v0.8.1)

This document will cover:

- **Direction**: single-direction handoff (gsealens-explorer → academic-paper).
  No bidirectional sync.
- **Upstream contract**: what fields/sections a gsealens-explorer `report.md`
  must contain to be eligible for handoff.
- **Downstream contract**: what academic-paper's `academic-paper` mode expects
  as input (Results section draft, citation list, figure captions).
- **Field mapping table**: gsealens-explorer output fields → academic-paper
  Results section fields.
- **Citation handling**: how the PMID-verified citations in
  `evidence/literature_verification.json` are passed through to academic-paper
  (which has its own citation discipline requirements).
- **Figure handoff**: how the cascade heatmap / dot plot / leading edge
  figures (v0.7.1) are packaged and referenced.
- **Decoupling principle**: this handoff is a *recommended workflow*, not a
  hard dependency. Both projects should remain independently usable.

## Why a placeholder now

The roadmap references this file from v0.8.1, but the actual content depends
on:

1. gsealens-explorer's final report schema (stable from v0.6.1 onwards).
2. academic-paper mode's input contract (need to verify against the
   [academic-research-skills](https://github.com/Imbad0202/academic-research-skills)
   repo at handoff time).
3. Visualization outputs from v0.7.1.

Writing it prematurely would either underspecify the contract or be
invalidated by upstream changes.

## See also

- [Roadmap §v0.8.1](roadmap.md#v081--论文生态交接)
- [academic-research-skills](https://github.com/Imbad0202/academic-research-skills)
