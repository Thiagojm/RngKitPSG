# Default imports
import time
import secrets
import os
import sys
from datetime import datetime, timedelta

# External imports
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from bitstring import BitArray
import serial
from serial.tools import list_ports
import pandas as pd
import numpy as np

# Internal imports

# Make 'src' importable for the service layer
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from rngkit.services import filenames as fn_service  # type: ignore
from rngkit.services import storage as storage_service  # type: ignore
from rngkit.services import utils as svc_utils  # type: ignore
from rngkit.devices import bitbabbler as dev_bitb  # type: ignore
from rngkit.devices import truerng as dev_trng  # type: ignore
from rngkit.devices import pseudo as dev_pseudo  # type: ignore

# Page configuration
st.set_page_config(
    page_title="RngKit 3.0 - Streamlit Version",
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
if 'current_values' not in st.session_state:
    st.session_state.current_values = {}
if 'collected_data' not in st.session_state:
    st.session_state.collected_data = []
if 'file_name' not in st.session_state:
    st.session_state.file_name = ""
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = datetime.now()
if 'sample_size' not in st.session_state:
    st.session_state.sample_size = 2048
if 'sample_interval' not in st.session_state:
    st.session_state.sample_interval = 1.0
if 'csv_ones' not in st.session_state:
    st.session_state.csv_ones = []

# No seedd process management needed with bbpy

# Ensure data directory exists
DATA_DIR = svc_utils.ensure_data_dir()

def main():
    # Header
    st.title("🎲 RngKit 3.0 - Streamlit Version")
    st.markdown("**by Thiago Jung** - thiagojm1984@hotmail.com")
    st.markdown("---")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📊 Data Collection & Analysis", "📈 Live Plot", "📖 Instructions"])
    
    with tab1:
        render_data_collection_tab()
    
    with tab2:
        render_live_plot_tab()
    
    with tab3:
        render_instructions_tab()

def render_data_collection_tab():
    st.header("📊 Data Collection & Analysis")
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🔧 Acquiring Data")
        
        # RNG Device Selection
        rng_type = st.radio(
            "Choose RNG Device:",
            ["BitBabbler", "TrueRNG", "TrueRNG + BitBabbler", "PseudoRNG"],
            index=0
        )
        
        # Device-specific options
        if rng_type in ["BitBabbler", "TrueRNG + BitBabbler"]:
            xor_mode = st.selectbox(
                "RAW(0)/XOR (1,2,3,4):",
                options=[0, 1, 2, 3, 4],
                index=0,
                help="0 = RAW mode, 1-4 = XOR with different fold counts"
            )
        else:
            xor_mode = 0
        
        # Sample parameters
        sample_size = st.number_input(
            "Sample Size (bits):",
            min_value=8,
            value=2048,
            step=8,
            help="Must be divisible by 8"
        )
        
        sample_interval = st.number_input(
            "Sample Interval (seconds):",
            min_value=1,
            value=1,
            step=1
        )
        
        # Collection controls
        col_start, col_status = st.columns([1, 1])
        
        with col_start:
            if not st.session_state.collecting:
                if st.button("▶️ Start Collection", type="primary", use_container_width=True):
                    start_data_collection(rng_type, xor_mode, sample_size, sample_interval)
            else:
                if st.button("⏹️ Stop Collection", type="secondary", use_container_width=True):
                    stop_data_collection()
        
        with col_status:
            # Auto-updating collection status
            # Only run fragment when collecting
            run_every = 1 if st.session_state.collecting else None
            
            @st.fragment(run_every=run_every)
            def update_collection_status():
                if st.session_state.collecting:
                    # Generate new data
                    collect_data_sample()
                    
                    st.success("🟢 Collecting")
                    # Show collection statistics
                    if st.session_state.collected_data:
                        data_count = len(st.session_state.collected_data)
                        latest_data = st.session_state.collected_data[-1]
                        st.metric("Samples", data_count)
                        st.metric("Latest Ones", latest_data['ones'])
                else:
                    st.info("🟡 Idle")
            
            update_collection_status()
    
    with col2:
        st.subheader("📈 Data Analysis")
        
        # File selection for analysis
        st.info("💡 **Tip**: Navigate to the data folder to find your generated files")
        uploaded_file = st.file_uploader(
            "Select file for analysis:",
            type=['csv', 'bin'],
            help="Select a previously generated .csv or .bin file from the data folder"
        )
        
        if uploaded_file:
            st.info(f"Selected: {uploaded_file.name}")
            
            # Analysis parameters (auto-detected from filename)
            analysis_col1, analysis_col2 = st.columns(2)
            
            # Try to detect defaults from filename convention
            detected_sample = 2048
            detected_interval = 1
            try:
                detected_sample = fn_service.parse_bits(uploaded_file.name)
                detected_interval = fn_service.parse_interval(uploaded_file.name)
            except Exception:
                pass

            # Update session defaults when file changes
            if st.session_state.get('_last_uploaded_for_analysis') != uploaded_file.name:
                st.session_state['an_sample_size'] = detected_sample
                st.session_state['an_sample_interval'] = detected_interval
                st.session_state['_last_uploaded_for_analysis'] = uploaded_file.name
            
            with analysis_col1:
                an_sample_size = st.number_input(
                    "Sample Size (bits):",
                    min_value=8,
                    value=st.session_state.get('an_sample_size', detected_sample),
                    step=8,
                    key="an_sample_size"
                )
            
            with analysis_col2:
                an_sample_interval = st.number_input(
                    "Sample Interval (seconds):",
                    min_value=1,
                    value=st.session_state.get('an_sample_interval', detected_interval),
                    step=1,
                    key="an_sample_interval"
                )
            
            # Analysis buttons
            analysis_btn_col1, analysis_btn_col2 = st.columns(2)
            
            with analysis_btn_col1:
                if st.button("📊 Generate Analysis", use_container_width=True):
                    if svc_utils.is_valid_params(an_sample_size, an_sample_interval):
                        # Save uploaded file to data folder
                        file_path = os.path.join(DATA_DIR, uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        try:
                            # Build dataframe depending on extension
                            if file_path.endswith('.bin'):
                                df = storage_service.read_bin_counts(file_path, an_sample_size)
                            else:
                                df = storage_service.read_csv_counts(file_path)
                            df = storage_service.add_zscore(df, an_sample_size)
                            storage_service.write_excel_with_chart(df, file_path, an_sample_size, an_sample_interval)
                            st.success("✅ Analysis completed! Check the output folder.")
                        except Exception as e:
                            st.error(f"❌ Analysis failed: {str(e)}")
                    else:
                        st.error("❌ Invalid parameters. Sample size must be divisible by 8.")
            
            with analysis_btn_col2:
                if st.button("📁 Open Output Folder", use_container_width=True):
                    os.startfile(DATA_DIR)
        
        # File concatenation section
        st.subheader("🔗 Concatenate Multiple CSV Files")
        st.info("💡 **Tip**: Navigate to the data folder to find your CSV files")
        
        concat_files = st.file_uploader(
            "Select multiple CSV files to concatenate:",
            type=['csv'],
            accept_multiple_files=True,
            help="Select multiple CSV files with the same sample size and interval from the data folder"
        )
        
        if concat_files:
            concat_col1, concat_col2 = st.columns(2)
            
            with concat_col1:
                concat_sample_size = st.number_input(
                    "Sample Size (bits):",
                    min_value=8,
                    value=2048,
                    step=8,
                    key="concat_sample_size"
                )
            
            with concat_col2:
                concat_sample_interval = st.number_input(
                    "Sample Interval (seconds):",
                    min_value=1,
                    value=1,
                    step=1,
                    key="concat_sample_interval"
                )
            
            if st.button("🔗 Concatenate Files", use_container_width=True):
                if len(concat_files) > 1:
                    # Save uploaded files to data folder
                    file_paths = []
                    for file in concat_files:
                        file_path = os.path.join(DATA_DIR, file.name)
                        with open(file_path, "wb") as f:
                            f.write(file.getbuffer())
                        file_paths.append(file_path)
                    
                    try:
                        # Create output stem with timestamp and parameters
                        out_stem = time.strftime(f"%Y%m%dT%H%M%S_concat_s{concat_sample_size}_i{concat_sample_interval}")
                        out_path = storage_service.concat_csv_files([*file_paths], out_stem)
                        st.success(f"✅ Files concatenated successfully! Saved: {out_path}")
                    except Exception as e:
                        st.error(f"❌ Concatenation failed: {str(e)}")
                else:
                    st.warning("⚠️ Please select at least 2 files to concatenate.")

def render_live_plot_tab():
    st.header("📈 Live Plot")
    
    # Create two columns
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("⚙️ Options")
        
        # RNG Device Selection for live plot
        live_rng_type = st.radio(
            "Choose RNG Device:",
            ["BitBabbler", "TrueRNG3", "PseudoRNG"],
            index=0,
            key="live_rng"
        )
        
        # Device-specific options
        if live_rng_type == "BitBabbler":
            live_xor_mode = st.selectbox(
                "RAW(0)/XOR (1,2,3,4):",
                options=[0, 1, 2, 3, 4],
                index=0,
                key="live_xor"
            )
        else:
            live_xor_mode = 0
        
        # Live plot parameters
        live_sample_size = st.number_input(
            "Sample Size (bits):",
            min_value=8,
            value=2048,
            step=8,
            key="live_sample_size"
        )
        
        live_sample_interval = st.number_input(
            "Sample Interval (seconds):",
            min_value=1,
            value=1,
            step=1,
            key="live_sample_interval"
        )
        
        # Live plot controls
        if not st.session_state.live_plotting:
            if st.button("▶️ Start Live Plot", type="primary", use_container_width=True):
                start_live_plotting(live_rng_type, live_xor_mode, live_sample_size, live_sample_interval)
        else:
            if st.button("⏹️ Stop Live Plot", type="secondary", use_container_width=True):
                stop_live_plotting()
        
        # Status
        if st.session_state.live_plotting:
            st.success("🟢 Live Plotting Active")
        else:
            st.info("🟡 Live Plot Idle")
    
    with col2:
        st.subheader("📊 Live Z-Score Chart")
        

        
        # Auto-updating live chart
        # Only run fragment when live plotting
        run_every = 1 if st.session_state.live_plotting else None
        
        @st.fragment(run_every=run_every)
        def update_live_chart():
            if st.session_state.live_plotting:
                # Generate new data
                collect_live_plot_sample()
            
            if st.session_state.zscore_data and st.session_state.index_data:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=st.session_state.index_data,
                    y=st.session_state.zscore_data,
                    mode='lines',
                    name='Z-Score',
                    line=dict(color='orange', width=2)
                ))
                
                fig.update_layout(
                    title="Live Z-Score Plot",
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
                st.info("📊 Chart will appear here when live plotting starts")
        
        update_live_chart()

def render_instructions_tab():
    st.header("📖 Instructions")
    
    # Read and display README content
    try:
        with open("README.md", "r", encoding="utf8") as f:
            instruction_text = f.read()
        
        # Convert markdown to display properly
        st.markdown(instruction_text)
    except FileNotFoundError:
        st.error("README.md file not found. Please ensure it exists in the project directory.")

def collect_data_sample():
    """Collect a single data sample based on current settings"""
    if not st.session_state.collecting or not st.session_state.current_values:
        return
    
    current_time = datetime.now()
    time_since_last = (current_time - st.session_state.last_update_time).total_seconds()
    
    # Only collect if enough time has passed
    if time_since_last >= st.session_state.sample_interval:
        values = st.session_state.current_values
        file_name = st.session_state.file_name
        
        try:
            if values["bit_ac"]:
                collect_bitbabbler_sample(values, file_name)
            elif values['true3_ac']:
                collect_trng3_sample(values, file_name)
            elif values['pseudo_rng_ac']:
                collect_pseudo_sample(values, file_name)
            
            st.session_state.last_update_time = current_time
        except Exception as e:
            print(f"Data collection error: {e}")
            st.session_state.collecting = False

def collect_bitbabbler_sample(values, file_name):
    """Collect a single BitBabbler sample"""
    sample_value = int(values["ac_bit_count"])
    sample_bytes = int(sample_value / 8)
    folds = int(values.get("ac_combo", 0))
    
    try:
        with open(file_name + '.bin', "ab+") as bin_file:
            chunk = dev_bitb.read_bytes(sample_bytes, folds)
            if chunk:
                bin_file.write(chunk)
            else:
                print("No data received from BitBabbler (bbpy)")
                return
        
        bin_hex = BitArray(chunk)
        bin_ascii = bin_hex.bin
        
        if not bin_ascii:
            print("Empty data from BitBabbler (bbpy)")
            return
        
        num_ones_array = bin_ascii.count('1')
        storage_service.write_csv_count(num_ones_array, file_name)
        
        # Update session state
        st.session_state.collected_data.append({
            'timestamp': time.time(),
            'ones': num_ones_array,
            'sample_size': sample_value
        })
        
    except Exception as e:
        print(f"BitBabbler collection error (bbpy): {e}")
        st.session_state.collecting = False

def collect_trng3_sample(values, file_name):
    """Collect a single TrueRNG3 sample"""
    sample_value = int(values["ac_bit_count"])
    blocksize = int(sample_value / 8)
    
    ports_available = list(list_ports.comports())
    rng_com_port = None
    for temp in ports_available:
        if temp[1].startswith("TrueRNG"):
            if rng_com_port is None:
                rng_com_port = str(temp[0])
    
    try:
        with open(file_name + '.bin', "ab") as bin_file:
            ser = serial.Serial(port=rng_com_port, timeout=10)
            if not ser.isOpen():
                ser.open()
            ser.setDTR(True)
            ser.flushInput()
            
            x = ser.read(blocksize)
            bin_file.write(x)
            ser.close()
        
        bin_hex = BitArray(x)
        bin_ascii = bin_hex.bin
        num_ones_array = bin_ascii.count('1')
        storage_service.write_csv_count(num_ones_array, file_name)
        
        # Update session state
        st.session_state.collected_data.append({
            'timestamp': time.time(),
            'ones': num_ones_array,
            'sample_size': sample_value
        })
        
    except Exception as e:
        print(f"TrueRNG3 collection error: {e}")
        st.session_state.collecting = False

def collect_pseudo_sample(values, file_name):
    """Collect a single Pseudo RNG sample"""
    sample_value = int(values["ac_bit_count"])
    blocksize = int(sample_value / 8)
    
    try:
        with open(file_name + '.bin', "ab") as bin_file:
            x = dev_pseudo.read_bytes(blocksize)
            bin_file.write(x)
        
        bin_hex = BitArray(x)
        bin_ascii = bin_hex.bin
        num_ones_array = bin_ascii.count('1')
        storage_service.write_csv_count(num_ones_array, file_name)
        
        # Update session state
        st.session_state.collected_data.append({
            'timestamp': time.time(),
            'ones': num_ones_array,
            'sample_size': sample_value
        })
        
    except Exception as e:
        print(f"Pseudo RNG collection error: {e}")
        st.session_state.collecting = False

def start_data_collection(rng_type, xor_mode, sample_size, sample_interval):
    """Start data collection process"""
    # Validate parameters
    if not svc_utils.is_valid_params(sample_size, sample_interval):
        st.error("❌ Invalid parameters. Sample size must be divisible by 8.")
        return
    
    # Create values dict for compatibility with existing functions
    values = {
        "bit_ac": rng_type == "BitBabbler",
        "true3_ac": rng_type == "TrueRNG",
        "true3_bit_ac": rng_type == "TrueRNG + BitBabbler",
        "pseudo_rng_ac": rng_type == "PseudoRNG",
        "ac_combo": xor_mode,
        "ac_bit_count": sample_size,
        "ac_time_count": sample_interval
    }
    
    # Device detection via adapters
    ok = True
    if values["bit_ac"] and not dev_bitb.detect():
        ok = False
    elif values["true3_ac"] and not dev_trng.detect():
        ok = False
    elif values["true3_bit_ac"] and not (dev_bitb.detect() and dev_trng.detect()):
        ok = False
    if not ok:
        if rng_type == "BitBabbler":
            st.error("❌ BitBabbler device check failed!")
            st.error("**Troubleshooting steps:**")
            st.error("1. Ensure BitBabbler is connected to USB")
            st.error("2. Install Visual C++ Redistributable (vcredist_x64.exe)")
            st.error("3. Install BitBabbler driver using Zadig (zadig-2.8.exe)")
            st.error("4. Try running `python test_bitbabbler.py` to diagnose")
        else:
            st.error("❌ Device check failed. Please ensure your device is connected.")
        return
    
    # Generate filename using service
    device_suffix = "bitb" if (values["bit_ac"] or values["true3_bit_ac"]) else "trng" if values["true3_ac"] else "pseudo"
    file_name = fn_service.format_capture_name(device_suffix, sample_size, sample_interval, xor_mode if device_suffix == "bitb" else None)
    file_name = os.path.join(DATA_DIR, file_name)
    
    # Start collection
    st.session_state.collecting = True
    st.session_state.current_values = values
    st.session_state.file_name = file_name
    st.session_state.collected_data = []
    st.session_state.sample_size = sample_size
    st.session_state.sample_interval = sample_interval
    st.session_state.last_update_time = datetime.now()
    
    # No seedd needed when using bbpy
    
    st.success("✅ Data collection started!")
    st.rerun()

def stop_data_collection():
    """Stop data collection process"""
    st.session_state.collecting = False
    # Nothing to kill for bbpy
    st.success("⏹️ Data collection stopped!")
    # Force rerun to update fragments
    st.rerun()

def collect_live_plot_sample():
    """Collect a single live plot sample based on current settings"""
    if not st.session_state.live_plotting or not st.session_state.current_values:
        return
    
    current_time = datetime.now()
    time_since_last = (current_time - st.session_state.last_update_time).total_seconds()
    
    # Only collect if enough time has passed
    if time_since_last >= st.session_state.sample_interval:
        values = st.session_state.current_values
        file_name = st.session_state.file_name
        
        try:
            if values['bit_live']:
                collect_live_bitbabbler_sample(values, file_name)
            elif values['true3_live']:
                collect_live_trng3_sample(values, file_name)
            elif values['pseudo_rng_live']:
                collect_live_pseudo_sample(values, file_name)
            
            st.session_state.last_update_time = current_time
        except Exception as e:
            print(f"Live plotting error: {e}")
            st.session_state.live_plotting = False

def collect_live_bitbabbler_sample(values, file_name):
    """Collect a single live BitBabbler sample"""
    sample_value = int(values["live_bit_count"])
    sample_bytes = int(sample_value / 8)
    folds = int(values.get("live_combo", 0))
    
    try:
        with open(file_name + '.bin', "ab+") as bin_file:
            chunk = dev_bitb.read_bytes(sample_bytes, folds)
            if chunk:
                bin_file.write(chunk)
            else:
                print("No data received from BitBabbler (bbpy)")
                return
        
        bin_hex = BitArray(chunk)
        bin_ascii = bin_hex.bin
        
        if not bin_ascii:
            print("Empty data from BitBabbler (bbpy)")
            return
        
        num_ones_array = bin_ascii.count('1')
        st.session_state.csv_ones.append(num_ones_array)
        storage_service.write_csv_count(num_ones_array, file_name)
        
        # Calculate Z-score
        index_number = len(st.session_state.csv_ones)
        sums_csv = sum(st.session_state.csv_ones)
        avrg_csv = sums_csv / index_number
        zscore_csv = (avrg_csv - (sample_value / 2)) / (((sample_value / 4) ** 0.5) / (index_number ** 0.5))
        
        # Update session state
        st.session_state.zscore_data.append(zscore_csv)
        st.session_state.index_data.append(index_number)
        
    except Exception as e:
        print(f"Live BitBabbler error (bbpy): {e}")
        st.session_state.live_plotting = False

def collect_live_trng3_sample(values, file_name):
    """Collect a single live TrueRNG3 sample"""
    sample_value = int(values["live_bit_count"])
    blocksize = int(sample_value / 8)
    
    try:
        with open(file_name + '.bin', "ab+") as bin_file:
            chunk = dev_trng.read_bytes(blocksize)
            bin_file.write(chunk)
        
        bin_hex = BitArray(chunk)
        bin_ascii = bin_hex.bin
        num_ones_array = int(bin_ascii.count('1'))
        st.session_state.csv_ones.append(num_ones_array)
        storage_service.write_csv_count(num_ones_array, file_name)
        
        # Calculate Z-score
        index_number = len(st.session_state.csv_ones)
        sums_csv = sum(st.session_state.csv_ones)
        avrg_csv = sums_csv / index_number
        zscore_csv = (avrg_csv - (sample_value / 2)) / (((sample_value / 4) ** 0.5) / (index_number ** 0.5))
        
        # Update session state
        st.session_state.zscore_data.append(zscore_csv)
        st.session_state.index_data.append(index_number)
        
    except Exception as e:
        print(f"Live TrueRNG3 error: {e}")
        st.session_state.live_plotting = False

def collect_live_pseudo_sample(values, file_name):
    """Collect a single live Pseudo RNG sample"""
    sample_value = int(values["live_bit_count"])
    blocksize = int(sample_value / 8)
    
    try:
        with open(file_name + '.bin', "ab+") as bin_file:
            chunk = secrets.token_bytes(blocksize)
            bin_file.write(chunk)
        
        bin_hex = BitArray(chunk)
        bin_ascii = bin_hex.bin
        num_ones_array = int(bin_ascii.count('1'))
        st.session_state.csv_ones.append(num_ones_array)
        storage_service.write_csv_count(num_ones_array, file_name)
        
        # Calculate Z-score
        index_number = len(st.session_state.csv_ones)
        sums_csv = sum(st.session_state.csv_ones)
        avrg_csv = sums_csv / index_number
        zscore_csv = (avrg_csv - (sample_value / 2)) / (((sample_value / 4) ** 0.5) / (index_number ** 0.5))
        
        # Update session state
        st.session_state.zscore_data.append(zscore_csv)
        st.session_state.index_data.append(index_number)
        
    except Exception as e:
        print(f"Live Pseudo RNG error: {e}")
        st.session_state.live_plotting = False

def start_live_plotting(rng_type, xor_mode, sample_size, sample_interval):
    """Start live plotting process"""
    # Validate parameters
    if not svc_utils.is_valid_params(sample_size, sample_interval):
        st.error("❌ Invalid parameters. Sample size must be divisible by 8.")
        return
    
    # Create values dict for compatibility
    values = {
        "bit_live": rng_type == "BitBabbler",
        "true3_live": rng_type == "TrueRNG3",
        "pseudo_rng_live": rng_type == "PseudoRNG",
        "live_combo": xor_mode,
        "live_bit_count": sample_size,
        "live_time_count": sample_interval
    }
    
    # Check USB capabilities
    # Device detection via adapters
    ok_live = True
    if values["bit_live"] and not dev_bitb.detect():
        ok_live = False
    elif values["true3_live"] and not dev_trng.detect():
        ok_live = False
    if not ok_live:
        if rng_type == "BitBabbler":
            st.error("❌ BitBabbler device check failed!")
            st.error("**Troubleshooting steps:**")
            st.error("1. Ensure BitBabbler is connected to USB")
            st.error("2. Install Visual C++ Redistributable (vcredist_x64.exe)")
            st.error("3. Install BitBabbler driver using Zadig (zadig-2.8.exe)")
            st.error("4. Try running `python test_bitbabbler.py` to diagnose")
        else:
            st.error("❌ Device check failed. Please ensure your device is connected.")
        return
    
    # Generate filename using service
    device_suffix = "bitb" if values["bit_live"] else "trng" if values["true3_live"] else "pseudo"
    file_name = fn_service.format_capture_name(device_suffix, sample_size, sample_interval, xor_mode if device_suffix == "bitb" else None)
    file_name = os.path.join(DATA_DIR, file_name)
    
    # Start live plotting
    st.session_state.live_plotting = True
    st.session_state.current_values = values
    st.session_state.file_name = file_name
    st.session_state.zscore_data = []
    st.session_state.index_data = []
    st.session_state.csv_ones = []
    st.session_state.sample_size = sample_size
    st.session_state.sample_interval = sample_interval
    st.session_state.last_update_time = datetime.now()
    
    # No seedd needed when using bbpy
    
    st.success("✅ Live plotting started!")
    st.rerun()

def stop_live_plotting():
    """Stop live plotting process"""
    st.session_state.live_plotting = False
    # Nothing to kill for bbpy
    st.success("⏹️ Live plotting stopped!")
    # Force rerun to update fragments
    st.rerun()

if __name__ == "__main__":
    main()
