Here’s the **complete updated `README.md`** including:

* ✅ CI badge (clickable)
* ✅ Screenshots section
* ✅ Offline/cache-first demo steps
* ✅ Click-by-click usage
* ✅ Example results (your numbers)
* ✅ Outputs + audit artefacts
* ✅ Roadmap + disclaimer

Copy/paste this into `README.md`:

````markdown
# Nexus-PV — Automated Pharmacovigilance Signal Detection Engine  
*(openFDA → Dedup → Bayesian BCPNN/IC → Evaluation → Signal Packs)*

[![tests](https://github.com/sid7k/pharmacovigilance-bayesian-engine/actions/workflows/tests.yml/badge.svg)](https://github.com/sid7k/pharmacovigilance-bayesian-engine/actions/workflows/tests.yml)

Nexus-PV is an automated pharmacovigilance (PV) signal detection engine designed for **report-level** safety signal mining from **openFDA FAERS** data.  
It supports **Bayesian BCPNN / Information Component (IC)** with posterior uncertainty (**IC_025 / IC_975**), **deduplication (v1)**, and **dedup impact evaluation** with audit-ready artifacts.

> Focus: reproducible, auditable analytics suitable for publication and productization.

---

## Screenshots

**Cache-first run + audit artefacts**
![Cache + Metrics](screenshots/01_cache_metrics.png)

**Signal visualization (IC vs IC_025)**
![Signal Plot](screenshots/02_signal_plot.png)

**Dedup impact evaluation (Overlap@100 + Spearman ρ)**
![Dedup Impact](screenshots/03_dedup_impact.png)

---

## What it does (end-to-end workflow)

1. **Ingest (openFDA FAERS)**
   - Reliable ingestion with retries, chunked pagination, IPv4 forcing  
   - **Cache-first mode**: loads cached `cache/openfda_event_limit*.json` if available

2. **Deduplicate (v1)**
   - Similarity scoring + clustering (canonical report mapping)

3. **Signal Detection**
   - **Report-level** BCPNN / IC
   - Bayesian posterior sampling for **IC_025 / IC_975** credible intervals

4. **Dedup Impact Evaluation**
   - Overlap@K (e.g., Overlap@100)
   - Spearman rank correlation
   - Tables: disappeared / appeared / shared signals

5. **Signal Packs**
   - Exports standardized signal pack artifacts to `artifacts/signal_packs/`

---

## Key Features

- ✅ **Report-level** unit of analysis (N = safety reports)
- ✅ Bayesian posterior IC with **IC_025 / IC_975** using Dirichlet sampling over the 2×2 table
- ✅ Deduplication (v1) via overlap scoring + clustering
- ✅ Dedup impact evaluation (Overlap@100, Spearman ρ, disappeared/appeared/shared)
- ✅ Audit artifacts: `run_id`, dataset fingerprints, `code_fingerprint`
- ✅ openFDA reliability: retries + pagination + IPv4 forcing + cache-first
- ✅ Streamlit `session_state` persistence (results survive button clicks)
- ✅ Signal pack export to `artifacts/signal_packs/`

---

## Repository Layout (high-level)

- `app/` — Streamlit UI (`app/main.py`)
- `src/ingest_openfda.py` — openFDA ingestion + caching + retries
- `src/dedup.py` — deduplication (v1)
- `src/bcpnn.py` — BCPNN / IC computation + Bayesian IC intervals
- `src/evaluate_dedup.py` — dedup impact evaluation metrics & tables
- `src/audit_utils.py` — run_id + fingerprint utilities
- `src/signal_pack.py` — signal pack export
- `cache/` — cached openFDA payloads (optional)
- `artifacts/signal_packs/` — outputs
- `tests/` — unit tests + CI support
- `.github/workflows/tests.yml` — GitHub Actions CI workflow

---

## Quickstart

### 1) Create environment
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
````

### 2) Run the Streamlit app

```bash
streamlit run app/main.py
```

---

## Recommended first run (fast + reproducible)

### A) Offline / cache-first demo (recommended)

1. Ensure this file exists:

   * `cache/openfda_event_limit300.json`
2. In the app sidebar:

   * Set **openFDA Record Limit = 300**
   * (Optional) Enable deduplication and set threshold (e.g., **0.92**)
3. Click **Run Signal Detection**

If cache exists, the app will display:

* ✅ Loaded from cache: `cache/openfda_event_limit300.json`

### B) First-time (no cache yet)

1. Set **openFDA Record Limit = 300**
2. Click **Run Signal Detection**
3. After the run, a cache file should appear under `cache/`
4. Re-run with the same limit to use cache-first automatically

---

## How to use the app (click-by-click)

### Run signal detection

1. Set parameters (sidebar):

   * `openFDA Record Limit` (start with 300)
   * `Minimum co-occurrences (a)` (default 3)
   * `Posterior samples` (e.g., 4000)
2. (Optional) Enable **Deduplication (v1)**
3. Click **Run Signal Detection**

### Run dedup impact evaluation

1. Ensure Deduplication is enabled
2. Click **Run Dedup Impact Evaluation**
3. Review:

   * Overlap@100
   * Spearman ρ
   * disappeared / appeared / shared tables

### Generate signal packs

1. Tick **Generate Signal Packs (JSON)**
2. Signal packs are written to:

   * `artifacts/signal_packs/`

---

## Example Results (300-report demo run)

* Original reports: **300**
* Deduped reports (N): **264**
* Duplicates removed: **12.0%**
* Pairs evaluated (a ≥ min): **39**
* Positive signals (IC_025 > 0): **18**
* Dedup impact:

  * **Overlap@100 ≈ 39%**
  * **Spearman ρ ≈ 0.992**

Interpretation:

* Deduplication can significantly change the **top triage list** (Overlap@100),
* while preserving stability among shared ranked signals (high ρ).

---

## Outputs

### Audit artifacts

Each run records:

* `run_id`
* dataset fingerprints
* `code_fingerprint`

These enable reproducibility: *same inputs + same code → same outputs.*

### Signal packs

Signal packs are written to:

* `artifacts/signal_packs/`

Each pack includes:

* drug–event identifiers
* IC metrics (IC, IC_025, IC_975)
* counts and filters used
* provenance references (run_id, fingerprints)

---

## Tests

Run locally:

```bash
python -m pytest -q
```

CI is configured to run tests on every push and pull request via:

* `.github/workflows/tests.yml`

---

## Regulatory & Method Notes (Important)

Nexus-PV is currently a **signal detection + evaluation engine**.
A production MHRA/EMA-grade signal management system typically also requires:

* signal registry & lifecycle state transitions (detect → validate → assess → close)
* rationale logging and sign-offs
* immutable audit trail

These are planned roadmap items.

---

## Roadmap (next)

* Signal Registry + lifecycle state transitions
* Immutable event log (append-only audit trail)
* MedDRA normalization + RxNorm ingredient mapping
* Dedup v2: case-version aware logic + probabilistic linkage calibration
* Temporal trending (time-sliced IC) and stratification
* External validation plan (e.g., OMOP/RWD confirmation)

---

## Disclaimer

This software is for research and engineering demonstration.
It does not replace medical judgment, formal pharmacovigilance processes, or regulatory obligations.
