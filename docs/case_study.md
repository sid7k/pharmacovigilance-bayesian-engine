# Case Study — Nexus-PV: Report-level Bayesian IC Signal Detection with Dedup Impact Evaluation

## Summary
Nexus-PV is an end-to-end pharmacovigilance signal detection engine built on openFDA FAERS data.  
It implements **report-level** BCPNN / Information Component (IC) with Bayesian uncertainty bounds (**IC_025 / IC_975**), includes **deduplication (v1)**, and quantifies how dedup changes signal prioritization using **Overlap@K** and **Spearman rank correlation**.

**Why this matters:** duplicate reports can materially change which signals appear in the top triage list; a PV analytics system needs both *signal detection* and *evidence about how preprocessing changes the results*.

---

## Problem
Spontaneous reporting systems (e.g., FAERS) are noisy and may contain duplicate or near-duplicate reports.  
Disproportionality methods can produce different top-ranked drug–event pairs depending on whether duplicates are present. That can impact:
- clinical triage workload,
- signal prioritization consistency,
- auditability and repeatability of analyses.

---

## Approach

### Pipeline (end-to-end)
1. **Ingest:** openFDA FAERS ingestion with retries + pagination and **cache-first mode**  
2. **Dedup (v1):** similarity scoring + clustering to map reports to a canonical representation  
3. **Signal Detection:** report-level BCPNN/IC with Bayesian posterior sampling for IC uncertainty  
4. **Dedup Impact Evaluation:** stability metrics and appeared/disappeared/shared signal tables  
5. **Signal Packs:** JSON evidence packs written to `artifacts/signal_packs/`

### Methods (technical)
- **Unit of analysis:** report-level (unique reports)  
- **Metric:** BCPNN / Information Component (IC) computed from a 2×2 contingency table per drug–event pair  
- **Uncertainty:** Bayesian posterior sampling over the 2×2 cell probabilities → **IC_025 / IC_975**  
- **Signal rule (screening):** IC_025 > 0 (conservative lower credible bound)

---

## Results (demo run)
Configuration:
- openFDA Record Limit: **300**
- Minimum co-occurrences: **a ≥ 3**
- Posterior samples per pair: **4000**
- Dedup enabled (threshold: **0.92**)

Key outcomes:
- Original reports: **300**
- Deduped reports: **264**
- Duplicates removed: **12.0%**
- Pairs evaluated (a ≥ min): **39**
- Positive signals (IC_025 > 0): **18**

### Dedup impact (baseline vs dedup)
- **Overlap@100:** **39/100 (39.0%)**
- **Spearman ρ (shared pairs):** **0.992**

Interpretation:
- Deduplication significantly changes the **top triage shortlist** (low-to-moderate overlap),
- while maintaining **high rank stability among shared signals** (very high ρ).

---

## Auditability & Reproducibility
Each run captures:
- **run_id**
- dataset fingerprints (input provenance)
- **code_fingerprint** (hash of key modules)

This supports reproducibility and traceability: *same input + same code → same outputs.*

---

## Limitations (current)
- Dedup v1 is similarity-based and not yet case-version aware (follow-up vs duplicate not explicitly modeled)
- Confounding controls (stratification, temporal trending) are limited in the current prototype
- openFDA does not provide full narrative detail available in full ICSRs

---

## Roadmap (next improvements)
- **Signal Registry** with lifecycle states (detect → validate → assess → close)
- Immutable audit event log (append-only)
- MedDRA normalization and RxNorm ingredient mapping
- Dedup v2: case-version handling + calibration
- Temporal trending (time-sliced IC) and stratified analyses
- External validation pathway (e.g., OMOP/RWD confirmation)

---

## Deliverables
- Streamlit application for interactive signal analysis
- JSON signal packs for each detected signal (`artifacts/signal_packs/`)
- Unit tests + CI pipeline (GitHub Actions)