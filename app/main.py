import streamlit as st
import plotly.express as px
import pandas as pd
import sys
import os

# Add the root project directory to the path so we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.fetch_fda import fetch_openfda_data
from src.bcpnn import calculate_bcpnn_ic

# Configure the page
st.set_page_config(page_title="Nexus-PV | Signal Engine", layout="wide")

st.title("Nexus-PV: Bayesian Signal Detection Engine")
st.markdown("Automated pharmacovigilance pipeline utilizing openFDA data and the BCPNN methodology.")

# Sidebar Controls
st.sidebar.header("Pipeline Controls")
record_limit = st.sidebar.slider("openFDA Record Limit", min_value=100, max_value=5000, value=1000, step=100)
run_pipeline = st.sidebar.button("Run Signal Detection")

if run_pipeline:
    with st.spinner("Fetching data from openFDA API..."):
        # 1. Ingest Data
        df_safety = fetch_openfda_data(limit=record_limit)
        
    if not df_safety.empty:
        with st.spinner("Calculating Bayesian Information Components (IC)..."):
            # 2. Run BCPNN Math
            signals_df = calculate_bcpnn_ic(df_safety, 'Drug', 'Event')
            
            # Filter for positive signals (IC_025 > 0)
            positive_signals = signals_df[signals_df['Signal_Detected'] == True]
            
            # 3. Display High-Level Metrics
            st.subheader("Pipeline Metrics")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Reports Analyzed", len(df_safety))
            col2.metric("Unique Drug-Event Pairs", len(signals_df))
            col3.metric("Positive Signals Detected", len(positive_signals))
            
            st.divider()

            # 4. Interactive Volcano Plot Visualization
            st.subheader("Signal Visualization (Volcano Plot)")
            
            
            
            # Create a dynamic scatter plot
            fig = px.scatter(
                signals_df, 
                x='IC', 
                y='IC_025', 
                color='Signal_Detected',
                hover_data=['drug_total', 'event_total', 'observed_count'],
                hover_name=signals_df['Drug'] + " - " + signals_df['Event'],
                labels={'IC': 'Information Component (IC)', 'IC_025': 'Lower 95% CI (IC_025)'},
                color_discrete_map={True: '#ef553b', False: '#636efa'},
                title="BCPNN Signal Strength Distribution"
            )
            # Add a horizontal line at Y=0 (the threshold for a positive signal)
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            st.plotly_chart(fig, use_container_width=True)

            # 5. Data Table Output
            st.subheader("Detected Signals Output")
            st.dataframe(
                positive_signals[['Drug', 'Event', 'observed_count', 'expected_count', 'IC', 'IC_025', 'IC_975']],
                use_container_width=True
            )
    else:
        st.error("Failed to retrieve data. Please check your connection or the API limits.")
else:
    st.info("👈 Adjust parameters in the sidebar and click 'Run Signal Detection' to start the pipeline.")