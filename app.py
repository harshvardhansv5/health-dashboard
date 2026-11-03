import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta, datetime
import re
import io
import math
import requests
import unicodedata

# --- CONSTANTS ---
TOTAL_SPOKES = 701 
available_sheets = [] 

# --- GOOGLE SHEETS INTEGRATION ---
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRwjDNp1zjbEXM-a4HYoAErb4ZWyJm9YmbKyTeEOhKOpKx6DAFLUlVPlQEvRP0ll5SUDXYWKlS5F7Gc/pub?output=xlsx"

# --- DISTANCE FALLBACK DICTIONARY ---
DISTANCE_FALLBACK = {}

# --- PAGE SETUP ---
st.set_page_config(page_title="Bihar Health Dashboard", page_icon="🩸", layout="wide")

# --- CLINICAL PEARL UI CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    .material-symbols-rounded, [data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }
    
    /* --- THE SOFT SLATE CANVAS --- */
    .stApp { background-color: #F1F5F9 !important; } 
    
    /* Remove Sidebar entirely */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    /* --- HIDE UGLY DATAFRAME COLUMN MENUS (WITHOUT BREAKING SORTING) --- */
    [data-testid="stDataFrameColumnMenu"] { display: none !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] { cursor: pointer !important; }

    /* --- FORCE TEAL PROGRESS BARS --- */
    div[data-testid="stProgress"] > div > div > div { background-color: #06B6D4 !important; }

    /* --- AUTH BOX --- */
    .auth-box {
        background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
        padding: 24px 24px 16px 24px; max-width: 520px; margin: 60px auto 20px auto;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1), 0 4px 10px -3px rgba(0,0,0,0.05);
        text-align: center;
    }

    /* Metric Cards (Floating Glass) */
    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 12px; }
    .metric-card {
        background-color: #FFFFFF !important; border: 1px solid #E2E8F0 !important; border-radius: 12px !important;
        padding: 16px !important; box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.05) !important; 
        display: flex; flex-direction: column; transition: transform 0.2s ease; border-top: 4px solid #06B6D4;
    }
    .metric-card:hover { transform: translateY(-1px); box-shadow: 0 6px 10px -3px rgba(0, 0, 0, 0.1); }
    .metric-label { color: #0F172A; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; cursor: help; }
    .metric-value { color: #0F172A; font-size: 28px; font-weight: 800; line-height: 1; display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
    .metric-sub { font-size: 13px; font-weight: 600; color: #64748B; }

    /* Mini Grade Badges */
    .mini-badge-A { background-color: #CCFBF1; color: #0F766E; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 12px; border: 1px solid #5EEAD4; }
    .mini-badge-B { background-color: #D9F99D; color: #4D7C0F; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 12px; border: 1px solid #BEF264; }
    .mini-badge-C { background-color: #FEF08A; color: #854D0E; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 12px; border: 1px solid #FDE047; }
    .mini-badge-D { background-color: #FED7AA; color: #9A3412; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 12px; border: 1px solid #FDBA74; }
    .mini-badge-F { background-color: #FECDD3; color: #991B1B; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 12px; border: 1px solid #FDA4AF; }

    /* Tables & Cards */
    [data-testid="stDataFrame"] { background-color: #FFFFFF !important; border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 2px 4px -1px rgba(0,0,0,0.05); padding: 8px; }
    
    /* --- REDESIGNED ZM CARD (PREMIUM IDENTITY STRIP) --- */
    div[data-testid="stHorizontalBlock"]:has(.zm-card-content) {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-left: 4px solid #14B8A6 !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        margin-bottom: 16px !important;
        margin-top: 4px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
        align-items: center !important;
        min-height: 58px !important;
    }
    .zm-card-content { display: flex; align-items: center; gap: 12px; }
    .zm-avatar { width: 32px; height: 32px; background-color: #F0FDFA; color: #0F766E; border: 1px solid #CCFBF1; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 12px; letter-spacing: 0.5px; }
    .zm-info { display: flex; flex-direction: column; justify-content: center; }
    .zm-name { font-size: 14px; font-weight: 700; color: #0F172A; line-height: 1.2; }
    .zm-zone { font-size: 11px; font-weight: 600; color: #64748B; display: flex; align-items: center; gap: 4px; margin-top: 2px; text-transform: uppercase; letter-spacing: 0.5px; }
    .zm-zone .dot { width: 5px; height: 5px; background-color: #14B8A6; border-radius: 50%; }
    
    /* Turn the button inside the strip into a sleek text link */
    div[data-testid="stHorizontalBlock"]:has(.zm-card-content) div[data-testid="stButton"] > button {
        height: 32px !important;
        background-color: transparent !important;
        color: #06B6D4 !important;
        border: 1px solid transparent !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        box-shadow: none !important;
        padding: 0 12px !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.zm-card-content) div[data-testid="stButton"] > button:hover {
        background-color: #ECFEFF !important;
        border: 1px solid #A5F3FC !important;
        color: #0891B2 !important;
    }

    /* --- MODERN PAGE HEADERS --- */
    .page-header-container { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; margin-top: 8px; }
    .page-icon-container { display: flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 10px; color: #FFFFFF; }
    .page-icon-active { background-color: #14B8A6; box-shadow: 0 4px 10px rgba(20, 184, 166, 0.3); }
    .page-icon-warning { background-color: #DC2626; box-shadow: 0 4px 10px rgba(220, 38, 38, 0.3); }
    .page-icon-state { background-color: #3B82F6; box-shadow: 0 4px 10px rgba(59, 130, 246, 0.3); }
    .page-icon-zm { background-color: #4F46E5; box-shadow: 0 4px 10px rgba(79, 70, 229, 0.3); }
    .page-icon svg { width: 20px; height: 20px; stroke: #FFFFFF; }
    .page-title-text { font-size: 22px; font-weight: 800; color: #0F172A; letter-spacing: -0.5px; line-height: 1.2; }
    .page-subtitle-text { font-size: 13px; font-weight: 500; color: #64748B; margin-top: 2px; }

    /* Report Header */
    .report-header { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 2px 4px -1px rgba(0,0,0,0.05); }
    .report-title { color: #0F172A; font-size: 20px; font-weight: 800; margin-bottom: 4px; }
    .report-meta { color: #475569; font-size: 12px; line-height: 1.5; font-weight: 500; }
    
    /* Grades */
    .grade-badge { display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 20px; font-weight: 800; }
    .grade-A { background-color: #CCFBF1; color: #0F766E; border: 1px solid #5EEAD4; }
    .grade-B { background-color: #D9F99D; color: #4D7C0F; border: 1px solid #BEF264; }
    .grade-C { background-color: #FEF08A; color: #854D0E; border: 1px solid #FDE047; }
    .grade-D { background-color: #FED7AA; color: #9A3412; border: 1px solid #FDBA74; }
    .grade-F { background-color: #FECDD3; color: #991B1B; border: 1px solid #FDA4AF; }

    /* --- UNIFIED COMMAND BAR & NAVIGATION --- */
    div[data-testid="stHorizontalBlock"]:has(.app-header) {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-bottom: 3px solid #06B6D4 !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 4px -1px rgba(0,0,0,0.05) !important;
        padding: 6px 16px !important;
        margin-bottom: 8px !important;
        align-items: center !important;
        height: 56px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.app-header) .app-header {
        border: none !important; box-shadow: none !important; background: transparent !important; padding: 0 !important; margin: 0 !important;
    }
    
    div[data-testid="stHorizontalBlock"]:has(.app-header) div[data-testid="stRadio"] div[role="radiogroup"] {
        background-color: #F1F5F9 !important; border: 1px solid #E2E8F0 !important; border-radius: 8px !important; padding: 2px !important; gap: 2px !important;
        flex-wrap: nowrap !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.app-header) div[data-testid="stRadio"] div[role="radiogroup"] label {
        padding: 4px 10px !important; font-size: 12px !important; margin: 0 !important; white-space: nowrap !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.app-header) div[data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {
        background-color: #FFFFFF !important; border-radius: 6px !important; box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important; color: #0F172A !important; font-weight: 700 !important;
    }

    /* Header Details */
    .header-left { display: flex; align-items: center; gap: 10px; }
    .header-icon { display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; background-color: #DC2626; border-radius: 8px; color: #FFFFFF; box-shadow: 0 2px 6px rgba(220, 38, 38, 0.3); }
    .header-icon svg { width: 16px; height: 16px; stroke: #FFFFFF; }
    .header-title { font-size: 15px; font-weight: 800; color: #0F172A; letter-spacing: -0.3px; line-height: 1.1; margin-bottom: 0px; }
    .header-subtitle { font-size: 11px; font-weight: 500; color: #64748B; margin-top: 0; }
    
    /* Blinking Radar Dot */
    .status-dot { width: 6px; height: 6px; background-color: #14B8A6; border-radius: 50%; animation: pulse-cyan 2s infinite; display: inline-block; margin-right: 4px; }
    @keyframes pulse-cyan {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(20, 184, 166, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 4px rgba(20, 184, 166, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(20, 184, 166, 0); }
    }

    /* Compare Battle Cards */
    .battle-card { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; box-shadow: 0 2px 4px -1px rgba(0,0,0,0.05); margin-bottom: 12px; }
    .battle-card-blue { border-top: 4px solid #06B6D4; }
    .battle-card-red { border-top: 4px solid #F43F5E; }
    .battle-title { font-size: 16px; font-weight: 800; margin-bottom: 10px; }
    .battle-row { display: flex; justify-content: space-between; border-bottom: 1px solid #F1F5F9; padding: 8px 0; font-size: 13px; color: #475569; font-weight: 500;}
    .battle-row:last-child { border-bottom: none; }
    .battle-val { font-weight: 700; color: #0F172A; }

    /* --- PREMIUM INPUTS & DROPDOWNS --- */
    div[data-testid="stSelectbox"] { margin-bottom: 0px; }
    div[data-testid="stSelectbox"] div[role="combobox"] { 
        background-color: #FFFFFF !important; border: none !important; box-shadow: 0 0 0 1px #CBD5E1 inset !important; border-radius: 6px !important; 
        transition: all 0.2s ease-in-out !important; min-height: 36px !important; 
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div { background-color: transparent !important; border: none !important; }
    div[data-testid="stSelectbox"] div[role="combobox"]:hover { background-color: #F8FAFC !important; box-shadow: 0 0 0 1px #94A3B8 inset !important; }
    div[data-testid="stSelectbox"] div[role="combobox"]:focus-within { box-shadow: 0 0 0 2px #06B6D4 inset !important; background-color: #FFFFFF !important; }
    div[data-testid="stSelectbox"] div[role="combobox"] * { color: #0F172A !important; font-weight: 500 !important; font-size: 13px !important; }
    div[data-testid="stSelectbox"] div[role="combobox"] svg { fill: #64748B !important; width: 16px !important; height: 16px !important;}
    
    label[data-testid="stWidgetLabel"] p { color: #475569 !important; font-weight: 600 !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px !important;}

    div[data-testid="stDateInput"] div[data-baseweb="input"] { border: none !important; box-shadow: 0 0 0 1px #CBD5E1 inset !important; border-radius: 6px !important; background-color: #FFFFFF !important; min-height: 36px !important; }
    div[data-testid="stDateInput"] div[data-baseweb="input"]:focus-within { box-shadow: 0 0 0 2px #06B6D4 inset !important; background-color: #FFFFFF !important; }

    /* --- TIGHTENED FORM & PREMIUM BUTTONS --- */
    div[data-testid="stForm"] {
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 2px 4px -1px rgba(0,0,0,0.05) !important;
        margin-bottom: 12px !important;
    }
    
    /* The Apply Filters Button (Primary) */
    div[data-testid="stFormSubmitButton"] > button {
        background-color: #0891B2 !important;
        color: #FFFFFF !important;
        border: 1px solid #0E7490 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 0px 16px !important;
        transition: all 0.15s ease !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        height: 36px !important;
    }
    div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #0E7490 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    div[data-testid="stFormSubmitButton"] > button:active { transform: translateY(0) !important; }

    /* Standard Streamlit Buttons (Download, etc.) */
    div[data-testid="stButton"] > button, div[data-testid="stDownloadButton"] > button {
        background-color: #FFFFFF !important;
        color: #06B6D4 !important;
        border: 1px solid #06B6D4 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        height: 40px !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stButton"] > button:hover, div[data-testid="stDownloadButton"] > button:hover {
        background-color: #ECFEFF !important;
        border-color: #0891B2 !important;
        color: #0891B2 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION GATE ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
    <div class="auth-box">
        <h2 style="color:#0F172A; margin-bottom: 8px;">🔒 Secure Login</h2>
        <p style="color:#64748B; font-size: 14px; margin-bottom: 20px;">Enter the password to access the Bihar Health Dashboard.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        pwd = st.text_input("Password", type="password", label_visibility="collapsed")
        if st.button("Login", use_container_width=True):
            if pwd == "BiharHealth2026!":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect Password. Please try again.")
    st.stop()

# --- DATA & HELPERS ---
ZM_DATA = {
    "Keshav Kumar (Patna)": {"Bhojpur": ["DH Ara Bhojpur"], "Nalanda": ["DH Bihar Sharif Nalanda"], "Patna": ["DH (Guru Gobind Singh Hospital, Patna City)"], "Barh": ["SDH Barh Patna"], "Danapur": ["SDH Danapur Patna"]},
    "Samir Kumar Singh (Bhagalpur)": {"Banka": ["DH Banka"], "Bhagalpur": ["DH LNJP Bhagalpur"], "Jamui": ["DH Jamui"], "Munger": ["DH Munger"]},
    "Manish Rai (Champaran)": {"East Champaran": ["DH Motihari"], "Sitamarhi": ["DH Sitamarhi"], "West Champaran": ["SDH Narkatiyaganj"]},
    "Mohammad Asif Nasir (Darbhanga)": {"Darbhanga": ["DH Darbhanga"], "Madhubani": ["DH Madhubani"], "Samastipur": ["DH Samastipur"]},
    "Narendra Kumar Pal (Gaya)": {"Aurangabad": ["DH Aurangabad"], "Gaya": ["Prabhawati Hospital Gaya"], "Nawada": ["DH Nawada"], "Arwal": ["DH Arwal"], "Jehanabad": ["DH Jehanabad"]},
    "Santosh Kumar (Khagaria)": {"Begusarai": ["DH Begusarai"], "Khagaria": ["DH Khagaria"], "Lakhisarai": ["DH Lakhisarai"], "Sheikhpura": ["DH Sheikhpura"]},
    "Rupesh Kumar (Muzaffarpur)": {"Muzaffarpur": ["DH Muzaffarpur"], "Sheohar": ["Saroja Sitaram Sadar Hospital Sheohar"], "Vaishali": ["DH Hajipur"]},
    "Paras kumar Jaiswal (Purnia)": {"Araria": ["DH Araria"], "Katihar": ["DH Katihar"], "Kishanganj": ["DH Kishanganj"], "Purnia": ["CHC Krityanand Nagar"]},
    "Umesh Tiwari (Rohtas)": {"Buxar": ["DH Buxar"], "Kaimur": ["DH Kaimur"], "Rohtas": ["DH Sasaram"]},
    "Anant Kumar Ray (Saharsa)": {"Madhepura": ["DH Madhepura"], "Saharsa": ["DH Saharsa"], "Supaul": ["DH Supaul"]},
    "Krishna Prakash (Saran)": {"Gopalganj": ["DH Gopalganj"], "Saran": ["DH Saran"], "Siwan": ["DH Siwan"]}
}
DISTRICT_TO_ZM = {d: zm for zm, dists in ZM_DATA.items() for d in dists}

DISTRICT_MAP = {
    "Sheikhpura": "Seikhpura",
    "Rohtas": "Sasaram",
    "East Champaran": "Motihari",
    "West Champaran": "Narkatiaganj"
}
REVERSE_DISTRICT_MAP = {v: k for k, v in DISTRICT_MAP.items()}

def style_reason(val):
    if pd.isna(val): return ''
    val_str = str(val).lower()
    if any(w in val_str for w in ['operational', 'no lt', 'no runner', 'strike', 'breakdown', 'not available']):
        return 'background-color: #FEE2E2; color: #991B1B; font-weight: 600; border-radius: 4px; padding: 4px 8px; display: inline-block;'
    elif any(w in val_str for w in ['low opd', 'low footfall']):
        return 'background-color: #FEF08A; color: #854D0E; font-weight: 600; border-radius: 4px; padding: 4px 8px; display: inline-block;'
    elif 'never reported' in val_str or 'unknown' in val_str or 'awaiting launch' in val_str:
        return 'background-color: #F1F5F9; color: #475569; font-weight: 600; border-radius: 4px; padding: 4px 8px; display: inline-block;'
    return 'background-color: #E0F2FE; color: #0369A1; font-weight: 600; border-radius: 4px; padding: 4px 8px; display: inline-block;'

def format_reason(reason):
    if pd.isna(reason): return reason
    acronyms = ['OPD', 'LT', 'CHC', 'PHC', 'UPHC', 'RH', 'SDH', 'DH']
    words = str(reason).split()
    return ' '.join([w if w.upper() in acronyms else w.capitalize() for w in words])

@st.cache_data(ttl=3600, show_spinner="Fetching live data from Google Sheets...")
def fetch_google_sheet(url):
    try:
        response = requests.get(url, timeout=20) # Added timeout
        response.raise_for_status()
        return response.content
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {e}")
        return None

def read_sheet_robust(xls, sheet_name):
    try:
        df_raw = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        header_idx = next((i for i in range(min(15, len(df_raw))) for cell in df_raw.iloc[i] if 'name of the hospital' in str(cell).lower()), None)
        df = pd.read_excel(xls, sheet_name=sheet_name, header=header_idx) if header_idx is not None else pd.read_excel(xls, sheet_name=sheet_name)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

def find_facility_column(df):
    for c in df.columns:
        c_str = str(c).lower()
        if 'name of the hospital' in c_str: return c
        if 'hospital' in c_str and 'name' in c_str: return c
        
    best_col = None
    max_strings = 0
    for c in df.columns:
        valid_strings = sum(1 for val in df[c].head(50) if isinstance(val, str) and len(val.strip()) > 2)
        if valid_strings > max_strings and valid_strings > 2:
            max_strings = valid_strings
            best_col = c
    return best_col

def find_distance_column(df):
    for c in df.columns:
        c_str = str(c).lower()
        if 'distance from hub' in c_str or 'spokes distance' in c_str:
            return c
    return None

@st.cache_data(show_spinner=False)
def extract_date(col_name):
    dt = pd.NaT
    if isinstance(col_name, pd.Timestamp): 
        dt = col_name
    else:
        s = str(col_name).lower()
        s = s.replace('\xa0', ' ').replace('\u200b', '').replace('\u200e', '')
        s = s.replace('<br>', ' ').replace('<br/>', ' ').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        s = re.sub(r'total number of patients( on)?', '', s)
        s = re.sub(r'\(.*?\)', '', s) 
        s = s.replace('∕', '/').replace('⁄', '/')
        s = s.replace('‐', '-').replace('–', '-').replace('—', '-')
        s = re.sub(r'\s*([-/.∕⁄‐–—])\s*', r'\1', s)
        s = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', s)
        s = s.strip()
        
        if not re.search(r'\d{4}', s):
            if re.search(r'\b\d{1,2}[-/\.\s][a-z]{3}\b', s) or re.search(r'\b\d{1,2}[-/\.\s]\d{1,2}\b', s):
                s = s + " " + str(pd.Timestamp.today().year)
        
        match = re.search(r'(\d{4}[-/\.\s]\d{1,2}[-/\.\s]\d{1,2})|(\d{1,2}[-/\.\s]\d{1,2}[-/\.\s]\d{2,4})|(\d{1,2}[-/\.\s][a-z]{3}[-/\.\s]\d{2,4})', s)
        if match:
            raw_date = match.group(0)
            if re.match(r'^\d{4}/\d{4}$', raw_date):
                raw_date = raw_date[:2] + '/' + raw_date[2:]
            try:
                dt = pd.to_datetime(raw_date, dayfirst=True, errors='coerce')
            except:
                pass
                
    if pd.notna(dt) and dt > pd.Timestamp.today().normalize():
        return pd.NaT
    return dt

def find_date_columns(df):
    date_cols = []
    for c in df.columns:
        if pd.notna(extract_date(c)):
            date_cols.append(c)
    return date_cols

def get_facility_mask(df, facility_col):
    mask = df[facility_col].notna()
    mask &= ~df[facility_col].astype(str).str.upper().str.contains('TOTAL', na=False)
    mask &= ~df[facility_col].astype(str).str.upper().str.contains('JAIL', na=False)
    mask &= ~df[facility_col].astype(str).str.strip().str.lower().isin(['nan', 'none', ''])
    mask &= ~df[facility_col].astype(str).str.lower().str.contains('prepared|signature|verified|report', na=False)
    return mask

def process_district_df(df, time_filter, start_date=None, end_date=None, window_offset=0):
    if df is None: return None, None, None
    facility_col = find_facility_column(df)
    if not facility_col: return None, None, None
    df = df[get_facility_mask(df, facility_col)].copy()
    df = df.drop_duplicates(subset=[facility_col])
    
    total_absolute_facilities = len(df)
    
    date_cols = find_date_columns(df)
    if not date_cols:
        plot_df = df[[facility_col]].copy()
        plot_df['Total Patients'] = 0
        plot_df['Average Patients'] = 0.0
        plot_df['Zero Days'] = 0
        plot_df['Uptime %'] = 0.0
        plot_df['Last Sample Date'] = "Never Reported"
        return plot_df, None, {
            'total': 0, 'weighted_avg': 0.0, 'zero_days': 0, 
            'num_facilities': len(df), 'num_days': 0, 
            'facility_col': facility_col, 'active_date_cols': [], 'active_date_map': {},
            'text_records': [], 'active_facilities': 0,
            'total_absolute_facilities': total_absolute_facilities
        }

    paired = [(c, extract_date(c)) for c in date_cols]
    paired = [(c, d) for c, d in paired if pd.notna(d)]
    
    date_map = {}
    for c, d in paired:
        if d not in date_map: date_map[d] = []
        date_map[d].append(c)
        
    sorted_dates = sorted(date_map.keys())
    
    clean_df = df[[facility_col]].copy()
    for d in sorted_dates:
        cols = date_map[d]
        if len(cols) > 1:
            clean_df[d] = df[cols].apply(pd.to_numeric, errors='coerce').fillna(0).max(axis=1)
        else:
            clean_df[d] = pd.to_numeric(df[cols[0]], errors='coerce').fillna(0)
            
    clean_df = clean_df.loc[:, (clean_df != 0).any(axis=0) | (clean_df.columns == facility_col)]
    sorted_dates = [d for d in sorted_dates if d in clean_df.columns]
    
    if not sorted_dates:
        plot_df = df[[facility_col]].copy()
        plot_df['Total Patients'] = 0
        plot_df['Average Patients'] = 0.0
        plot_df['Zero Days'] = 0
        plot_df['Uptime %'] = 0.0
        plot_df['Last Sample Date'] = "Never Reported"
        return plot_df, None, {
            'total': 0, 'weighted_avg': 0.0, 'zero_days': 0, 
            'num_facilities': len(df), 'num_days': 0, 
            'facility_col': facility_col, 'active_date_cols': [], 'active_date_map': {},
            'text_records': [], 'active_facilities': 0,
            'total_absolute_facilities': total_absolute_facilities
        }

    active_dates = sorted_dates
    if time_filter == "Select Dates..." and start_date and end_date:
        active_dates = [d for d in sorted_dates if start_date <= d.date() <= end_date]
    else:
        windows = {"Past Week": 7, "Past 2 Weeks": 15, "Past Month": 30}
        if time_filter in windows:
            w = windows[time_filter]
            end_idx = len(sorted_dates) - w * window_offset
            start_idx = max(0, end_idx - w)
            active_dates = sorted_dates[start_idx:end_idx] if end_idx > 0 else []
        
    if not active_dates:
        if window_offset > 0:
            plot_df = df[[facility_col]].copy()
            plot_df['Total Patients'] = 0
            plot_df['Average Patients'] = 0.0
            plot_df['Zero Days'] = 0
            plot_df['Uptime %'] = 0.0
            plot_df['Last Sample Date'] = "Never Reported"
            return plot_df, None, {
                'total': 0, 'weighted_avg': 0.0, 'zero_days': 0, 
                'num_facilities': len(df), 'num_days': 0, 
                'facility_col': facility_col, 'active_date_cols': [], 'active_date_map': {},
                'text_records': [], 'active_facilities': 0,
                'total_absolute_facilities': total_absolute_facilities
            }
        active_dates = sorted_dates

    text_records = []
    def is_text_note(x):
        if not isinstance(x, str): return False
        v = x.strip().lower()
        if v in ['', 'nan', 'none', '0', '0.0']: return False
        try:
            float(v); return False
        except ValueError:
            return True
            
    for c, d in paired:
        if d in active_dates:
            str_mask = df[c].apply(is_text_note)
            if str_mask.any():
                for idx in df[str_mask].index:
                    raw_note = str(df.loc[idx, c]).strip()
                    text_records.append({'Facility': df.loc[idx, facility_col], 'Date': d, 'Raw_Note': raw_note})

    plot_df = clean_df[[facility_col] + active_dates].copy()
    plot_df['Total Patients'] = plot_df[active_dates].sum(axis=1)
    plot_df['Average Patients'] = plot_df[active_dates].mean(axis=1).round(1)
    plot_df['Zero Days'] = (plot_df[active_dates] == 0).sum(axis=1)
    
    def get_last_sample_date(row):
        for d in reversed(sorted_dates):
            if row[d] > 0:
                return d.strftime('%d %b %Y')
        return "Never Reported"
    
    plot_df['Last Sample Date'] = clean_df.apply(get_last_sample_date, axis=1)
    active_facilities = int((plot_df['Total Patients'] > 0).sum())
    
    district_total = int(plot_df['Total Patients'].sum())
    num_facilities = len(plot_df)
    num_days = len(active_dates)
    weighted_avg = round(district_total / (num_facilities * num_days), 1) if num_facilities > 0 and num_days > 0 else 0
    total_zero = int(plot_df['Zero Days'].sum())
    
    if num_days > 0: plot_df['Uptime %'] = ((num_days - plot_df['Zero Days']) / num_days * 100).round(1)
    else: plot_df['Uptime %'] = 0
        
    col_map = {d: d.strftime('%d %b') for d in active_dates}
    active_date_map = {col_map[d]: d for d in active_dates}
    plot_df = plot_df.rename(columns=col_map)
        
    return plot_df, None, {
        'total': district_total, 'weighted_avg': weighted_avg, 'zero_days': total_zero,
        'num_facilities': num_facilities, 'num_days': num_days, 'facility_col': facility_col,
        'active_date_cols': [col_map[d] for d in active_dates], 'active_date_map': active_date_map,
        'text_records': text_records, 'active_facilities': active_facilities,
        'total_absolute_facilities': total_absolute_facilities
    }

def calc_uptime(s):
    total_fd = s['num_facilities'] * s['num_days']
    return round(((total_fd - s['zero_days']) / total_fd * 100), 1) if total_fd > 0 else 0

def calculate_grade(uptime_pct, avg_per_day):
    if avg_per_day == 0 or uptime_pct < 30: return "F"
    if uptime_pct > 85 and avg_per_day > 10: return "A"
    if uptime_pct > 70 and avg_per_day > 5: return "B"
    if uptime_pct > 50 and avg_per_day > 2: return "C"
    if uptime_pct > 30 and avg_per_day > 1: return "D"
    return "F"

def district_grade(plot_df):
    if plot_df is None or plot_df.empty: return "F"
    grade_map = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}
    reverse_map = {5: "A", 4: "B", 3: "C", 2: "D", 1: "F"}
    grades = [grade_map[calculate_grade(row['Uptime %'], row['Average Patients'])] for _, row in plot_df.iterrows()]
    if not grades: return "F"
    avg_grade = sum(grades) / len(grades)
    rounded_grade = math.floor(avg_grade + 0.5)
    return reverse_map[max(1, min(5, int(rounded_grade)))]

def grade_emoji(g): return {"A": "🟢 A", "B": "🟢 B", "C": "🟡 C", "D": "🟠 D", "F": "🔴 F"}.get(g, g)

@st.cache_data(show_spinner=False)
def calculate_all_districts(sheet_names_tuple, file_bytes, time_filter, start_date=None, end_date=None, window_offset=0, _cache_buster="v34.0"):
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    data = []
    for sheet in sheet_names_tuple:
        try:
            sdf = read_sheet_robust(xls, sheet)
            _, _, s = process_district_df(sdf, time_filter, start_date, end_date, window_offset=window_offset)
            if s:
                display_name = REVERSE_DISTRICT_MAP.get(sheet, sheet)
                data.append({
                    'District': display_name, 
                    'Total Patients': s['total'], 
                    'Weighted Avg': s['weighted_avg'], 
                    'Uptime %': calc_uptime(s), 
                    'Facilities': s['total_absolute_facilities'],
                    'Active Spokes': s['active_facilities'],
                    'Days Reported': s['num_days']
                })
        except Exception: pass
    return pd.DataFrame(data)

@st.cache_data(show_spinner=False)
def get_all_facility_data(sheet_names_tuple, file_bytes, time_filter, start_date=None, end_date=None, _cache_buster="v34.0"):
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    all_data = []
    for sheet in sheet_names_tuple:
        try:
            sdf = read_sheet_robust(xls, sheet)
            fac_col_raw = find_facility_column(sdf)
            if not fac_col_raw: continue
            date_cols_raw = find_date_columns(sdf)
            is_pending = len(date_cols_raw) == 0

            plot_df, _, stats = process_district_df(sdf, time_filter, start_date, end_date)
            if plot_df is None: continue
            
            fac_col = stats['facility_col']
            text_records = stats.get('text_records', [])
            
            d_df = pd.DataFrame({
                'District': REVERSE_DISTRICT_MAP.get(sheet, sheet),
                'Facility': plot_df[fac_col],
                'Total Patients': plot_df['Total Patients'],
                'Avg / Day': plot_df['Average Patients'],
                'Uptime %': plot_df['Uptime %'],
                'Last Sample Date': plot_df['Last Sample Date'],
                'Zero Days': plot_df['Zero Days'],
                'Status': 'Pending Launch' if is_pending else 'Operational'
            })
            d_df['Grade'] = d_df.apply(lambda r: calculate_grade(r['Uptime %'], r['Avg / Day']), axis=1)
            
            def get_reason(row):
                if row['Total Patients'] > 0: return ""
                fac_texts = [t for t in text_records if t['Facility'] == row['Facility']]
                if fac_texts: return fac_texts[-1]['Raw_Note']
                return "Awaiting Launch" if is_pending else "Unknown / No Note"

            d_df['Primary Reason'] = d_df.apply(get_reason, axis=1)
            all_data.append(d_df)
        except Exception:
            pass
            
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()

def get_district_monthly_trend(df_raw, facility_col):
    monthly_totals = {}
    df_filtered = df_raw[get_facility_mask(df_raw, facility_col)]
    date_cols = find_date_columns(df_filtered)
    for c in date_cols:
        dt = extract_date(c)
        if pd.isna(dt): continue
        month_key = dt.strftime('%b %Y')
        total_patients = pd.to_numeric(df_filtered[c], errors='coerce').fillna(0).sum()
        if total_patients > 0 or month_key in monthly_totals:
            monthly_totals[month_key] = monthly_totals.get(month_key, 0) + total_patients
    if not monthly_totals: return pd.DataFrame()
    trend_df = pd.DataFrame(list(monthly_totals.items()), columns=['Month', 'Total Patients'])
    trend_df['Sort_Date'] = pd.to_datetime(trend_df['Month'], format='%b %Y', errors='coerce')
    trend_df = trend_df.dropna(subset=['Sort_Date']).sort_values('Sort_Date')
    return trend_df

def _zm_aggregates(state_df):
    out = {}
    for zm, dists in ZM_DATA.items():
        subset = state_df[state_df['District'].isin(dists.keys())]
        if subset.empty: continue
        facs = int(subset['Facilities'].sum())
        pats = int(subset['Total Patients'].sum())
        fac_days = int((subset['Facilities'] * subset['Days Reported']).sum())
        avg = round(pats / fac_days, 1) if fac_days > 0 else 0.0
        uptime = round(subset['Uptime %'].mean(), 1)
        out[zm] = {
            'Districts': len(dists),
            'Total Patients': pats,
            'Weighted Avg': avg,
            'Uptime %': uptime,
            'Active Spokes': int(subset['Active Spokes'].sum()),
            'Total Spokes': facs,
        }
    return out

# --- MAIN AREA ---
if SPREADSHEET_URL == "YOUR_PUBLISHED_XLSX_URL_HERE":
    st.error("Please insert your Published Google Sheets URL in the code.")
    st.stop()
    
file_bytes = fetch_google_sheet(SPREADSHEET_URL)

if file_bytes is None:
    st.markdown("""
    <div class="app-header" style="border-color:#FECACA; box-shadow: 0 10px 25px -5px rgba(239, 68, 68, 0.1);">
        <div class="header-left">
            <div class="header-icon" style="background-color:#FEE2E2; color:#EF4444;">⚠️</div>
            <div>
                <div class="header-title">Bihar Health Dashboard</div>
                <div class="header-subtitle">Could not connect to the Google Sheet.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

xls = pd.ExcelFile(io.BytesIO(file_bytes))
valid_keywords = set(DISTRICT_TO_ZM.keys()).union(set(DISTRICT_MAP.values())).union(set(DISTRICT_MAP.keys()))
available_sheets = []
for s in xls.sheet_names:
    s_lower = s.lower()
    if any(kw.lower() in s_lower or s_lower in kw.lower() for kw in valid_keywords):
        available_sheets.append(s)

_DISPLAY_TO_SHEET = {REVERSE_DISTRICT_MAP.get(s, s): s for s in available_sheets}
_DISPLAY_DISTRICTS = sorted(_DISPLAY_TO_SHEET.keys())

# --- UNIFIED COMMAND BAR ---
col_title, col_nav, col_time_ctrl = st.columns([2.5, 4.5, 2.0])

with col_title:
    st.markdown("""
    <div class="app-header">
        <div class="header-left">
            <div class="header-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14.5 2v17.5c0 1.4-1.1 2.5-2.5 2.5h0c-1.4 0-2.5-1.1-2.5-2.5V2" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M8.5 2h7" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M14.5 16h-5" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div>
                <div class="header-title">Bihar Health Dashboard</div>
                <div class="header-subtitle">Statewide Operations & Pathology</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_nav:
    _NAV_OPTS = ["District View", "State View", "ZM View", "Active Spokes", "Zero-Sample Tracker"]
    if 'view_mode_override' in st.session_state:
        _override = st.session_state.pop('view_mode_override')
        if _override in _NAV_OPTS:
            st.session_state['nav_radio'] = _override
    view_mode = st.radio("Navigation", _NAV_OPTS, key='nav_radio', horizontal=True, label_visibility="collapsed")

with col_time_ctrl:
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0px; padding-bottom: 2px;">
        <div style="font-size: 10px; font-weight: 700; color: #64748B; letter-spacing: 0.5px;">TIME RANGE</div>
        <div style="font-size: 10px; font-weight: 700; color: #14B8A6; display: flex; align-items: center;">
            <div class="status-dot"></div> Live
        </div>
    </div>
    """, unsafe_allow_html=True)
    time_filter = st.selectbox("Time Range", ["Full History", "Past Week", "Past 2 Weeks", "Past Month", "Select Dates..."], label_visibility="collapsed")
    start_date, end_date = None, None
    if time_filter == "Select Dates...":
        start_date = st.date_input("Start Date", value=pd.Timestamp.now() - timedelta(days=30))
        end_date = st.date_input("End Date", value=pd.Timestamp.now())
        date_range_str = f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}"
    else:
        date_range_str = time_filter

PLOTLY_LAYOUT = dict(
    template="plotly_white", 
    font=dict(family="Inter, sans-serif", size=13, color="#475569"), 
    title_font=dict(size=16, color="#0F172A", family="Inter, sans-serif", weight="bold"), 
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
    margin=dict(l=10, r=10, t=60, b=10),
    xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#CBD5E1'),
    yaxis=dict(showgrid=True, gridwidth=1, gridcolor='#CBD5E1')
)

# ==============================================================================
# VIEW: DISTRICT VIEW
# ==============================================================================
if view_mode == "District View":
    # --- UNIFIED SINGLE-ROW CONTROL STRIP ---
    with st.form("district_filters", clear_on_submit=False):
        col_d, col_h, col_chk, col_btn = st.columns([2.5, 2.5, 1.5, 1], vertical_alignment="bottom")
        
        with col_d: 
            selected_district_zm = st.selectbox("Select District", sorted(DISTRICT_TO_ZM.keys()))
        with col_h:
            zm_name_for_district = DISTRICT_TO_ZM.get(selected_district_zm, "Unknown")
            selected_hub_zm = st.selectbox("Select Hub", sorted(ZM_DATA[zm_name_for_district][selected_district_zm]))
        with col_chk:
            active_only = st.checkbox("Exclude Inactive", value=False)
        with col_btn:
            submitted = st.form_submit_button("Apply Filters", use_container_width=True)

    # --- REDESIGNED ZM PROFILE STRIP ---
    zone_name = zm_name_for_district.split("(")[1].replace(")", "").strip() + " Zone" if "(" in zm_name_for_district else "Unknown Zone"
    display_zm = zm_name_for_district.split("(")[0].strip() if "(" in zm_name_for_district else zm_name_for_district
    initials = "".join([part[0] for part in display_zm.split()[:2]]).upper()

    col_zm_card, col_zm_btn = st.columns([4.5, 1], vertical_alignment="center")
    with col_zm_card:
        st.markdown(f'''
        <div class="zm-card-content">
            <div class="zm-avatar">{initials}</div>
            <div class="zm-info">
                <div class="zm-name">{display_zm}</div>
                <div class="zm-zone"><span class="dot"></span>{zone_name}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    with col_zm_btn:
        if st.button("View Profile →", use_container_width=True):
            st.session_state.zm_view_target = zm_name_for_district
            st.session_state.view_mode_override = "ZM View"
            st.rerun()

    # --- DATA LOADING ---
    target_district = DISTRICT_MAP.get(selected_district_zm, selected_district_zm)
    sheet_to_load = next((s for s in available_sheets if s.lower() == selected_district_zm.lower() or s.lower() == target_district.lower()), None)
    if not sheet_to_load:
        sheet_to_load = next((s for s in available_sheets if selected_district_zm.lower() in s.lower() or s.lower() in selected_district_zm.lower() or target_district.lower() in s.lower() or s.lower() in target_district.lower()), None)
            
    if not sheet_to_load:
        st.warning(f"⏳ **Data Not Yet Available for {selected_district_zm}**"); st.stop()
        
    df_raw = read_sheet_robust(xls, sheet_to_load)
    plot_df, _, stats = process_district_df(df_raw, time_filter, start_date, end_date)
    if plot_df is None: st.error(f"Could not process data."); st.stop()
    facility_col = stats['facility_col']

    total_active = stats['active_facilities']
    total_inactive = stats['num_facilities'] - total_active
    zero_day_facilities = int((plot_df['Zero Days'] > 0).sum())
    active_icon = "🟢" if total_active > 0 else "🔴"
    inactive_icon = "🔴" if total_inactive > 0 else "🟢"

    d_tab1, d_tab2, d_tab3, d_tab4 = st.tabs(["📊 Dashboard", "📋 Report Card", "🩺 Diagnosis & Tracking", "📍 Logistics"])

    with d_tab1:
        filtered_base = plot_df.copy()
        if active_only: filtered_base = filtered_base[filtered_base['Total Patients'] > 0]
        
        num_facs = len(filtered_base)
        dist_total = int(filtered_base['Total Patients'].sum())
        
        if num_facs > 0 and stats['num_days'] > 0:
            new_weighted_avg = round(dist_total / (num_facs * stats['num_days']), 1)
            total_fd = num_facs * stats['num_days']
            new_zero_days = int(filtered_base['Zero Days'].sum())
            new_uptime = round(((total_fd - new_zero_days) / total_fd * 100), 1)
        else:
            new_weighted_avg = 0.0
            new_uptime = 0.0
            
        if not filtered_base.empty:
            best_idx = filtered_base['Average Patients'].idxmax()
            best_row = filtered_base.loc[best_idx]
            best_name = best_row[facility_col]
            best_grade = calculate_grade(best_row['Uptime %'], best_row['Average Patients'])
            best_avg = best_row['Average Patients']
        else:
            best_name = "N/A"
            best_grade = "F"
            best_avg = 0
            
        uptime_color = "#14B8A6" if new_uptime >= 50 else "#F43F5E"

        st.markdown(f'''
        <div class="metric-grid">
            <div class="metric-card"><div class="metric-label" title="Total number of reporting facilities.">Total Spokes</div><div class="metric-value">{num_facs}</div></div>
            <div class="metric-card">
                <div class="metric-label" title="The facility with the highest average patients per day.">Best Performing Spoke</div>
                <div class="metric-value" style="font-size: 18px; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%;" title="{best_name}">{best_name}</div>
                <div class="metric-sub" style="display: flex; align-items: center; gap: 8px;">
                    <span class="mini-badge-{best_grade}">{best_grade}</span>
                    <span>{best_avg} Avg/Day</span>
                </div>
            </div>
            <div class="metric-card"><div class="metric-label" title="Total number of patients seen across all facilities.">Total Patients</div><div class="metric-value">{dist_total:,}</div></div>
            <div class="metric-card"><div class="metric-label" title="Total patients divided by (facilities × days).">Weighted Avg / Day</div><div class="metric-value">{new_weighted_avg}</div></div>
            <div class="metric-card">
                <div class="metric-label" title="The percentage of days facilities reported more than 0 patients.">Facility Uptime</div>
                <div class="metric-value">{new_uptime}%</div>
                <div style="height: 6px; background-color: #E2E8F0; border-radius: 3px; margin-top: 10px; overflow: hidden;">
                    <div style="height: 100%; width: {new_uptime}%; background-color: {uptime_color};"></div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        c1, c2 = st.columns([3, 1.5], vertical_alignment="bottom")
        with c1: metric_option = st.radio("Metric:", ("Average Patients", "Total Patients", "Uptime %"), horizontal=True, key="d2")
        with c2: sort_option = st.selectbox("Sort:", ["Highest to Lowest", "Lowest to Highest"], key="d3")
        
        metric_col = {'Average Patients': 'Average Patients', 'Total Patients': 'Total Patients', 'Uptime %': 'Uptime %'}[metric_option]
        filtered = filtered_base.copy()
            
        if filtered.empty: st.warning("No data matches the filters.")
        else:
            sorted_df = filtered.sort_values(by=metric_col, ascending=(sort_option == "Lowest to Highest"))
            sorted_df['Grade'] = sorted_df.apply(lambda r: calculate_grade(r['Uptime %'], r['Average Patients']), axis=1)
            text_labels = [f"{v:.1f}%" if metric_col == 'Uptime %' else (f"{v:.1f}" if v % 1 != 0 else f"{int(v)}") for v in sorted_df[metric_col]]
                
            grade_color_map = {'A': '#14B8A6', 'B': '#84CC16', 'C': '#FBBF24', 'D': '#F97316', 'F': '#F43F5E'}
            
            fig = px.bar(
                sorted_df, y=facility_col, x=metric_col, orientation='h', color='Grade', 
                color_discrete_map=grade_color_map, text=text_labels, 
                category_orders={facility_col: sorted_df[facility_col].tolist()},
                title=f"<b>{metric_option} per Facility</b><br><span style='font-size:13px;color:#64748B;font-weight:500;'>{selected_district_zm} District | {date_range_str}</span>"
            )
            
            if metric_col == 'Average Patients': current_avg = new_weighted_avg
            elif metric_col == 'Total Patients': current_avg = round(filtered['Total Patients'].mean(), 1)
            else: current_avg = round(filtered['Uptime %'].mean(), 1)
                
            fig.add_vline(x=current_avg, line_dash="dash", line_color="#0F172A", line_width=2)
            
            layout_dict = PLOTLY_LAYOUT.copy()
            layout_dict.update(dict(
                height=max(500, len(sorted_df) * 30),
                yaxis=dict(autorange="reversed", showgrid=False, tickfont=dict(size=13, color="#1E293B", weight="bold")),
                xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#CBD5E1', tickfont=dict(size=12, color="#64748B")),
                showlegend=False, xaxis_title=metric_option, yaxis_title="",
                margin=dict(l=40, r=80, t=80, b=10), coloraxis_showscale=False
            ))
            fig.update_layout(**layout_dict)
            fig.update_traces(textposition='outside', textfont=dict(color="#1E293B", size=12, weight="bold"), cliponaxis=False)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("<hr style='margin: 20px 0 16px 0; border-color: #CBD5E1;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color:#0F172A; margin-bottom:10px;'>🔍 Facility Drill-Down</h4>", unsafe_allow_html=True)
            
            drill_options = sorted_df[facility_col].tolist()
            selected_drill_facility = st.selectbox("Facility", drill_options, index=0 if drill_options else None, label_visibility="collapsed")
            
            if selected_drill_facility:
                fac_row = plot_df[plot_df[facility_col] == selected_drill_facility].iloc[0]
                
                m1, m2, m3 = st.columns(3)
                m1.markdown(f"<div class='metric-card'><div class='metric-label'>Avg / Day</div><div class='metric-value'>{fac_row['Average Patients']}</div></div>", unsafe_allow_html=True)
                m2.markdown(f"<div class='metric-card'><div class='metric-label'>Uptime</div><div class='metric-value'>{fac_row['Uptime %']}%</div></div>", unsafe_allow_html=True)
                m3.markdown(f"<div class='metric-card'><div class='metric-label'>Zero Days</div><div class='metric-value'>{fac_row['Zero Days']}</div></div>", unsafe_allow_html=True)
                
                drill_trend = [{'Date': stats['active_date_map'][c], 'Patients': fac_row[c]} for c in stats['active_date_cols']]
                if drill_trend:
                    dt_df = pd.DataFrame(drill_trend).sort_values('Date')
                    fig_dt = px.area(dt_df, x='Date', y='Patients', markers=True)
                    fig_dt.update_traces(line_color='#06B6D4', line_width=3, marker=dict(size=6, color='#FFFFFF', line=dict(width=2, color='#06B6D4')), fillcolor='rgba(6, 182, 212, 0.1)')
                    
                    dt_layout = PLOTLY_LAYOUT.copy()
                    dt_layout.update(dict(
                        height=300,
                        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#CBD5E1', tickformat="%d %b", range=[dt_df['Date'].min(), dt_df['Date'].max()]),
                        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='#CBD5E1'),
                        margin=dict(l=10, r=10, t=20, b=10)
                    ))
                    fig_dt.update_layout(**dt_layout)
                    st.plotly_chart(fig_dt, use_container_width=True)

        st.markdown("<h4 style='color:#0F172A; margin-top:20px; margin-bottom:10px;'>📈 Monthly Patient Volume</h4>", unsafe_allow_html=True)
        monthly_df = get_district_monthly_trend(df_raw, facility_col)
        
        if not monthly_df.empty:
            fig_m = px.bar(monthly_df, x='Month', y='Total Patients', text='Total Patients')
            fig_m.update_traces(marker_color='#06B6D4', texttemplate='%{text:,}', textposition='outside')
            m_layout = PLOTLY_LAYOUT.copy()
            m_layout.update(dict(height=350, xaxis=dict(showgrid=False, type='category'), yaxis=dict(showgrid=True, gridwidth=1, gridcolor='#CBD5E1', title="Total Patients")))
            fig_m.update_layout(**m_layout)
            st.plotly_chart(fig_m, use_container_width=True)

        st.markdown("<h4 style='color:#0F172A; margin-top:20px; margin-bottom:10px;'>🔥 Spoke Heatmap</h4>", unsafe_allow_html=True)
        if stats['active_date_cols']:
            heatmap_df = plot_df.set_index(facility_col)[stats['active_date_cols']].copy()
            heatmap_df['Total'] = heatmap_df.sum(axis=1)
            heatmap_df = heatmap_df.sort_values(by='Total', ascending=True).drop(columns=['Total'])
            
            fig_h = px.imshow(heatmap_df, aspect='auto', color_continuous_scale=[[0, '#F0FDFA'], [0.1, '#99F6E4'], [1, '#0F766E']], labels=dict(x="Date", y="", color="Patients"))
            fig_h.update_traces(xgap=2, ygap=2)
            
            hm_layout = PLOTLY_LAYOUT.copy()
            hm_layout.update(dict(
                height=max(400, len(heatmap_df) * 35),
                yaxis=dict(tickfont=dict(size=12, color="#1E293B", weight="bold")),
                xaxis=dict(tickfont=dict(size=11, color="#475569"), tickangle=-45),
                coloraxis_colorbar=dict(title="Patients", thickness=15)
            ))
            fig_h.update_layout(**hm_layout)
            st.plotly_chart(fig_h, use_container_width=True)

    with d_tab2:
        period_str = "N/A"
        if stats['active_date_cols']:
            period_str = f"{stats['active_date_cols'][0]} – {stats['active_date_cols'][-1]}"
        
        scorecard = plot_df.copy()
        scorecard['Grade'] = scorecard.apply(lambda r: calculate_grade(r['Uptime %'], r['Average Patients']), axis=1)
        scorecard = scorecard.sort_values(by=['Grade', 'Uptime %', 'Average Patients'], ascending=[True, False, False])
        
        d_grade = district_grade(plot_df)
        
        st.markdown(f'''
        <div class="report-header">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div class="report-title" style="margin-bottom: 0;">District Report Card — {selected_district_zm}</div>
                <div style="background-color: #ECFEFF; color: #0E7490; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 14px; border: 1px solid #A5F3FC; display: flex; align-items: center; gap: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    🏥 <span>Total Spokes: {stats['num_facilities']}</span>
                </div>
            </div>
            <div class="report-meta"><strong>ZM:</strong> {zm_name_for_district} &nbsp;|&nbsp; <strong>Hub:</strong> {selected_hub_zm} &nbsp;|&nbsp; <strong>Period:</strong> {period_str} ({stats["num_days"]} days)</div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown(f'''
        <div class="metric-grid">
            <div class="metric-card"><div class="metric-label" title="Total number of patients seen across all facilities.">Total Patients</div><div class="metric-value">{stats['total']:,}</div></div>
            <div class="metric-card"><div class="metric-label" title="Total patients divided by (facilities × days).">Weighted Avg / Day</div><div class="metric-value">{stats['weighted_avg']}</div></div>
            <div class="metric-card"><div class="metric-label" title="The percentage of days facilities reported more than 0 patients.">Facility Uptime</div><div class="metric-value">{calc_uptime(stats)}%</div></div>
            <div class="metric-card" style="background-color:#F8FAFC;"><div class="metric-label" title="The average grade of all facilities in this district.">District Grade</div><div><span class="grade-badge grade-{d_grade}">{d_grade}</span></div></div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align: center; margin-top: 10px; margin-bottom: 8px;">
            <div style="display: inline-flex; gap: 16px; font-size: 13px; font-weight: 600; color: #475569; background-color: #FFFFFF; padding: 8px 16px; border-radius: 20px; border: 1px solid #E2E8F0; align-items: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                <span style="color: #64748B;">Grade Legend:</span>
                <div style="display: flex; align-items: center; gap: 4px;"><span style="display:inline-block; width:12px; height:12px; background-color:#14B8A6; border-radius:2px;"></span> A</div>
                <div style="display: flex; align-items: center; gap: 4px;"><span style="display:inline-block; width:12px; height:12px; background-color:#84CC16; border-radius:2px;"></span> B</div>
                <div style="display: flex; align-items: center; gap: 4px;"><span style="display:inline-block; width:12px; height:12px; background-color:#FBBF24; border-radius:2px;"></span> C</div>
                <div style="display: flex; align-items: center; gap: 4px;"><span style="display:inline-block; width:12px; height:12px; background-color:#F97316; border-radius:2px;"></span> D</div>
                <div style="display: flex; align-items: center; gap: 4px;"><span style="display:inline-block; width:12px; height:12px; background-color:#F43F5E; border-radius:2px;"></span> F</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<h4 style='color:#0F172A; margin-top:16px; margin-bottom:10px;'>Spoke Scorecard</h4>", unsafe_allow_html=True)
        display = pd.DataFrame()
        display['Facility'] = scorecard[facility_col]
        display['Grade'] = scorecard['Grade'].apply(grade_emoji)
        display['Uptime %'] = scorecard['Uptime %']
        display['Avg / Day'] = scorecard['Average Patients']
        display['Total Patients'] = scorecard['Total Patients'].astype(int)
        display['Zero Days'] = scorecard['Zero Days'].astype(int)
        
        total_row = pd.DataFrame([{
            'Facility': '🏆 TOTAL', 'Grade': d_grade,
            'Uptime %': round(calc_uptime(stats), 1), 'Avg / Day': stats['weighted_avg'],
            'Total Patients': stats['total'], 'Zero Days': stats['zero_days']
        }])
        display = pd.concat([total_row, display], ignore_index=True)
        
        st.dataframe(display, use_container_width=True, hide_index=True, column_config={
            "Facility": st.column_config.TextColumn("Facility", width="large"),
            "Grade": st.column_config.TextColumn("Grade", width="small"),
            "Uptime %": st.column_config.NumberColumn("Uptime %", format="%.1f%%"),
            "Avg / Day": st.column_config.NumberColumn("Avg / Day", format="%.1f"),
            "Total Patients": st.column_config.NumberColumn("Total Patients", format="%d"),
            "Zero Days": st.column_config.NumberColumn("Zero Days", format="%d")
        })
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            summary_df = pd.DataFrame({
                'Metric': ['District', 'ZM', 'Hub', 'Period', 'Total Patients', 'Weighted Avg / Day', 'Facility Uptime', 'District Grade'],
                'Value': [selected_district_zm, zm_name_for_district, selected_hub_zm, date_range_str, stats['total'], stats['weighted_avg'], f"{calc_uptime(stats)}%", d_grade]
            })
            summary_df.to_excel(writer, index=False, sheet_name='Summary')
            display.to_excel(writer, index=False, sheet_name='Scorecard')
            
        st.download_button(
            label="📥 Download Excel Report", data=buffer.getvalue(),
            file_name=f"{selected_district_zm}_Report_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True
        )
        st.caption("The Excel file contains two sheets: one for the District Summary and one for the full Spoke Scorecard.")

    with d_tab3:
        sub_tab1, sub_tab2, sub_tab3 = st.tabs([f"🔴 Failures ({zero_day_facilities})", f"{active_icon} Active ({total_active})", f"{inactive_icon} Inactive ({total_inactive})"])
        
        with sub_tab1:
            text_records = stats.get('text_records', [])
            if not text_records:
                st.success("✅ No text notes (reasons) were found for this district in the selected time range. All zero days are pure numerical zeroes.")
            else:
                df_texts = pd.DataFrame(text_records)
                offense_data = []
                for _, row in plot_df.iterrows():
                    fac_name = row[facility_col]
                    z_days = row['Zero Days']
                    if z_days > 0:
                        fac_texts = df_texts[df_texts['Facility'] == fac_name]
                        primary_reason = fac_texts['Raw_Note'].value_counts().idxmax() if not fac_texts.empty else "Unknown / No Note"
                        offense_data.append({'Facility': fac_name, 'Uptime %': row['Uptime %'], 'Primary Reason': primary_reason})
                if offense_data:
                    offense_df = pd.DataFrame(offense_data).sort_values('Uptime %', ascending=True).reset_index(drop=True)
                    styled_offense = offense_df.style.map(style_reason, subset=['Primary Reason'])
                    st.dataframe(styled_offense, use_container_width=True, hide_index=True, column_config={
                        "Uptime %": st.column_config.NumberColumn("Uptime %", format="%.1f%%")
                    })
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                        offense_df.to_excel(writer, index=False, sheet_name='Follow-Up List')
                    st.download_button(
                        label="🚨 Download Follow-up List", data=buf.getvalue(),
                        file_name=f"{selected_district_zm}_Followup.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True
                    )
                else:
                    st.info("No facilities had zero days in this period.")
        
        with sub_tab2:
            active_df = plot_df[plot_df['Total Patients'] > 0].copy()
            if active_df.empty:
                st.info("No active spokes in this district for the selected time range.")
            else:
                active_df['Grade'] = active_df.apply(lambda r: calculate_grade(r['Uptime %'], r['Average Patients']), axis=1)
                active_df = active_df.sort_values(by=['Grade', 'Uptime %', 'Average Patients'], ascending=[True, False, False]).reset_index(drop=True)
                
                def style_grade_local(val):
                    if val in ['A', 'B']: return 'background-color: #CCFBF1; color: #0F766E; font-weight: bold;'
                    elif val in ['C', 'D']: return 'background-color: #FEF08A; color: #854D0E; font-weight: bold;'
                    elif val == 'F': return 'background-color: #FECDD3; color: #991B1B; font-weight: bold;'
                    return ''
                    
                dynamic_total_label = f"Total Patients ({time_filter})"
                if time_filter == "Select Dates...": dynamic_total_label = f"Total Patients ({date_range_str})"
                
                # This line is correct, uses Average Patients
                display_active = active_df[['Facility', 'Grade', 'Uptime %', 'Average Patients', 'Last Sample Date', 'Total Patients']].copy()
                display_active = display_active.rename(columns={'Average Patients': 'Avg / Day', 'Total Patients': dynamic_total_label})
                display_active['Grade'] = display_active['Grade'].apply(grade_emoji)
                styled_active = display_active.style.map(style_grade_local, subset=['Grade'])
                
                st.dataframe(styled_active, use_container_width=True, hide_index=True, column_config={
                    "Uptime %": st.column_config.NumberColumn("Uptime %", format="%.1f%%"),
                    "Avg / Day": st.column_config.NumberColumn("Avg / Day", format="%.1f"),
                    "Last Sample Date": st.column_config.TextColumn("Last Sample Date", width="medium"),
                    dynamic_total_label: st.column_config.NumberColumn(dynamic_total_label, format="%d")
                })

        with sub_tab3:
            inactive_df = plot_df[plot_df['Total Patients'] == 0].copy()
            if inactive_df.empty:
                st.success("✅ No inactive spokes in this district! All facilities are reporting.")
            else:
                is_pending = stats['num_days'] == 0
                inactive_df['Status'] = 'Pending Launch' if is_pending else 'Operational'
                text_records = stats.get('text_records', [])
                def get_reason(row):
                    if is_pending: return "Awaiting Launch"
                    fac_texts = [t for t in text_records if t['Facility'] == row[facility_col]]
                    if fac_texts: return fac_texts[-1]['Raw_Note']
                    return "Unknown / No Note"
                inactive_df['Primary Reason'] = inactive_df.apply(get_reason, axis=1).apply(format_reason)
                inactive_df = inactive_df.sort_values(by=['Status', facility_col]).reset_index(drop=True)
                
                display_inactive = inactive_df[['Facility', 'Status', 'Last Sample Date', 'Primary Reason']].copy()
                styled_inactive = display_inactive.style.map(style_reason, subset=['Primary Reason'])
                
                st.dataframe(styled_inactive, use_container_width=True, hide_index=True, column_config={
                    "Facility": st.column_config.TextColumn("Facility", width="large"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "Last Sample Date": st.column_config.TextColumn("Last Sample Date", width="medium"),
                    "Primary Reason": st.column_config.TextColumn("Primary Reason", width="large"),
                })
                st.info("💡 Tip: 'Pending Launch' means the facility infrastructure isn't ready. 'Operational' means the facility exists but failed to report patients.")

    with d_tab4:
        st.markdown("<h4 style='color:#0F172A; margin-bottom:10px;'>📍 Hub Logistics & Distance Mapping</h4>", unsafe_allow_html=True)
        dist_col = find_distance_column(df_raw)
        
        if dist_col:
            dist_data = df_raw[[facility_col, dist_col]].copy()
            dist_data.columns = ['Facility', 'Raw_Distance']
            
            def clean_distance(val):
                if pd.isna(val): return None
                s = str(val).strip().replace(' ', '')
                s = re.sub(r'^\.', '', s)
                try: return float(s)
                except ValueError: return DISTANCE_FALLBACK.get(str(val).strip(), None)
                    
            dist_data['Distance'] = dist_data['Raw_Distance'].apply(clean_distance)
            polar_df = pd.merge(scorecard[[facility_col, 'Grade', 'Uptime %', 'Average Patients']], 
                                dist_data[['Facility', 'Distance']], left_on=facility_col, right_on='Facility')
            
            valid_polar_df = polar_df.dropna(subset=['Distance']).copy()
            missing_polar_df = polar_df[polar_df['Distance'].isna()]
            
            if not valid_polar_df.empty:
                valid_polar_df['Display_Name'] = valid_polar_df[facility_col].apply(lambda x: x if len(x) <= 28 else x[:25] + "...")
                
                st.markdown(f"**Hub Center:** {selected_hub_zm}")
                st.caption("Bar length represents distance from Hub (km). Hover for grade and performance details.")
                
                fig_polar = px.bar_polar(valid_polar_df, r="Distance", theta="Display_Name", 
                                         color_discrete_sequence=['#06B6D4'],
                                         hover_data={"Distance": ":.1f", "Uptime %": ":.1f", "Average Patients": ":.1f", "Grade": True, facility_col: True, "Display_Name": False})
                fig_polar.update_traces(marker_line_color='#0F172A', marker_line_width=1, opacity=0.9)
                
                polar_layout = PLOTLY_LAYOUT.copy()
                polar_layout.update(dict(
                    template="plotly_white", height=750, showlegend=False,
                    margin=dict(l=40, r=40, t=80, b=40),
                    polar=dict(bargap=0.5, radialaxis=dict(visible=False, range=[0, valid_polar_df['Distance'].max() + 5], gridcolor='#CBD5E1'),
                               angularaxis=dict(gridcolor='#CBD5E1', tickfont=dict(size=11, color="#1E293B", weight="bold")),
                               bgcolor='rgba(241, 245, 249, 0.5)')
                ))
                fig_polar.update_layout(**polar_layout)
                fig_polar.add_annotation(x=0.5, y=0.5, text="<b>HUB</b>", showarrow=False,
                                         font=dict(size=14, color="#FFFFFF"), bgcolor="#06B6D4",
                                         borderpad=8, bordercolor="#FFFFFF", borderwidth=2)
                st.plotly_chart(fig_polar, use_container_width=True)
            else:
                st.warning("⚠️ No valid distance data available for this district.")
            
            if not missing_polar_df.empty:
                st.warning(f"**Note:** Distance data is missing or unreadable for {len(missing_polar_df)} facilities. They have been omitted from the chart above to prevent false data.")
                with st.expander("View omitted facilities"):
                    st.write(", ".join(missing_polar_df[facility_col].tolist()))
        else:
            st.warning("⚠️ The distance column could not be found in this district's sheet. Cannot render the Hub Logistics chart.")

# ==============================================================================
# VIEW: STATE VIEW
# ==============================================================================
elif view_mode == "State View":
    st.markdown("""
    <div class="page-header-container">
        <div class="page-icon-container page-icon-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="page-icon"><path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11m16-11v11M8 14v3m4-3v3m4-3v3"></path></svg>
        </div>
        <div>
            <div class="page-title-text">Bihar State Master View</div>
            <div class="page-subtitle-text">Statewide operational summary and district performance</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("Loading State Data..."):
        state_df = calculate_all_districts(tuple(available_sheets), file_bytes, time_filter, start_date, end_date)
        
    if not state_df.empty:
        total_active = state_df['Active Spokes'].sum()
        total_facilities = TOTAL_SPOKES 
        reporting_districts = state_df[state_df['Days Reported'] > 0]
        avg_state_uptime = round(reporting_districts['Uptime %'].mean(), 1) if not reporting_districts.empty else 0.0
        
        st.markdown(f'''
        <div class="metric-grid" style="grid-template-columns: repeat(2, 1fr);">
            <div class="metric-card">
                <div class="metric-label" title="Total number of currently active facilities.">Active Spokes ({time_filter})</div>
                <div class="metric-value">{total_active} <span class="metric-sub">/ {total_facilities} Total</span></div>
            </div>
            <div class="metric-card">
                <div class="metric-label" title="The average uptime across all active districts.">Statewide Avg Uptime (Active Districts)</div>
                <div class="metric-value">{avg_state_uptime}%</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        s_tab1, s_tab2, s_tab3 = st.tabs(["District Leaderboard", "ZM Leaderboard", "District vs District"])
        
        with s_tab1:
            c1, c2 = st.columns(2)
            with c1: state_metric_label = st.radio("Rank & Compare by:", ["Total Patient Count", "Weighted Avg", "Uptime %"], horizontal=True)
            with c2: state_sort_order = st.radio("Sort Order:", ["Descending", "Ascending"], horizontal=True)
                
            state_metric_col = {"Total Patient Count": "Total Patients", "Weighted Avg": "Weighted Avg", "Uptime %": "Uptime %"}[state_metric_label]
            
            lb_df = state_df.copy()
            if state_metric_col == "Weighted Avg":
                lb_df = lb_df[lb_df['Days Reported'] >= 7]
                st.caption("⚠️ Districts with less than 7 days of data are hidden from ranking to ensure fair comparison.")
            
            is_ascending = (state_sort_order == "Ascending")
            lb_df = lb_df.sort_values(state_metric_col, ascending=is_ascending).reset_index(drop=True)
            lb_df['Rank'] = lb_df.index + 1
            
            def medal(r): return "🥇" if r == 1 else "🥈" if r == 2 else "🥉" if r == 3 else ""
            if not is_ascending:
                lb_df['District'] = lb_df.apply(lambda row: f"{medal(row['Rank'])} {row['District']}".strip(), axis=1)
            
            total_row = pd.DataFrame([{
                'Rank': '', 'District': '🏆 STATE TOTAL', 'Total Patients': state_df['Total Patients'].sum(),
                'Weighted Avg': '', 'Uptime %': None, 'Facilities': TOTAL_SPOKES,
                'Active Spokes': state_df['Active Spokes'].sum(), 'Days Reported': None
            }])
            lb_df = pd.concat([lb_df, total_row], ignore_index=True)
            
            display_cols = ['Rank', 'District', 'Total Patients', 'Weighted Avg', 'Uptime %', 'Facilities', 'Active Spokes']
            st.dataframe(lb_df[display_cols], use_container_width=True, hide_index=True, column_config={"Uptime %": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100)})
            
            buf_state = io.BytesIO()
            with pd.ExcelWriter(buf_state, engine='openpyxl') as writer:
                lb_df.to_excel(writer, index=False, sheet_name='Leaderboard')
            st.download_button("📥 Download Leaderboard", data=buf_state.getvalue(), file_name="State_Leaderboard.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            
        with s_tab2:
            zm_metric = st.radio("Rank ZMs by:", ["Uptime %", "Weighted Avg", "Total Patients"], horizontal=True, key="zm_lb_metric")
            cur_zm = _zm_aggregates(state_df)
            
            prev_zm = None
            if time_filter != "Full History":
                try:
                    if time_filter == "Select Dates..." and start_date and end_date:
                        span = (end_date - start_date).days + 1
                        prev_end = start_date - timedelta(days=1)
                        prev_start = prev_end - timedelta(days=span - 1)
                        prev_state_df = calculate_all_districts(
                            tuple(available_sheets), file_bytes, "Select Dates...",
                            prev_start, prev_end, window_offset=0
                        )
                    else:
                        prev_state_df = calculate_all_districts(
                            tuple(available_sheets), file_bytes, time_filter,
                            None, None, window_offset=1
                        )
                    prev_zm = _zm_aggregates(prev_state_df) if not prev_state_df.empty else {}
                except Exception:
                    prev_zm = None
            
            if not cur_zm:
                st.info("No ZM data available for the selected period.")
            else:
                cur_sorted = sorted(cur_zm.items(), key=lambda kv: kv[1][zm_metric], reverse=True)
                cur_rank = {zm: i+1 for i, (zm, _) in enumerate(cur_sorted)}
                prev_rank = {}
                if prev_zm:
                    prev_sorted = sorted(prev_zm.items(), key=lambda kv: kv[1][zm_metric], reverse=True)
                    prev_rank = {zm: i+1 for i, (zm, _) in enumerate(prev_sorted)}
                
                rows = []
                for zm, m in cur_zm.items():
                    cur_v = m[zm_metric]
                    prev_v = prev_zm.get(zm, {}).get(zm_metric) if prev_zm else None
                    
                    if prev_rank.get(zm):
                        rd = prev_rank[zm] - cur_rank[zm]
                        rank_delta = f"↑{rd}" if rd > 0 else (f"↓{abs(rd)}" if rd < 0 else "—")
                    else:
                        rank_delta = "—"
                    
                    if prev_v is None:
                        trend = "—"
                    elif prev_v == 0 and cur_v == 0:
                        trend = "⚪ 0.0%"
                    elif prev_v == 0 and cur_v > 0:
                        trend = "🟢 NEW"
                    else:
                        pct = (cur_v - prev_v) / prev_v * 100
                        if pct > 0.05: trend = f"🟢 +{pct:.1f}%"
                        elif pct < -0.05: trend = f"🔴 {pct:.1f}%"
                        else: trend = "⚪ 0.0%"
                    
                    rows.append({
                        'Rank': cur_rank[zm],
                        'ZM': zm,
                        'Districts': m['Districts'],
                        'Total Patients': m['Total Patients'],
                        'Weighted Avg': m['Weighted Avg'],
                        'Uptime %': m['Uptime %'],
                        'Active Spokes': m['Active Spokes'],
                        'Total Spokes': m['Total Spokes'],
                        'Rank Δ': rank_delta,
                        'Trend': trend,
                    })
                
                zm_lb = pd.DataFrame(rows).sort_values('Rank').reset_index(drop=True)
                
                if prev_zm is None:
                    st.caption("ℹ️ Trend arrows require a comparison period. Select 'Past Week', 'Past 2 Weeks', 'Past Month', or 'Select Dates...' to enable.")
                
                st.dataframe(
                    zm_lb, use_container_width=True, hide_index=True,
                    column_config={
                        "Uptime %": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
                        "Total Patients": st.column_config.NumberColumn(format="%d"),
                        "Weighted Avg": st.column_config.NumberColumn(format="%.1f"),
                        "Rank Δ": st.column_config.TextColumn("Rank Δ", width="small"),
                        "Trend": st.column_config.TextColumn("Trend", width="medium"),
                    }
                )

        with s_tab3:
            col_empty1, ca, cb, col_empty2 = st.columns([1, 2, 2, 1])
            with ca: district_a_display = st.selectbox("District A", _DISPLAY_DISTRICTS, index=0, key='cmp_a')
            with cb: district_b_display = st.selectbox("District B", _DISPLAY_DISTRICTS, index=min(1, len(_DISPLAY_DISTRICTS) - 1), key='cmp_b')
            
            district_a_sheet = _DISPLAY_TO_SHEET.get(district_a_display, district_a_display)
            district_b_sheet = _DISPLAY_TO_SHEET.get(district_b_display, district_b_display)
            
            if district_a_sheet and district_b_sheet:
                df_a = read_sheet_robust(xls, district_a_sheet); df_b = read_sheet_robust(xls, district_b_sheet)
                pa, ra, sa = process_district_df(df_a, time_filter, start_date, end_date)
                pb, rb, sb = process_district_df(df_b, time_filter, start_date, end_date)
                
                if pa is None or pb is None: st.error("Could not process one of the selected districts.")
                else:
                    a_uptime = calc_uptime(sa); b_uptime = calc_uptime(sb)

                    def get_style(v1, v2):
                        if v1 > v2: return "font-weight: 800; color: #0F172A; font-size: 1.15rem;"
                        if v2 > v1: return "font-weight: 500; color: #64748B; font-size: 1rem;"
                        return "font-weight: 700; color: #0F172A; font-size: 1rem;"

                    col1, col2 = st.columns(2)
                    with col1: 
                        st.markdown(f'''
                        <div class="battle-card battle-card-blue">
                            <div class="battle-title" style="color: #06B6D4;">{district_a_display}</div>
                            <div class="battle-row"><span>Total Patients</span> <span style="{get_style(sa['total'], sb['total'])}">{sa['total']:,}</span></div>
                            <div class="battle-row"><span>Weighted Avg / Day</span> <span style="{get_style(sa['weighted_avg'], sb['weighted_avg'])}">{sa['weighted_avg']}</span></div>
                            <div class="battle-row"><span>Facility Uptime</span> <span style="{get_style(a_uptime, b_uptime)}">{a_uptime}%</span></div>
                            <div class="battle-row"><span>Total Spokes</span> <span style="{get_style(sa['total_absolute_facilities'], sb['total_absolute_facilities'])}">{sa['total_absolute_facilities']}</span></div>
                        </div>
                        ''', unsafe_allow_html=True)
                    
                    with col2: 
                        st.markdown(f'''
                        <div class="battle-card battle-card-red">
                            <div class="battle-title" style="color: #F43F5E;">{district_b_display}</div>
                            <div class="battle-row"><span>Total Patients</span> <span style="{get_style(sb['total'], sa['total'])}">{sb['total']:,}</span></div>
                            <div class="battle-row"><span>Weighted Avg / Day</span> <span style="{get_style(sb['weighted_avg'], sa['weighted_avg'])}">{sb['weighted_avg']}</span></div>
                            <div class="battle-row"><span>Facility Uptime</span> <span style="{get_style(b_uptime, a_uptime)}">{b_uptime}%</span></div>
                            <div class="battle-row"><span>Total Spokes</span> <span style="{get_style(sb['total_absolute_facilities'], sa['total_absolute_facilities'])}">{sb['total_absolute_facilities']}</span></div>
                        </div>
                        ''', unsafe_allow_html=True)
                    
                    st.markdown("#### Daily Patient Trend — Overlaid")
                    
                    a_obj_to_col = {v: k for k, v in sa.get('active_date_map', {}).items()}
                    b_obj_to_col = {v: k for k, v in sb.get('active_date_map', {}).items()}
                    all_dates_objs = sorted(set(a_obj_to_col.keys()) | set(b_obj_to_col.keys()))
                    
                    def get_trend(p, obj_to_col, name, all_dates_objs):
                        rows = []
                        for dt in all_dates_objs:
                            col = obj_to_col.get(dt)
                            if col and col in p.columns:
                                v = pd.to_numeric(p[col], errors='coerce').fillna(0).sum()
                            else:
                                v = None
                            rows.append({'Date': dt, 'Patients': v, 'District': name})
                        return pd.DataFrame(rows)
                        
                    combined = pd.concat([
                        get_trend(pa, a_obj_to_col, district_a_display, all_dates_objs),
                        get_trend(pb, b_obj_to_col, district_b_display, all_dates_objs)
                    ])
                    fig_c = px.line(combined, x='Date', y='Patients', color='District', markers=True, color_discrete_map={district_a_display: '#06B6D4', district_b_display: '#F43F5E'})
                    
                    cmp_layout = PLOTLY_LAYOUT.copy()
                    cmp_layout.update(dict(
                        height=350, margin=dict(l=10, r=10, t=40, b=40),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#CBD5E1', tickformat="%d %b"), 
                        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='#CBD5E1')
                    ))
                    fig_c.update_layout(**cmp_layout)
                    st.plotly_chart(fig_c, use_container_width=True)
    else:
        st.warning("No district data available for the selected time range.")

# ==============================================================================
# VIEW: ZM VIEW
# ==============================================================================
elif view_mode == "ZM View":
    st.markdown("""
    <div class="page-header-container">
        <div class="page-icon-container page-icon-zm">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="page-icon"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><path d="M9 12l2 2 4-4"></path></svg>
        </div>
        <div>
            <div class="page-title-text">Zone Manager View</div>
            <div class="page-subtitle-text">Drill down into specific Zonal performance</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    _zm_opts = sorted(ZM_DATA.keys())
    if 'zm_view_target' in st.session_state:
        _target = st.session_state.pop('zm_view_target')
        if _target in _zm_opts:
            st.session_state['zm_sel'] = _target
        
    selected_zm = st.selectbox("Select Zone Manager", _zm_opts, key='zm_sel')
    zm_districts = list(ZM_DATA[selected_zm].keys())
    
    with st.spinner(f"Loading data for {selected_zm}..."):
        state_df = calculate_all_districts(tuple(available_sheets), file_bytes, time_filter, start_date, end_date)
        all_fac_df = get_all_facility_data(tuple(available_sheets), file_bytes, time_filter, start_date, end_date)
        
    if not state_df.empty and not all_fac_df.empty:
        zm_df = state_df[state_df['District'].isin(zm_districts)].copy()
        zm_fac_df = all_fac_df[all_fac_df['District'].isin(zm_districts)].copy()
        
        if zm_df.empty:
            st.warning(f"No data available for {selected_zm}'s districts in the selected time range.")
        else:
            total_patients = zm_df['Total Patients'].sum()
            total_active = zm_df['Active Spokes'].sum()
            total_facilities = zm_df['Facilities'].sum()
            pending_zm = zm_fac_df[zm_fac_df['Status'] == 'Pending Launch']
            total_pending = len(pending_zm)
            total_operational = total_facilities - total_pending
            
            zone_fac_days = int((zm_df['Facilities'] * zm_df['Days Reported']).sum())
            zone_weighted_avg = round(total_patients / zone_fac_days, 1) if zone_fac_days > 0 else 0.0
            
            avg_uptime = round(zm_df['Uptime %'].mean(), 1)
            
            sub_districts = ['Barh', 'Danapur']
            sub_count = len([d for d in zm_districts if d in sub_districts])
            dist_count = len(zm_districts) - sub_count
            total_units = len(zm_districts)
            breakdown_text = f"{dist_count} Districts"
            if sub_count > 0:
                breakdown_text += f" & {sub_count} Sub-districts"
            
            st.markdown(f'''
            <div class="metric-grid" style="grid-template-columns: repeat(4, 1fr);">
                <div class="metric-card">
                    <div class="metric-label">Coverage</div>
                    <div class="metric-value">{total_units}</div>
                    <div class="metric-sub" style="font-size: 13px; margin-top: 6px;">{breakdown_text}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Weighted Avg / Day</div>
                    <div class="metric-value">{zone_weighted_avg}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Active Spokes</div>
                    <div class="metric-value">{total_active} <span class="metric-sub">/ {total_operational} Operational</span></div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Zone Uptime</div>
                    <div class="metric-value">{avg_uptime}%</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            op_failures_zm = zm_fac_df[(zm_fac_df['Total Patients'] == 0) & (zm_fac_df['Status'] == 'Operational')]
            
            zm_tab1, zm_tab2, zm_tab3, zm_tab4 = st.tabs([
                "📊 Zone Summary", 
                f"🟢 Active Spokes ({total_active})", 
                f"🔴 Operational Failures ({len(op_failures_zm)})",
                f"🚧 Pending Launch ({total_pending})"
            ])
            
            with zm_tab1:
                col_sort, _ = st.columns([1.5, 3.5])
                with col_sort:
                    zm_sort_order = st.radio("Sort Order:", ["Descending", "Ascending"], horizontal=True, key="zm_sort")
                
                st.markdown(f"<h4 style='color:#0F172A; margin-top:16px; margin-bottom:10px;'>District Breakdown</h4>", unsafe_allow_html=True)
                display_cols = ['District', 'Total Patients', 'Weighted Avg', 'Uptime %', 'Facilities', 'Active Spokes']
                is_ascending = (zm_sort_order == "Ascending")
                display_df = zm_df[display_cols].sort_values(by=['Uptime %', 'Weighted Avg'], ascending=[is_ascending, is_ascending]).reset_index(drop=True)
                
                st.dataframe(display_df, use_container_width=True, hide_index=True, column_config={
                    "Uptime %": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
                    "Total Patients": st.column_config.NumberColumn(format="%d"),
                    "Weighted Avg": st.column_config.NumberColumn(format="%.1f")
                })
                
                st.markdown(f"<h4 style='color:#0F172A; margin-top:24px; margin-bottom:10px;'>District Comparison</h4>", unsafe_allow_html=True)
                fig_zm = px.bar(display_df, x='District', y='Total Patients', color='Uptime %', color_continuous_scale='Teal', text='Total Patients')
                fig_zm.update_traces(texttemplate='%{text:,}', textposition='outside', marker_line_color='#0F172A', marker_line_width=1)
                
                zm_layout = PLOTLY_LAYOUT.copy()
                zm_layout.update(dict(
                    height=400,
                    xaxis=dict(showgrid=False, tickfont=dict(size=13, color="#1E293B", weight="bold")),
                    yaxis=dict(showgrid=True, gridwidth=1, gridcolor='#CBD5E1', title="Total Patients")
                ))
                fig_zm.update_layout(**zm_layout)
                st.plotly_chart(fig_zm, use_container_width=True)

            with zm_tab2:
                active_zm = zm_fac_df[zm_fac_df['Total Patients'] > 0].copy()
                if active_zm.empty:
                    st.info("No active spokes in this zone for the selected time range.")
                else:
                    active_zm = active_zm.sort_values(by=['Uptime %', 'Total Patients'], ascending=[False, False]).reset_index(drop=True)
                    
                    def style_grade(val):
                        if val in ['A', 'B']: return 'background-color: #CCFBF1; color: #0F766E; font-weight: bold;'
                        elif val in ['C', 'D']: return 'background-color: #FEF08A; color: #854D0E; font-weight: bold;'
                        elif val == 'F': return 'background-color: #FECDD3; color: #991B1B; font-weight: bold;'
                        return ''
                        
                    dynamic_total_label = f"Total Patients ({time_filter})"
                    if time_filter == "Select Dates...": dynamic_total_label = f"Total Patients ({date_range_str})"
                    
                    display_active = active_zm[['District', 'Facility', 'Grade', 'Uptime %', 'Avg / Day', 'Last Sample Date', 'Total Patients']].copy()
                    display_active = display_active.rename(columns={'Total Patients': dynamic_total_label})
                    styled_active = display_active.style.map(style_grade, subset=['Grade'])
                    
                    st.dataframe(styled_active, use_container_width=True, hide_index=True, column_config={
                        "Uptime %": st.column_config.NumberColumn("Uptime %", format="%.1f%%"),
                        "Avg / Day": st.column_config.NumberColumn("Avg / Day", format="%.1f"),
                        "Last Sample Date": st.column_config.TextColumn("Last Sample Date", width="medium"),
                        dynamic_total_label: st.column_config.NumberColumn(dynamic_total_label, format="%d")
                    })

            with zm_tab3:
                if op_failures_zm.empty:
                    st.success("✅ Excellent! No operational failures in this zone.")
                else:
                    op_failures_zm = op_failures_zm.sort_values(by=['District', 'Facility']).reset_index(drop=True)
                    op_failures_zm['Primary Reason'] = op_failures_zm['Primary Reason'].apply(format_reason)
                    
                    display_inactive = op_failures_zm[['District', 'Facility', 'Last Sample Date', 'Primary Reason']].copy()
                    styled_inactive = display_inactive.style.map(style_reason, subset=['Primary Reason'])
                    
                    st.dataframe(styled_inactive, use_container_width=True, hide_index=True, column_config={
                        "District": st.column_config.TextColumn("District", width="medium"),
                        "Facility": st.column_config.TextColumn("Facility Name", width="large"),
                        "Last Sample Date": st.column_config.TextColumn("Last Sample Date", width="medium"),
                        "Primary Reason": st.column_config.TextColumn("Primary Reason", width="large"),
                    })
                    
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                        display_inactive.to_excel(writer, index=False, sheet_name='Follow-Up List')
                    st.download_button(
                        label="🚨 Download ZM Follow-up List", data=buf.getvalue(),
                        file_name=f"{selected_zm}_Followup.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True
                    )

            with zm_tab4:
                if pending_zm.empty:
                    st.success("✅ All facilities in this zone have launched!")
                else:
                    pending_zm = pending_zm.sort_values(by=['District', 'Facility']).reset_index(drop=True)
                    
                    display_pending = pending_zm[['District', 'Facility', 'Last Sample Date', 'Primary Reason']].copy()
                    styled_pending = display_pending.style.map(style_reason, subset=['Primary Reason'])
                    
                    st.dataframe(styled_pending, use_container_width=True, hide_index=True, column_config={
                        "District": st.column_config.TextColumn("District", width="medium"),
                        "Facility": st.column_config.TextColumn("Facility Name", width="large"),
                        "Last Sample Date": st.column_config.TextColumn("Last Sample Date", width="medium"),
                        "Primary Reason": st.column_config.TextColumn("Primary Reason", width="large"),
                    })
                    st.info("These facilities will automatically move to 'Operational' as soon as their first data column is added.")
    else:
        st.warning("Could not load statewide or facility data. Try refreshing, or check the Google Sheet connection.")

# ==============================================================================
# VIEW: ACTIVE SPOKES
# ==============================================================================
elif view_mode == "Active Spokes":
    st.markdown("""
    <div class="page-header-container">
        <div class="page-icon-container page-icon-active">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="page-icon"><polyline points="20 6 9 17 4 12"></polyline></svg>
        </div>
        <div>
            <div class="page-title-text">Active Spokes Tracker</div>
            <div class="page-subtitle-text">Facilities currently seeing patients</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("Loading all active facilities..."):
        all_fac_df = get_all_facility_data(tuple(available_sheets), file_bytes, time_filter, start_date, end_date)
        
    if not all_fac_df.empty:
        active_df = all_fac_df[all_fac_df['Total Patients'] > 0].copy()
        
        # --- TOP LAYOUT: Filters & Download ---
        col_dist, col_grade = st.columns(2)
        with col_dist:
            dist_filter = st.multiselect("Filter by District", sorted(active_df['District'].unique()), default=[])
        with col_grade:
            grade_filter = st.multiselect("Filter by Grade", ["A", "B", "C", "D", "F"], default=[])
            
        if dist_filter: active_df = active_df[active_df['District'].isin(dist_filter)]
        if grade_filter: active_df = active_df[active_df['Grade'].isin(grade_filter)]
        
        active_df = active_df.sort_values(by=['Uptime %', 'Total Patients'], ascending=[False, False]).reset_index(drop=True)
        
        col_metric, col_dl = st.columns([3, 1], vertical_alignment="bottom")
        
        with col_metric:
            st.markdown(f'''
            <div class="metric-card" style="border-top: 4px solid #14B8A6; padding: 16px; margin-bottom: 0;">
                <div class="metric-label">Active Spokes Shown</div>
                <div class="metric-value" style="color:#14B8A6;">{len(active_df)} <span class="metric-sub" style="font-size: 14px;">/ {TOTAL_SPOKES} Total</span></div>
            </div>
            ''', unsafe_allow_html=True)
            
        with col_dl:
            def style_grade(val):
                if val in ['A', 'B']: return 'background-color: #CCFBF1; color: #0F766E; font-weight: bold;'
                elif val in ['C', 'D']: return 'background-color: #FEF08A; color: #854D0E; font-weight: bold;'
                elif val == 'F': return 'background-color: #FECDD3; color: #991B1B; font-weight: bold;'
                return ''
                
            dynamic_total_label = f"Total Patients ({time_filter})"
            if time_filter == "Select Dates...": dynamic_total_label = f"Total Patients ({date_range_str})"

            display_active = active_df[['District', 'Facility', 'Grade', 'Uptime %', 'Avg / Day', 'Last Sample Date', 'Total Patients']].copy()
            display_active = display_active.rename(columns={'Total Patients': dynamic_total_label})
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                display_active.to_excel(writer, index=False, sheet_name='Active Spokes')
                
            st.download_button(
                label=f"📥 Download ({len(active_df)})", 
                data=buffer.getvalue(),
                file_name=f"Statewide_Active_Spokes_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                use_container_width=True
            )

        styled_active = display_active.style.map(style_grade, subset=['Grade'])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.dataframe(styled_active, use_container_width=True, hide_index=True, column_config={
            "Uptime %": st.column_config.NumberColumn("Uptime %", format="%.1f%%"),
            "Avg / Day": st.column_config.NumberColumn("Avg / Day", format="%.1f"),
            "Last Sample Date": st.column_config.TextColumn("Last Sample Date", width="medium"),
            dynamic_total_label: st.column_config.NumberColumn(dynamic_total_label, format="%d")
        })
        
    else:
        st.warning("Could not load facility data.")

# ==============================================================================
# VIEW: ZERO-SAMPLE TRACKER
# ==============================================================================
else:
    st.markdown("""
    <div class="page-header-container">
        <div class="page-icon-container page-icon-warning">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="page-icon"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
        </div>
        <div>
            <div class="page-title-text">Statewide Zero-Sample Tracker</div>
            <div class="page-subtitle-text">Operational failures and pending infrastructure launches</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("Scanning all districts for inactive facilities..."):
        all_fac_df = get_all_facility_data(tuple(available_sheets), file_bytes, time_filter, start_date, end_date)
        
    if not all_fac_df.empty:
        inactive_df = all_fac_df[all_fac_df['Total Patients'] == 0].copy()
        op_failures = inactive_df[inactive_df['Status'] == 'Operational'].reset_index(drop=True)
        pending_launch = inactive_df[inactive_df['Status'] == 'Pending Launch'].reset_index(drop=True)
        
        col_card1, col_card2 = st.columns(2)
        with col_card1:
            st.markdown(f'''
            <div class="metric-card" style="border-top: 4px solid #F43F5E; padding: 16px; margin-bottom: 16px;">
                <div class="metric-label" title="Facilities that exist but failed to report patients.">Operational Failures</div>
                <div class="metric-value" style="color:#F43F5E;">{len(op_failures)}</div>
                <div class="metric-sub" style="margin-top: 8px;">Requires immediate intervention</div>
            </div>
            ''', unsafe_allow_html=True)
        with col_card2:
            st.markdown(f'''
            <div class="metric-card" style="border-top: 4px solid #94A3B8; padding: 16px; margin-bottom: 16px;">
                <div class="metric-label" title="Facilities that have no data columns yet.">Pending Launch</div>
                <div class="metric-value" style="color:#64748B;">{len(pending_launch)}</div>
                <div class="metric-sub" style="margin-top: 8px;">Awaiting infrastructure readiness</div>
            </div>
            ''', unsafe_allow_html=True)

        if not op_failures.empty:
            st.markdown("<h4 style='color:#0F172A; margin-top:10px; margin-bottom:10px;'>Top Offending Districts (Operational Failures)</h4>", unsafe_allow_html=True)
            district_counts = op_failures['District'].value_counts().head(5).reset_index()
            district_counts.columns = ['District', 'Failures']
            
            fig_off = px.bar(district_counts, x='Failures', y='District', orientation='h', text='Failures')
            fig_off.update_traces(marker_color='#F43F5E', textposition='outside')
            
            off_layout = PLOTLY_LAYOUT.copy()
            off_layout.update(dict(height=250, showlegend=False, xaxis_title="Number of Facilities", yaxis_title="", margin=dict(l=10, r=20, t=20, b=10)))
            fig_off.update_layout(**off_layout)
            st.plotly_chart(fig_off, use_container_width=True)

        z_tab1, z_tab2 = st.tabs([f"🔴 True Operational Failures ({len(op_failures)})", f"🚧 Pending Launch ({len(pending_launch)})"])
        
        with z_tab1:
            if not op_failures.empty:
                col_title, col_dl = st.columns([3, 1], vertical_alignment="bottom")
                with col_dl:
                    buffer1 = io.BytesIO()
                    with pd.ExcelWriter(buffer1, engine='openpyxl') as writer:
                        op_failures.to_excel(writer, index=False, sheet_name='Operational Failures')
                    st.download_button(
                        label=f"📥 Download ({len(op_failures)})", data=buffer1.getvalue(),
                        file_name=f"Statewide_OpFailures_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True
                    )
                
                op_failures['SortDate'] = pd.to_datetime(op_failures['Last Sample Date'], errors='coerce')
                op_failures = op_failures.sort_values(by=['SortDate', 'Last Sample Date'], ascending=[True, True], na_position='first').drop(columns=['SortDate'])
                
                display_tracker = op_failures[['District', 'Facility', 'Last Sample Date', 'Primary Reason']].copy()
                display_tracker['Primary Reason'] = display_tracker['Primary Reason'].apply(format_reason)
                styled_tracker = display_tracker.style.map(style_reason, subset=['Primary Reason'])
                
                st.dataframe(styled_tracker, use_container_width=True, hide_index=True, column_config={
                    "District": st.column_config.TextColumn("District", width="medium"),
                    "Facility": st.column_config.TextColumn("Facility Name", width="large"),
                    "Last Sample Date": st.column_config.TextColumn("Last Sample Date", width="medium"),
                    "Primary Reason": st.column_config.TextColumn("Primary Reason", width="large"),
                })
            else:
                st.success("✅ Excellent! No operational facilities found with 0 patients.")

        with z_tab2:
            if not pending_launch.empty:
                col_title, col_dl = st.columns([3, 1], vertical_alignment="bottom")
                with col_dl:
                    buffer2 = io.BytesIO()
                    with pd.ExcelWriter(buffer2, engine='openpyxl') as writer:
                        pending_launch.to_excel(writer, index=False, sheet_name='Pending Launch')
                    st.download_button(
                        label=f"📥 Download ({len(pending_launch)})", data=buffer2.getvalue(),
                        file_name=f"Statewide_PendingLaunch_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True
                    )

                pending_launch['SortDate'] = pd.to_datetime(pending_launch['Last Sample Date'], errors='coerce')
                pending_launch = pending_launch.sort_values(by=['SortDate', 'Last Sample Date'], ascending=[True, True], na_position='first').drop(columns=['SortDate'])
                
                display_pending = pending_launch[['District', 'Facility', 'Last Sample Date', 'Primary Reason']].copy()
                display_pending['Primary Reason'] = display_pending['Primary Reason'].apply(format_reason)
                styled_pending = display_pending.style.map(style_reason, subset=['Primary Reason'])
                
                st.dataframe(styled_pending, use_container_width=True, hide_index=True, column_config={
                    "District": st.column_config.TextColumn("District", width="medium"),
                    "Facility": st.column_config.TextColumn("Facility Name", width="large"),
                    "Last Sample Date": st.column_config.TextColumn("Last Sample Date", width="medium"),
                    "Primary Reason": st.column_config.TextColumn("Primary Reason", width="large"),
                })
                st.info("These facilities will automatically move to 'Operational' as soon as their first data column is added.")
            else:
                st.success("✅ All facilities have launched!")
    else:
        st.warning("Could not load facility data.")

# --- GLOBAL DEFINITIONS EXPANDER ---
st.markdown("<br><hr style='border-color: #CBD5E1; margin: 40px 0 20px 0;'><br>", unsafe_allow_html=True)
with st.expander("ℹ️ Metric Definitions & Grading System"):
    st.markdown("""
    **📊 Weighted Avg / Day** — *The efficiency score.*
    Total patients divided by *(Total Facilities × Total Days)*. 
    *Why use this?* It prevents a facility that was only open for 1 day with 50 patients from artificially inflating the district's average. It accounts for every facility-day equally.
    
    **⏱️ Uptime %** — *The reliability score.*
    The percentage of days a facility reported more than 0 patients.
    """)
    
    st.info("""
    **Example:**
    *   **Weighted Avg:** 10 facilities report for 5 days (50 total facility-days). They see 100 patients total. The Weighted Avg is **100 ÷ 50 = 2.0**.
    *   **Uptime:** A facility has 10 days of data. They report `0` on 3 days. Their Uptime is **7 ÷ 10 = 70%**.
    """)

    st.markdown("**🏆 Grading System**")
    st.markdown("*Note: A facility must meet **BOTH** the Uptime and Avg Patients requirements to earn the grade. If it fails either one, it drops to the next lowest grade.*")
    
    grade_data = pd.DataFrame({
        "Grade": ["A (Excellent)", "B (Good)", "C (Fair)", "D (Poor)", "F (Critical)"],
        "Uptime Requirement": ["> 85%", "> 70%", "> 50%", "> 30%", "< 30%"],
        "Avg Patients Requirement": ["> 10", "> 5", "> 2", "> 1", "0"]
    })
    
    st.dataframe(grade_data, hide_index=True, use_container_width=True, column_config={
        "Grade": st.column_config.TextColumn("Grade", width="medium"),
        "Uptime Requirement": st.column_config.TextColumn("Uptime Requirement", width="medium"),
        "Avg Patients Requirement": st.column_config.TextColumn("Avg Patients Requirement", width="medium"),
    })
    
    st.info("""
    **Grading Example:**
    If a facility reports every single day (100% Uptime) but only sees **1 patient per day** (Avg 1.0), they get a **D**. They do not get an A, because their patient volume is too low.
    """)