# Nexus-PV: Bayesian Pharmacovigilance Signal Engine

## Overview
Nexus-PV is a Predictive Pharmacovigilance Platform designed to identify disproportionate reporting of adverse drug events. By bridging official regulatory datasets with advanced statistical modeling, this engine calculates the Information Component (IC) using the Bayesian Confidence Propagation Neural Network (BCPNN) methodology. 

This approach handles small sample sizes and zero-count reporting limits more effectively than traditional frequentist methods, providing robust 95% confidence intervals for early signal detection.

## Professional Context
This architecture was engineered by a Technical Orchestrator with an MSc in Pharmacology and 5 years of Commercial Operations Leadership and Independent Clinical R&D. It demonstrates the ability to build complex, enterprise-ready data pipelines, moving from raw API ingestion to professional clinical dashboards.

## Core Features
* **Fault-Tolerant Data Ingestion:** Automated pipeline fetching real-world safety reports from the openFDA API, featuring built-in timeout handling and synthetic fallback data for continuous testing.
* **Bayesian Statistical Engine:** Implementation of BCPNN logic to calculate Information Components (IC), automatically flagging positive safety signals when the lower 95% confidence interval exceeds zero.
* **Interactive Clinical UI:** A streamlined Streamlit dashboard featuring Plotly-powered Volcano plots, allowing reviewers to visually isolate and investigate drug-event pairs instantly.

## Tech Stack
* **Language:** Python 3.10
* **Data Processing & Statistics:** Pandas, NumPy, SciPy
* **Frontend Visualization:** Streamlit, Plotly
* **External APIs:** openFDA (FAERS Data)

## How to Run Locally

1. **Activate your virtual environment:**
   ```bash
   venv\Scripts\activate