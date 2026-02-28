import streamlit as st
import plotly.express as px
import pandas as pd
import sys
import os
import uuid

# Add the root project directory to the path so we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.fetch_fda import fetch_openfda_data
from src.bcpnn import calculate_bcpnn_ic

# Registry imports
from src.registry.db import get_conn, init_db
from src.registry.service import register_signal, update_status, update_notes
from src.registry.export_pack import export_signal_pack

# Configure the page
st.set_page_config(page_title="Nexus-PV | Signal Engine", layout="wide")

st.title("Nexus-PV: Bayesian Signal Detection Engine")
st.markdown("Automated pharmacovigilance pipeline utilizing openFDA data and the BCPNN methodology.")

# Initialize registry DB once per session
if "registry_ready" not in st.session_state:
    _conn = get_conn()
    init_db(_conn)
    st.session_state["registry_ready"] = True

# Keep a single DB connection handle in session_state
if "registry_conn" not in st.session_state:
    st.session_state["registry_conn"] = get_conn()
conn = st.session_state["registry_conn"]

# Session storage keys
st.session_state.setdefault("run_id", None)
st.session_state.setdefault("df_safety", None)
st.session_state.setdefault("signals_df", None)
st.session_state.setdefault("positive_signals", None)
st.session_state.setdefault("selected_signal_id", "")
st.session_state.setdefault("notes_prefill", "")

# Sidebar Controls
st.sidebar.header("Pipeline Controls")
record_limit = st.sidebar.slider("openFDA Record Limit", min_value=100, max_value=5000, value=1000, step=100)
run_pipeline = st.sidebar.button("Run Signal Detection")

if run_pipeline:
    # New run id each time you run pipeline
    st.session_state["run_id"] = str(uuid.uuid4())

    with st.spinner("Fetching data from openFDA API..."):
        df_safety = fetch_openfda_data(limit=record_limit)

    if not df_safety.empty:
        with st.spinner("Calculating Bayesian Information Components (IC)..."):
            signals_df = calculate_bcpnn_ic(df_safety, 'Drug', 'Event')
            positive_signals = signals_df[signals_df['Signal_Detected'] == True].copy()

            st.session_state["df_safety"] = df_safety
            st.session_state["signals_df"] = signals_df
            st.session_state["positive_signals"] = positive_signals
    else:
        st.error("Failed to retrieve data. Please check your connection or the API limits.")

# Use saved results
df_safety = st.session_state.get("df_safety")
signals_df = st.session_state.get("signals_df")
positive_signals = st.session_state.get("positive_signals")
run_id = st.session_state.get("run_id")

if df_safety is not None and isinstance(df_safety, pd.DataFrame) and not df_safety.empty:
    # Metrics
    st.subheader("Pipeline Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports Analyzed", len(df_safety))
    col2.metric("Unique Drug-Event Pairs", len(signals_df) if signals_df is not None else 0)
    col3.metric("Positive Signals Detected", len(positive_signals) if positive_signals is not None else 0)
    st.caption(f"run_id: `{run_id}`")
    st.divider()

    # Volcano plot
    if signals_df is not None and not signals_df.empty:
        st.subheader("Signal Visualization (Volcano Plot)")
        fig = px.scatter(
            signals_df,
            x='IC',
            y='IC_025',
            color='Signal_Detected',
            hover_data=['drug_total', 'event_total', 'observed_count'],
            hover_name=signals_df['Drug'].astype(str) + " - " + signals_df['Event'].astype(str),
            labels={'IC': 'Information Component (IC)', 'IC_025': 'Lower 95% CI (IC_025)'},
            color_discrete_map={True: '#ef553b', False: '#636efa'},
            title="BCPNN Signal Strength Distribution"
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig, use_container_width=True)

    # Output table
    if positive_signals is not None:
        st.subheader("Detected Signals Output")
        show_cols = ['Drug', 'Event', 'observed_count', 'expected_count', 'IC', 'IC_025', 'IC_975']
        available_cols = [c for c in show_cols if c in positive_signals.columns]
        st.dataframe(positive_signals[available_cols], use_container_width=True)

        # =========================
        # Signal Registry UI
        # =========================
        st.divider()
        st.header("Signal Registry (Governance Layer)")

        # Registered signals table + dropdown
        st.subheader("Registered Signals (from SQLite)")
        reg_df = pd.read_sql_query(
            "SELECT signal_id, drug_key, event_key, status, priority, ic, ic025, ic975, first_seen_run, last_seen_run, updated_at "
            "FROM signal_registry ORDER BY updated_at DESC",
            conn
        )

        if reg_df.empty:
            st.info("No registered signals yet. Register one from the detected list below.")
        else:
            st.dataframe(reg_df, use_container_width=True)
            pick_id = st.selectbox("Select a registered signal_id", reg_df["signal_id"].tolist())
            st.session_state["selected_signal_id"] = pick_id
            st.caption(f"Selected signal_id: `{pick_id}`")

        # Register from detected list
        if len(positive_signals) == 0:
            st.info("No positive signals to register for this run.")
        else:
            st.write("Register a signal from the detected list:")
            idx = st.number_input(
                "Row index to register",
                min_value=0,
                max_value=max(len(positive_signals) - 1, 0),
                value=0,
                step=1
            )

            row = positive_signals.iloc[int(idx)]
            drug_key = str(row.get("Drug", "")).strip().lower()
            event_key = str(row.get("Event", "")).strip().lower()
            st.caption(f"Selected: **{row.get('Drug')} — {row.get('Event')}**")

            colR1, colR2 = st.columns(2)

            with colR1:
                if st.button("✅ Register selected signal"):
                    signal_id = register_signal(
                        conn,
                        drug_key=drug_key,
                        event_key=event_key,
                        run_id=run_id,
                        metrics={
                            "ic": float(row.get("IC", 0) or 0),
                            "ic025": float(row.get("IC_025", 0) or 0),
                            "ic975": float(row.get("IC_975", 0) or 0),
                            "n11": int(row.get("observed_count", 0) or 0),
                            "n1p": int(row.get("drug_total", 0) or 0),
                            "np1": int(row.get("event_total", 0) or 0),
                            "npp": int(len(df_safety)),
                        },
                    )
                    st.session_state["selected_signal_id"] = signal_id
                    st.success(f"Registered signal_id: **{signal_id}**")

            with colR2:
                if st.button("⚡ Register Top 10 signals"):
                    top = positive_signals.head(10).copy()
                    created = 0
                    for _, r in top.iterrows():
                        register_signal(
                            conn,
                            drug_key=str(r.get("Drug", "")).strip().lower(),
                            event_key=str(r.get("Event", "")).strip().lower(),
                            run_id=run_id,
                            metrics={
                                "ic": float(r.get("IC", 0) or 0),
                                "ic025": float(r.get("IC_025", 0) or 0),
                                "ic975": float(r.get("IC_975", 0) or 0),
                                "n11": int(r.get("observed_count", 0) or 0),
                                "n1p": int(r.get("drug_total", 0) or 0),
                                "np1": int(r.get("event_total", 0) or 0),
                                "npp": int(len(df_safety)),
                            },
                        )
                        created += 1
                    st.success(f"Registered Top-10 signals ({created}).")

            # Update section (auto-filled)
            st.subheader("Update a registered signal")
            signal_id_in = st.text_input(
                "Signal ID",
                value=st.session_state.get("selected_signal_id", ""),
                placeholder="Select from dropdown above"
            )
            signal_id_in = (signal_id_in or "").strip()

            # Auto-load notes for selected signal
            if signal_id_in:
                _tmp = pd.read_sql_query(
                    "SELECT notes FROM signal_registry WHERE signal_id = ?",
                    conn,
                    params=(signal_id_in,)
                )
                if not _tmp.empty:
                    st.session_state["notes_prefill"] = _tmp.iloc[0]["notes"] or ""
                else:
                    st.session_state["notes_prefill"] = ""

            colA, colB = st.columns(2)
            with colA:
                new_status = st.selectbox("New Status", ["DETECTED", "VALIDATING", "ASSESSED", "CLOSED"])
            with colB:
                reason = st.text_input("Reason (optional)", placeholder="Why are you changing the status?")

            if st.button("🔁 Update Status"):
                if not signal_id_in:
                    st.error("Please select/enter a Signal ID first.")
                else:
                    update_status(conn, signal_id=signal_id_in, to_status=new_status, reason=reason, run_id=run_id)
                    st.success("Status updated.")

            notes = st.text_area(
                "Notes / Rationale",
                value=st.session_state.get("notes_prefill", ""),
                placeholder="Add your review notes here (why signal matters, next steps, etc.)"
            )

            if st.button("📝 Save Notes"):
                if not signal_id_in:
                    st.error("Please select/enter a Signal ID first.")
                else:
                    update_notes(conn, signal_id=signal_id_in, notes=notes)
                    st.success("Notes saved.")

            if st.button("📦 Export Signal Review Pack (PDF + JSON)"):
                if not signal_id_in:
                    st.error("Please select/enter a Signal ID first.")
                else:
                    pdf_path = export_signal_pack(
                        conn,
                        signal_id=signal_id_in,
                        provenance={
                            "run_id": run_id,
                            "record_limit": record_limit,
                            "app": "Nexus-PV Streamlit",
                        },
                    )
                    st.success(f"Exported review pack to: {pdf_path}")

else:
    st.info("👈 Adjust parameters in the sidebar and click 'Run Signal Detection' to start the pipeline.")