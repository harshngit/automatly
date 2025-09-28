# fixed_streamlit_app.py - Prevents infinite initialization loop
import streamlit as st
import pandas as pd
import asyncio
import json
from datetime import datetime
import time

# Prevent auto-rerun issues
st.set_page_config(
    page_title="Fixed Option Trading System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import system
try:
    from main import OptimizedOptionTradingSystem as OptionTradingSystem
except ImportError:
    st.error("Cannot import optimized_main.py - please ensure it exists!")
    st.stop()

# CRITICAL: Initialize session state properly to prevent loops
if 'system_initialized' not in st.session_state:
    st.session_state.system_initialized = False
if 'system_obj' not in st.session_state:
    st.session_state.system_obj = None
if 'dropdown_options' not in st.session_state:
    st.session_state.dropdown_options = {
        'symbols': ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"],
        'option_expiry': ["30Nov2023", "07Dec2023", "14Dec2023", "21Dec2023"],
        'future_expiry': ["30Nov2023", "07Dec2023", "14Dec2023", "21Dec2023"]
    }
if 'option_data' not in st.session_state:
    st.session_state.option_data = None
if 'init_time' not in st.session_state:
    st.session_state.init_time = None
if 'fetch_time' not in st.session_state:
    st.session_state.fetch_time = None

# Header
st.title("🔧 Fixed Option Trading System")
st.markdown("**No more infinite loops - Single initialization only**")

# Sidebar
with st.sidebar:
    st.header("System Control")
    
    # Status display
    if st.session_state.system_initialized:
        st.success("✅ System Ready")
        if st.session_state.init_time:
            st.info(f"⏱️ Initialized in {st.session_state.init_time:.2f}s")
    else:
        st.warning("⏳ System Not Initialized")
    
    # Initialize button - ONLY show if not initialized
    if not st.session_state.system_initialized:
        if st.button("🚀 Initialize System", type="primary", key="init_btn"):
            with st.spinner("Initializing system (one time only)..."):
                try:
                    start_time = time.time()
                    
                    # Create system object
                    if st.session_state.system_obj is None:
                        st.session_state.system_obj = OptionTradingSystem()
                    
                    # Initialize
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    success = loop.run_until_complete(
                        st.session_state.system_obj.initialize_system_fast()
                    )
                    loop.close()
                    
                    if success:
                        # Get dropdown options
                        options = st.session_state.system_obj.get_dropdown_options()
                        st.session_state.dropdown_options = options
                        
                        # Mark as initialized
                        st.session_state.system_initialized = True
                        st.session_state.init_time = time.time() - start_time
                        
                        st.success(f"System initialized in {st.session_state.init_time:.2f} seconds!")
                        st.rerun()
                    else:
                        st.error("Initialization failed!")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Reset button - ONLY show if initialized
    if st.session_state.system_initialized:
        if st.button("🔄 Reset System", type="secondary", key="reset_btn"):
            # Clean reset
            if st.session_state.system_obj:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(st.session_state.system_obj.cleanup())
                    loop.close()
                except:
                    pass
            
            # Reset all session state
            st.session_state.system_initialized = False
            st.session_state.system_obj = None
            st.session_state.option_data = None
            st.session_state.init_time = None
            st.session_state.fetch_time = None
            
            st.success("System reset! Click Initialize to start again.")
            st.rerun()

# Main content
col1, col2 = st.columns([1, 2])

with col1:
    st.header("📊 Trading Controls")
    
    if st.session_state.system_initialized:
        # Show dropdown info
        options = st.session_state.dropdown_options
        st.info(f"Available options:\n- Symbols: {len(options['symbols'])}\n- Expiries: {len(options['option_expiry'])}")
        
        # Trading form
        with st.form("trading_form", clear_on_submit=False):
            symbol = st.selectbox(
                "Symbol",
                options=options['symbols'],
                key="symbol_select"
            )
            
            option_expiry = st.selectbox(
                "Option Expiry",
                options=options['option_expiry'],
                key="opt_expiry_select"
            )
            
            future_expiry = st.selectbox(
                "Future Expiry", 
                options=options['future_expiry'],
                key="fut_expiry_select"
            )
            
            chain_length = st.slider(
                "Chain Length",
                min_value=5,
                max_value=50,
                value=20,
                step=5,
                key="chain_slider"
            )
            
            # Submit button
            submitted = st.form_submit_button("📈 Fetch Data", type="primary")
            
            if submitted:
                with st.spinner("Fetching option data..."):
                    try:
                        start_time = time.time()
                        
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        data = loop.run_until_complete(
                            st.session_state.system_obj.fetch_option_data_fast(
                                symbol=symbol,
                                option_expiry=option_expiry,
                                future_expiry=future_expiry,
                                chain_length=chain_length
                            )
                        )
                        loop.close()
                        
                        st.session_state.fetch_time = time.time() - start_time
                        
                        if data and data.get('option_chain'):
                            st.session_state.option_data = data
                            st.success(f"Data fetched in {st.session_state.fetch_time:.2f}s!")
                            # Don't rerun here to prevent loops
                        else:
                            st.error("No data received!")
                            
                    except Exception as e:
                        st.error(f"Fetch failed: {str(e)}")
        
        # Quick buttons
        st.subheader("⚡ Quick Actions")
        
        if st.button("🔥 Quick NIFTY", key="quick_nifty"):
            with st.spinner("Fetching NIFTY..."):
                try:
                    start_time = time.time()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    data = loop.run_until_complete(
                        st.session_state.system_obj.fetch_option_data_fast(
                            symbol="NIFTY",
                            option_expiry=options['option_expiry'][0],
                            future_expiry=options['future_expiry'][0],
                            chain_length=20
                        )
                    )
                    loop.close()
                    
                    st.session_state.fetch_time = time.time() - start_time
                    st.session_state.option_data = data
                    st.success(f"NIFTY fetched in {st.session_state.fetch_time:.2f}s!")
                except Exception as e:
                    st.error(f"Quick fetch failed: {str(e)}")
    
    else:
        st.warning("Please initialize the system first!")

with col2:
    st.header("📈 Option Data")
    
    if st.session_state.option_data:
        data = st.session_state.option_data
        
        # Summary
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Symbol", data.get('symbol', 'N/A'))
        with col_b:
            price = data.get('underlying_price', 0)
            st.metric("Spot Price", f"₹{price:,.0f}" if price else "N/A")
        with col_c:
            count = len(data.get('option_chain', []))
            st.metric("Strikes", count)
        
        # Performance metrics
        if st.session_state.fetch_time:
            st.info(f"⚡ Last fetch: {st.session_state.fetch_time:.2f} seconds")
        
        # Option chain table
        if data.get('option_chain'):
            st.subheader("Option Chain Data")
            
            df = pd.DataFrame(data['option_chain'])
            
            # Format display
            display_df = pd.DataFrame({
                'CALL LTP': df['call_ltp'].apply(lambda x: f"₹{x:,.2f}"),
                'CALL VOL': df['call_volume'].apply(lambda x: f"{x:,}"),
                'CALL OI': df['call_oi'].apply(lambda x: f"{x:,}"),
                'STRIKE': df['strike'].apply(lambda x: f"₹{x:,.0f}"),
                'PUT LTP': df['put_ltp'].apply(lambda x: f"₹{x:,.2f}"),
                'PUT VOL': df['put_volume'].apply(lambda x: f"{x:,}"),
                'PUT OI': df['put_oi'].apply(lambda x: f"{x:,}")
            })
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Export options
        st.subheader("📤 Export")
        
        export_col1, export_col2 = st.columns(2)
        with export_col1:
            json_str = json.dumps(data, indent=2, default=str)
            st.download_button(
                "📄 Download JSON",
                data=json_str,
                file_name=f"option_data_{data.get('symbol')}_{datetime.now().strftime('%H%M%S')}.json",
                mime="application/json"
            )
        
        with export_col2:
            if data.get('option_chain'):
                csv_data = pd.DataFrame(data['option_chain']).to_csv(index=False)
                st.download_button(
                    "📊 Download CSV",
                    data=csv_data,
                    file_name=f"option_chain_{data.get('symbol')}_{datetime.now().strftime('%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        # Raw data
        with st.expander("🔍 Raw JSON Data"):
            st.json(data)
    
    else:
        st.info("No data available. Please fetch data first.")

# Footer
st.markdown("---")
st.markdown("### 📊 System Information")

info_col1, info_col2, info_col3 = st.columns(3)

with info_col1:
    status = "🟢 READY" if st.session_state.system_initialized else "🔴 NOT READY"
    st.info(f"**Status:** {status}")

with info_col2:
    init_time = st.session_state.init_time or 0
    st.info(f"**Init Time:** {init_time:.2f}s")

with info_col3:
    current_time = datetime.now().strftime("%H:%M:%S")
    st.info(f"**Time:** {current_time}")

# Debug info
with st.expander("🐛 Debug Information"):
    st.write("Session State Keys:", list(st.session_state.keys()))
    st.write("System Initialized:", st.session_state.system_initialized)
    st.write("System Object:", type(st.session_state.system_obj))
    st.write("Has Option Data:", bool(st.session_state.option_data))