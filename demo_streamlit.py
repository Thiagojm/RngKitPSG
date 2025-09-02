# Demo version of RngKit Streamlit app - works without hardware
import streamlit as st
import plotly.graph_objects as go
import time
import random
import numpy as np
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="RngKit 3.0 - Demo Version",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'collecting' not in st.session_state:
    st.session_state.collecting = False
if 'live_plotting' not in st.session_state:
    st.session_state.live_plotting = False
if 'zscore_data' not in st.session_state:
    st.session_state.zscore_data = []
if 'index_data' not in st.session_state:
    st.session_state.index_data = []
if 'collected_data' not in st.session_state:
    st.session_state.collected_data = []
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = datetime.now()
if 'sample_size' not in st.session_state:
    st.session_state.sample_size = 2048
if 'sample_interval' not in st.session_state:
    st.session_state.sample_interval = 1.0

def generate_demo_data():
    """Generate demo data based on current time and settings"""
    current_time = datetime.now()
    time_since_last = (current_time - st.session_state.last_update_time).total_seconds()
    
    # Only generate new data if enough time has passed
    if time_since_last >= st.session_state.sample_interval:
        # Simulate random data collection
        ones_count = random.randint(0, st.session_state.sample_size)
        
        # Add to collected data
        st.session_state.collected_data.append({
            'timestamp': current_time,
            'ones': ones_count,
            'sample_size': st.session_state.sample_size
        })
        
        # Update last update time
        st.session_state.last_update_time = current_time

def generate_live_plot_data():
    """Generate live plot data based on current time and settings"""
    current_time = datetime.now()
    time_since_last = (current_time - st.session_state.last_update_time).total_seconds()
    
    # Only generate new data if enough time has passed
    if time_since_last >= st.session_state.sample_interval:
        # Simulate random data
        ones_count = random.randint(0, st.session_state.sample_size)
        
        # Calculate Z-score
        if st.session_state.zscore_data:
            # Use existing data for calculation
            all_ones = [random.randint(0, st.session_state.sample_size) for _ in range(len(st.session_state.zscore_data) + 1)]
            all_ones[-1] = ones_count
        else:
            all_ones = [ones_count]
        
        index_number = len(st.session_state.zscore_data) + 1
        sums_csv = sum(all_ones)
        avrg_csv = sums_csv / index_number
        zscore_csv = (avrg_csv - (st.session_state.sample_size / 2)) / (((st.session_state.sample_size / 4) ** 0.5) / (index_number ** 0.5))
        
        # Update session state
        st.session_state.zscore_data.append(zscore_csv)
        st.session_state.index_data.append(index_number)
        
        # Update last update time
        st.session_state.last_update_time = current_time

def start_demo_collection(sample_size, sample_interval):
    """Start demo data collection"""
    st.session_state.collecting = True
    st.session_state.collected_data = []
    st.session_state.sample_size = sample_size
    st.session_state.sample_interval = sample_interval
    st.session_state.last_update_time = datetime.now()
    
    st.success("✅ Demo data collection started!")
    st.rerun()

def stop_demo_collection():
    """Stop demo data collection"""
    st.session_state.collecting = False
    st.success("⏹️ Demo data collection stopped!")
    st.rerun()

def start_demo_live_plot(sample_size, sample_interval):
    """Start demo live plotting"""
    st.session_state.live_plotting = True
    st.session_state.zscore_data = []
    st.session_state.index_data = []
    st.session_state.sample_size = sample_size
    st.session_state.sample_interval = sample_interval
    st.session_state.last_update_time = datetime.now()
    
    st.success("✅ Demo live plotting started!")
    st.rerun()

def stop_demo_live_plot():
    """Stop demo live plotting"""
    st.session_state.live_plotting = False
    st.success("⏹️ Demo live plotting stopped!")
    st.rerun()

def main():
    # Header
    st.title("🎲 RngKit 3.0 - Demo Version")
    st.markdown("**Demo Mode** - Simulates random data without hardware")
    st.markdown("---")
    
    # Create tabs
    tab1, tab2 = st.tabs(["📊 Demo Data Collection", "📈 Demo Live Plot"])
    
    with tab1:
        st.header("📊 Demo Data Collection")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("⚙️ Settings")
            
            sample_size = st.number_input(
                "Sample Size (bits):",
                min_value=8,
                value=2048,
                step=8,
                help="Must be divisible by 8"
            )
            
            sample_interval = st.number_input(
                "Sample Interval (seconds):",
                min_value=0.1,
                value=1.0,
                step=0.1,
                help="Time between samples"
            )
            
            if not st.session_state.collecting:
                if st.button("▶️ Start Demo Collection", type="primary", use_container_width=True):
                    start_demo_collection(sample_size, sample_interval)
            else:
                if st.button("⏹️ Stop Demo Collection", type="secondary", use_container_width=True):
                    stop_demo_collection()
        
        with col2:
            st.subheader("📈 Collection Status")
            
            # Auto-updating collection status
            @st.fragment(run_every=1)
            def update_collection_status():
                if st.session_state.collecting:
                    # Generate new data
                    generate_demo_data()
                    
                    st.success("🟢 Collecting Demo Data")
                    if st.session_state.collected_data:
                        data_count = len(st.session_state.collected_data)
                        latest_data = st.session_state.collected_data[-1]
                        
                        col_stat1, col_stat2 = st.columns(2)
                        with col_stat1:
                            st.metric("Samples", data_count)
                        with col_stat2:
                            st.metric("Latest Ones", latest_data['ones'])
                        
                        # Show recent data
                        if len(st.session_state.collected_data) > 10:
                            recent_data = st.session_state.collected_data[-10:]
                            ones_values = [d['ones'] for d in recent_data]
                            st.line_chart(ones_values)
                else:
                    st.info("🟡 Demo Collection Idle")
            
            update_collection_status()
    
    with tab2:
        st.header("📈 Demo Live Plot")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("⚙️ Settings")
            
            live_sample_size = st.number_input(
                "Sample Size (bits):",
                min_value=8,
                value=2048,
                step=8,
                key="live_sample_size"
            )
            
            live_sample_interval = st.number_input(
                "Sample Interval (seconds):",
                min_value=0.1,
                value=1.0,
                step=0.1,
                key="live_sample_interval"
            )
            
            if not st.session_state.live_plotting:
                if st.button("▶️ Start Demo Live Plot", type="primary", use_container_width=True):
                    start_demo_live_plot(live_sample_size, live_sample_interval)
            else:
                if st.button("⏹️ Stop Demo Live Plot", type="secondary", use_container_width=True):
                    stop_demo_live_plot()
            
            if st.session_state.live_plotting:
                st.success("🟢 Demo Live Plotting Active")
            else:
                st.info("🟡 Demo Live Plot Idle")
        
        with col2:
            st.subheader("📊 Live Z-Score Chart")
            
            # Auto-updating live chart
            @st.fragment(run_every=1)
            def update_demo_chart():
                if st.session_state.live_plotting:
                    # Generate new data
                    generate_live_plot_data()
                
                if st.session_state.zscore_data and st.session_state.index_data:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=st.session_state.index_data,
                        y=st.session_state.zscore_data,
                        mode='lines',
                        name='Z-Score',
                        line=dict(color='orange', width=2)
                    ))
                    
                    # Add reference lines
                    fig.add_hline(y=2, line_dash="dash", line_color="red", annotation_text="+2σ")
                    fig.add_hline(y=-2, line_dash="dash", line_color="red", annotation_text="-2σ")
                    fig.add_hline(y=0, line_dash="dot", line_color="gray", annotation_text="Expected")
                    
                    fig.update_layout(
                        title="Demo Live Z-Score Plot",
                        xaxis_title=f"Number of samples (one sample every {live_sample_interval} second(s))",
                        yaxis_title=f"Z-Score - Sample Size = {live_sample_size} bits",
                        height=400,
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show current statistics
                    if st.session_state.zscore_data:
                        current_zscore = st.session_state.zscore_data[-1]
                        current_samples = st.session_state.index_data[-1]
                        
                        col_stat1, col_stat2, col_stat3 = st.columns(3)
                        with col_stat1:
                            st.metric("Current Z-Score", f"{current_zscore:.3f}")
                        with col_stat2:
                            st.metric("Samples Collected", current_samples)
                        with col_stat3:
                            if current_zscore > 2:
                                st.metric("Status", "🔴 High", delta="Above +2σ")
                            elif current_zscore < -2:
                                st.metric("Status", "🔴 Low", delta="Below -2σ")
                            else:
                                st.metric("Status", "🟢 Normal", delta="Within ±2σ")
                else:
                    st.info("📊 Chart will appear here when demo live plotting starts")
            
            update_demo_chart()

if __name__ == "__main__":
    main()
