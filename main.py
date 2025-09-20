import streamlit as st
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from io import StringIO
import os

# Page configuration
st.set_page_config(
    page_title="Project Chandana Dashboard",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Anthropic-inspired theme
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4F46E5;
        color: white;
    }
    h1, h2, h3 {
        color: #1f2937;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# Configuration
@st.cache_data
def load_config():
    # For Streamlit Cloud deployment - use Google Sheets URLs
    return {
        'hpos_data_url': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTVZqlJ7YBLKbPSWwYTA5tAr401wUIBpp7ALPvEOKch91uxdvTevpvWs1FuQ1hQKB84RsZyAFsJYRRr/pub?gid=1058968279&single=true&output=csv',
        'hplc_data_path': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTAHLMLCH4GO0WGXgUXO7hz3Lvc66MIgMffh3JnqcO3QSGX2Pk_YmbCRuD2welz7-aDhINSixl9g-nN/pub?gid=43184154&single=true&output=csv',  # Replace with your actual HPLC Google Sheets URL
        'hpos_threshold_low': 0.38,
        'hpos_threshold_high': 0.42,
        'target_hplc_tests': 1000,
        'theme': {
            'primary_color': '#4F46E5',
            'background_color': '#ffffff',
            'secondary_color': '#667eea',
            'text_color': '#1f2937'
        }
    }

def create_sample_hplc_data():
    """Create sample HPLC data for demo when file is not available"""
    np.random.seed(42)
    n_samples = 2725
    
    sample_data = {
        'SL No.': range(1, n_samples + 1),
        'Sickle Id': [f'SK{i:04d}' for i in range(1, n_samples + 1)],
        'Age': [f'{np.random.randint(1, 80)} yrs' for _ in range(n_samples)],
        'Gender': np.random.choice(['M', 'F', 'Male', 'Female'], n_samples),
        'District': np.random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad', 'Pune'], n_samples),
        'Pathology stated HPLC RESULT': np.random.choice(['Normal', 'Sickle Cell Trait', 'Sickle Cell Disease', None], n_samples, p=[0.6, 0.2, 0.15, 0.05]),
        'Lab_HPOS_Test': np.random.choice(['Done', 'Pending', 'Not Required'], n_samples, p=[0.7, 0.2, 0.1])
    }
    
    return pd.DataFrame(sample_data)

@st.cache_data(ttl=3600)
def load_data(hpos_url, hplc_source):
    """Load HPOS data from Google Sheets and HPLC data from file or create sample data"""
    hpos_data = None
    hplc_data = None
    
    # Load HPOS data from Google Sheets
    try:
        hpos_response = requests.get(hpos_url, timeout=30)
        hpos_response.raise_for_status()
        
        # Try different CSV parsing options
        try:
            hpos_data = pd.read_csv(StringIO(hpos_response.text))
        except pd.errors.ParserError:
            # Try with different separator or quoting
            hpos_data = pd.read_csv(StringIO(hpos_response.text), sep=',', quotechar='"', skipinitialspace=True)
        
        hpos_data = hpos_data.dropna(how="all")
        st.success("✅ Loaded HPOS data from Google Sheets")
        
    except Exception as e:
        st.error(f"Error loading HPOS data: {str(e)}")
        st.info("Will continue with HPLC data analysis only")
    
    # Load HPLC data
    try:
        if hplc_source and hplc_source.startswith('http'):
            # Load from Google Sheets URL
            hplc_response = requests.get(hplc_source, timeout=30)
            hplc_response.raise_for_status()
            
            # Try multiple parsing strategies for problematic CSV
            csv_content = hplc_response.text
            
            # Strategy 1: Standard parsing
            try:
                hplc_data = pd.read_csv(StringIO(csv_content))
            except pd.errors.ParserError as pe:
                st.warning(f"CSV parsing issue: {str(pe)}")
                
                # Strategy 2: Try with error handling
                try:
                    hplc_data = pd.read_csv(StringIO(csv_content), error_bad_lines=False, warn_bad_lines=True)
                    st.info("⚠️ Some problematic lines were skipped during CSV parsing")
                except:
                    # Strategy 3: Try with different parameters
                    try:
                        hplc_data = pd.read_csv(StringIO(csv_content), sep=',', quotechar='"', skipinitialspace=True, on_bad_lines='skip')
                        st.info("⚠️ Used flexible CSV parsing - some data may have been adjusted")
                    except Exception as e3:
                        st.error(f"All CSV parsing strategies failed: {str(e3)}")
                        # Create sample data as fallback
                        hplc_data = create_sample_hplc_data()
                        st.warning("🔄 Using sample HPLC data due to CSV parsing issues")
            
            if hplc_data is not None:
                hplc_data = hplc_data.dropna(how="all")
                st.success("✅ Loaded HPLC data from Google Sheets")
                
        elif hplc_source and os.path.exists(hplc_source):
            # Load from local file with error handling
            try:
                hplc_data = pd.read_csv(hplc_source)
            except pd.errors.ParserError:
                try:
                    hplc_data = pd.read_csv(hplc_source, error_bad_lines=False, warn_bad_lines=True)
                    st.info("⚠️ Some problematic lines were skipped during local CSV parsing")
                except:
                    hplc_data = pd.read_csv(hplc_source, sep=',', quotechar='"', skipinitialspace=True, on_bad_lines='skip')
                    st.info("⚠️ Used flexible local CSV parsing")
            
            hplc_data = hplc_data.dropna(how="all")
            st.success("✅ Loaded HPLC data from local file")
        else:
            # Create sample data for demonstration
            hplc_data = create_sample_hplc_data()
            st.warning("⚠️ Using sample HPLC data for demonstration")
            
    except Exception as e:
        st.error(f"Error loading HPLC data: {str(e)}")
        # Create sample data as fallback
        hplc_data = create_sample_hplc_data()
        st.warning("🔄 Using sample HPLC data due to loading error")
    
    return hpos_data, hplc_data

def process_age_data(df):
    """Process age data and create age groups"""
    # Remove 'yrs' using regex and convert to int
    df['age_in_years'] = df['Age'].str.replace(r'\s*[yY][rR][sS]\s*', '', regex=True)
    df['age_in_years'] = pd.to_numeric(df['age_in_years'], errors='coerce')
    df['age_in_years'] = df['age_in_years'].fillna(0).astype(int)
    
    # Create age bins in 5-year intervals
    min_age = df['age_in_years'].min()
    max_age = df['age_in_years'].max()
    bins = range(min_age // 5 * 5, (max_age // 5 + 2) * 5, 5)
    labels = [f"{i}-{i+4}" for i in bins[:-1]]
    
    df['age_group'] = pd.cut(df['age_in_years'], bins=bins, labels=labels, right=False)
    return df

def process_gender_data(df):
    """Process and standardize gender data"""
    df['Gender'] = df['Gender'].str.strip().str.upper()
    gender_map = {
        'M': 'Male',
        'F': 'Female',
        'MALE': 'Male',
        'FEMALE': 'Female',
        'NA': 'Unknown',
        '': 'Unknown',
        None: 'Unknown'
    }
    df['Gender_standardized'] = df['Gender'].map(gender_map).fillna('Unknown')
    return df

def get_weekly_delta(df, date_column=None):
    """Calculate weekly delta for metrics"""
    if date_column and date_column in df.columns:
        # If date column exists, filter for last week
        try:
            df[date_column] = pd.to_datetime(df[date_column])
            last_week = datetime.now() - timedelta(days=7)
            recent_tests = df[df[date_column] >= last_week].shape[0]
            return recent_tests
        except:
            pass
    # If no date column or error, return estimated weekly increase (10% of total)
    return int(df.shape[0] * 0.1)

def main():
    st.title("🧬 Project Chandana - HPLC and HPOS Tests Analysis")
    st.markdown("---")
    
    # Load configuration
    config = load_config()
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Dashboard Navigation")
        st.markdown("Welcome to Project Chandana Analytics")
        
        # Data debugging section
        if st.sidebar.button("🔍 Debug Data Issues"):
            st.subheader("🔍 Data Debugging Information")
            
            # Check HPLC data structure
            if hplc_data is not None:
                st.write("**HPLC Data Info:**")
                st.write(f"Shape: {hplc_data.shape}")
                st.write(f"Columns: {list(hplc_data.columns)}")
                st.write("First few rows:")
                st.dataframe(hplc_data.head(3))
                
                # Check for common issues
                if hplc_data.isnull().any().any():
                    st.warning("⚠️ HPLC data contains null values")
                
                # Check column consistency
                if len(hplc_data.columns) != len(set(hplc_data.columns)):
                    st.warning("⚠️ HPLC data has duplicate column names")
            
            # Check HPOS data structure  
            if hpos_data is not None:
                st.write("**HPOS Data Info:**")
                st.write(f"Shape: {hpos_data.shape}")
                st.write(f"Columns: {list(hpos_data.columns)}")
                st.write("First few rows:")
                st.dataframe(hpos_data.head(3))
        
        # Data refresh button
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    
    # Load data
    with st.spinner("Loading data..."):
        hpos_data, hplc_data = load_data(
            config['hpos_data_url'], 
            config['hplc_data_path']
        )
    
    if hplc_data is None:
        st.error("Critical error: Could not load any data.")
        return
    
    # Store in session state
    st.session_state['hpos_data'] = hpos_data
    st.session_state['hplc_data'] = hplc_data
    
    # Process HPLC data
    if 'SL No.' in hplc_data.columns:
        hplc_processed = hplc_data[['SL No.','Sickle Id','Age','Gender','District','Pathology stated HPLC RESULT','Lab_HPOS_Test']].copy()
    else:
        # Use all available columns if expected columns don't exist
        hplc_processed = hplc_data.copy()
    
    hplc_processed = process_age_data(hplc_processed)
    hplc_processed = process_gender_data(hplc_processed)
    
    # Main dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "👥 Demographics", "🏥 HPOS Analysis", "📊 Detailed Reports"])
    
    with tab1:
        st.header("📈 Project Overview")
        
        # Key Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_hplc = hplc_processed.shape[0]
            weekly_delta = get_weekly_delta(hplc_processed)
            st.metric(
                "Total HPLC Tests", 
                value=total_hplc,
                delta=f"+{weekly_delta} this week"
            )
        
        with col2:
            total_hpos = hpos_data.shape[0]
            st.metric("Total HPOS Tests", value=total_hpos)
        
        with col3:
            progress_pct = min((total_hplc / config['target_hplc_tests']) * 100, 100)
            st.metric("Progress %", value=f"{progress_pct:.1f}%")
        
        with col4:
            # Count signed HPLC tests (assuming non-null results indicate signed tests)
            if 'Pathology stated HPLC RESULT' in hplc_processed.columns:
                signed_tests = hplc_processed['Pathology stated HPLC RESULT'].notna().sum()
            else:
                signed_tests = total_hplc  # Fallback
            st.metric("Signed HPLC Tests", value=signed_tests)
        
        # Progress bar
        st.progress(progress_pct / 100)
        
        # Summary charts
        st.subheader("📊 Quick Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Age distribution
            age_counts = hplc_processed['age_group'].value_counts().sort_index()
            fig_age = px.bar(
                x=age_counts.index, 
                y=age_counts.values,
                title="Age Distribution",
                labels={'x': 'Age Group', 'y': 'Count'}
            )
            fig_age.update_layout(showlegend=False)
            st.plotly_chart(fig_age, use_container_width=True)
        
        with col2:
            # Gender distribution
            gender_counts = hplc_processed['Gender_standardized'].value_counts()
            fig_gender = px.pie(
                values=gender_counts.values,
                names=gender_counts.index,
                title="Gender Distribution"
            )
            st.plotly_chart(fig_gender, use_container_width=True)
    
    with tab2:
        st.header("👥 Demographics Analysis")
        
        # Age Analysis
        st.subheader("Age Distribution")
        age_counts = hplc_processed['age_group'].value_counts().sort_index()
        st.dataframe(age_counts.to_frame("Count"))
        
        fig_age_detailed = px.histogram(
            hplc_processed, 
            x='age_in_years',
            nbins=20,
            title="Detailed Age Distribution"
        )
        st.plotly_chart(fig_age_detailed, use_container_width=True)
        
        # District Analysis
        st.subheader("District-wise Test Distribution")
        if 'District' in hplc_processed.columns:
            hplc_processed['District'] = hplc_processed['District'].str.strip().str.title()
            hplc_processed['District'] = hplc_processed['District'].fillna('Unknown')
            
            district_counts = hplc_processed['District'].value_counts()
            
            # Create thinner box plot equivalent using bar chart
            fig_district = px.bar(
                x=district_counts.values,
                y=district_counts.index,
                orientation='h',
                title="Tests by District",
                labels={'x': 'Number of Tests', 'y': 'District'}
            )
            fig_district.update_layout(height=max(400, len(district_counts) * 25))
            st.plotly_chart(fig_district, use_container_width=True)
            
            st.dataframe(district_counts.to_frame("Number of Tests"))
    
    with tab3:
        st.header("🏥 HPOS Analysis")
        
        if hpos_data is not None and 'deviceRatio' in hpos_data.columns:
            # Convert deviceRatio to numeric, handling any non-numeric values
            hpos_data['deviceRatio_numeric'] = pd.to_numeric(hpos_data['deviceRatio'], errors='coerce')
            
            # Remove any NaN values for analysis
            valid_ratios = hpos_data['deviceRatio_numeric'].dropna()
            
            if len(valid_ratios) == 0:
                st.warning("No valid numeric device ratio data found")
            else:
                # HPOS scatter plot with control lines
                fig_hpos = go.Figure()
                
                # Add scatter plot
                fig_hpos.add_trace(go.Scatter(
                    x=list(range(len(valid_ratios))),
                    y=valid_ratios,
                    mode='markers',
                    name='Device Ratio',
                    marker=dict(color='blue', size=6)
                ))
                
                # Add threshold lines
                fig_hpos.add_hline(
                    y=config['hpos_threshold_low'], 
                    line_dash="dash", 
                    line_color="red",
                    annotation_text="Lower Threshold (0.38)"
                )
                fig_hpos.add_hline(
                    y=config['hpos_threshold_high'], 
                    line_dash="dash", 
                    line_color="orange",
                    annotation_text="Upper Threshold (0.42)"
                )
                
                fig_hpos.update_layout(
                    title="HPOS Absorbance Ratios with Control Lines",
                    xaxis_title="Sample Index",
                    yaxis_title="Absorbance Ratio",
                    yaxis=dict(range=[0.1, 0.9])
                )
                
                st.plotly_chart(fig_hpos, use_container_width=True)
                
                # HPOS Statistics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    below_threshold = (valid_ratios < config['hpos_threshold_low']).sum()
                    st.metric("Below Lower Threshold", below_threshold)
                
                with col2:
                    within_range = ((valid_ratios >= config['hpos_threshold_low']) & 
                                   (valid_ratios <= config['hpos_threshold_high'])).sum()
                    st.metric("Within Normal Range", within_range)
                
                with col3:
                    above_threshold = (valid_ratios > config['hpos_threshold_high']).sum()
                    st.metric("Above Upper Threshold", above_threshold)
                
                # Show data quality info
                total_samples = len(hpos_data)
                valid_samples = len(valid_ratios)
                invalid_samples = total_samples - valid_samples
                
                if invalid_samples > 0:
                    st.info(f"Data Quality: {valid_samples} valid samples out of {total_samples} total samples. {invalid_samples} samples had invalid ratio values.")
        elif hpos_data is None:
            st.warning("HPOS data could not be loaded from Google Sheets. Please check the connection.")
        else:
            st.warning("Device ratio data not found in HPOS dataset")
    
    with tab4:
        st.header("📊 Detailed Reports")
        
        # Data tables
        st.subheader("HPLC Data Sample")
        st.dataframe(hplc_processed.head(20), use_container_width=True)
        
        if hpos_data is not None:
            st.subheader("HPOS Data Sample")
            st.dataframe(hpos_data.head(20), use_container_width=True)
        else:
            st.info("HPOS data not available - check Google Sheets connection")
        
        # Download buttons
        col1, col2 = st.columns(2)
        
        with col1:
            csv_hplc = hplc_processed.to_csv(index=False)
            st.download_button(
                label="📥 Download HPLC Data",
                data=csv_hplc,
                file_name=f"hplc_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        with col2:
            if hpos_data is not None:
                csv_hpos = hpos_data.to_csv(index=False)
                st.download_button(
                    label="📥 Download HPOS Data",
                    data=csv_hpos,
                    file_name=f"hpos_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("HPOS data not available for download")

if __name__ == "__main__":
    main()
