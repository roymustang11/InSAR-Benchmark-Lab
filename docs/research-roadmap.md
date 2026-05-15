# Research Roadmap

## Phase 1: Subsidence Validation Foundation

Scientific question: how reliably do open InSAR products measure groundwater-related land subsidence in California's Central Valley?

Deliverables:

- Study-area configuration for the Central Valley.
- Validation metrics for InSAR-vs-GNSS time series.
- Notebook sequence for product organization, validation, uncertainty checks, and final figures.
- Clear documentation of data provenance and reference-frame assumptions.

## Phase 2: Workflow Comparison

Scientific question: how do OPERA, HyP3/ARIA, MintPy-compatible, and phase-linking workflows differ in velocity, residuals, uncertainty, and spatial coverage?

Deliverables:

- Common product-loading interfaces.
- Benchmark tables for multiple workflows.
- Reference-point sensitivity analysis.
- Coherence and masking sensitivity analysis.

## Phase 3: Volcano Extension

Scientific question: can the same validation framework characterize nonlinear volcanic deformation and event-like signals?

Deliverables:

- Volcano study-area config.
- Event-window time-series diagnostics.
- Phase-linking comparison on decorrelating surfaces.

## Phase 4: Landslide Extension

Scientific question: can the same framework support localized slope-deformation monitoring under coherence loss?

Deliverables:

- Landslide study-area config.
- Local time-series extraction utilities.
- Masking and coherence-loss diagnostics.
- Alert-style summary plots.
