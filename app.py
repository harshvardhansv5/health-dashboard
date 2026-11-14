import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta, datetime
import re
import io
import math
import requests
import unicodedata

# --- CONSTANTS ---
TOTAL_SPOKES = 702 
available_sheets = [] 

# --- GOOGLE SHEETS INTEGRATION ---
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRwjDNp1zjbEXM-a4HYoAErb4ZWyJm9YmbKyTeEOhKOpKx6DAFLUlVPlQEvRP0ll5SUDXYWKlS5F7Gc/pub?output=xlsx"

# --- DISTANCE FALLBACK DICTIONARY ---
DISTANCE_FALLBACK = {}

# --- PAGE SETUP ---
st.set_page_config(page_title="Bihar Health Command", page_icon="🩸", layout="wide", initial_sidebar_state="collapsed")

# --- NEON HUD UI CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Outfit:wght@400;600;800&display=swap');

    /* Global Reset */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Outfit', sans-serif !important;
        background-color: #09090B !important;
    }
    
    /* Hide Sidebar & Header */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    header { display: none !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Typography Overrides */
    h1, h2, h3, h4, h5, h6 { color: #F8FAFC !important; font-weight: 800 !important; letter-spacing: -0.5px !important; }
    p, span, .stMarkdown { color: #94A3B8 !important; }
    .mono { font-family: 'JetBrains Mono', monospace !important; }
    
    /* Neon Colors */
    .neon-cyan { color: #00E5FF !important; text-shadow: 0 0 10px rgba(0, 229, 255, 0.3); }
    .neon-magenta { color: #FF0055 !important; text-shadow: 0 0 10px rgba(255, 0, 85, 0.3); }
    .neon-lime { color: #00FF94 !important; text-shadow: 0 0 10px rgba(0, 255, 148, 0.3); }

    /* Glassmorphism KPI Cards */
    .kpi-card {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 4px 24px -1px rgba(0, 0, 0, 0.5) !important;
        display: flex; flex-direction: column; position: relative; overflow: hidden;
        transition: all 0.3s ease;
    }
    .kpi-card:hover { border-color: rgba(0, 229, 255, 0.4) !important; transform: translateY(-2px); }
    .kpi-card::before {
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 2px;
        background: linear-gradient(90deg, transparent, #00E5FF, transparent);
        opacity: 0.5;
    }
    .kpi-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #64748B !important; font-weight: 800; margin-bottom: 8px; }
    .kpi-value { font-family: 'JetBrains Mono', monospace !important; font-size: 28px; font-weight: 700; color: #FFFFFF !important; line-height: 1; }
    .kpi-sub { font-size: 12px; color: #64748B !important; margin-top: 8px; font-weight: 600; }

    /* HUD Command Bar */
    div[data-testid="stHorizontalBlock"]:has(.hud-header) {
        background: rgba(0, 0, 0, 0.4) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        padding: 12px 24px !important;
        margin-bottom: 24px !important;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.8) !important;
    }
    
    /* Tabs as Tactile Switches */
    button[data-baseweb="tab"] {
        background: transparent !important; color: #64748B !important;
        font-family: 'JetBrains Mono', monospace !important; font-size: 13px !important;
        border: 1px solid transparent !important; border-radius: 8px !important;
        padding: 8px 16px !important; transition: all 0.2s ease !important;
    }
    button[data-baseweb="tab"]:hover { color: #00E5FF !important; }
    button[aria-selected="true"] { 
        background: rgba(0, 229, 255, 0.1) !important; 
        color: #00E5FF !important; 
        border: 1px solid rgba(0, 229, 255, 0.3) !important;
        box-shadow: 0 0 15px rgba(0, 229, 255, 0.2) !important;
    }
    div[data-baseweb="tab-highlight"] { display: none !important; }
    div[data-baseweb="tab-border"] { display: none !important; }

    /* Inputs & Dropdowns */
    div[data-testid="stSelectbox"] div[role="combobox"], div[data-testid="stMultiSelect"] div[role="combobox"] {
        background-color: rgba(255, 255, 255, 0.05) !important; 
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }
    div[data-testid="stSelectbox"] div[role="combobox"] * { color: #F8FAFC !important; font-family: 'JetBrains Mono', monospace !important; font-size: 13px !important; }
    div[data-testid="stSelectbox"] svg { fill: #00E5FF !important; }

    /* Dataframes (Terminal Style) */
    div[data-testid="stDataFrame"] {
        background-color: #09090B !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
    }
    div[data-testid="stDataFrame"] * { 
        font-family: 'JetBrains Mono', monospace !important; 
        color: #F8FAFC !important;
    }
    div[data-testid="stDataFrame"] th {
        background-color: #1E293B !important;
        color: #00E5FF !important;
        border-bottom: 1px solid rgba(0, 229, 255, 0.2) !important;
    }
    [data-testid="stDataFrameColumnMenu"] { display: none !important; }
    
    /* Force progress bars in dataframe to be cyan */
    div[data-testid="stDataFrame"] div[role="progressbar"] > div { background-color: rgba(0, 229, 255, 0.2) !important; }
    div[data-testid="stDataFrame"] div[role="progressbar"] > div > div { background-color: #00E5FF !important; box-shadow: 0 0 10px rgba(0,229,255,0.5) !important; }

    /* ZM Race Track */
    .race-track { margin-bottom: 16px; }
    .race-label { display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #F8FAFC; margin-bottom: 6px; }
    .race-bar-bg { height: 8px; background: rgba(255, 255, 255, 0.05); border-radius: 4px; overflow: hidden; }
    .race-bar-fill { height: 100%; border-radius: 4px; box-shadow: 0 0 10px currentColor; }

    /* Login Override */
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(0, 229, 255, 0.2) !important;
        box-shadow: 0 0 40px rgba(0, 229, 255, 0.1) !important;
        border-radius: 20px !important;
        backdrop-filter: blur(20px) !important;
    }
    div[data-testid="stForm"] h2 { color: #00E5FF !important; font-family: 'Outfit'; }
    div[data-testid="stForm"] p { color: #94A3B8 !important; }
    div[data-testid="stTextInput"] input { background: rgba(0,0,0,0.5) !important; border: 1px solid rgba(255,255,255,0.1) !important; color: #FFF !important; }
    div[data-testid="stFormSubmitButton"] > button { background: #00E5FF !important; color: #000 !important; font-weight: 800 !important; border: none !important; }
</style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION GATE ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("""
            <div style="text-align: center; margin-bottom: 32px;">
                <h2 style="color:#00E5FF !important; font-family: 'JetBrains Mono'; font-size: 24px; letter-spacing: 2px;">SYSTEM ACCESS</h2>
                <p style="color:#64748B !important; font-family: 'JetBrains Mono'; font-size: 12px;">Bihar Health Command Center</p>
            </div>
            """, unsafe_allow_html=True)
            
            pwd = st.text_input("Password", type="password", label_visibility="collapsed")
            submit = st.form_submit_button("AUTHENTICATE", use_container_width=True)
            
        if submit:
            if pwd == "BiharHealth2026!":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("ACCESS DENIED")
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
    "Paras Kumar Jaiswal (Purnia)": {"Araria": ["DH Araria"], "Katihar": ["DH Katihar"], "Kishanganj": ["DH Kishanganj"], "Purnia": ["CHC Krityanand Nagar"]},
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

def get_grade_color(grade):
    return {"A": "#00FF94", "B": "#00E5FF", "C": "#FFD500", "D": "#FF8C00", "F": "#FF0055"}.get(grade, "#FFFFFF")

def style_reason(val):
    if pd.isna(val) or str(val).strip() == '' or str(val) == '-': return 'color: #64748B;'
    val_str = str(val).lower()
    if any(w in val_str for w in ['operational', 'no lt', 'no runner', 'strike', 'breakdown', 'not available', 'locked', 'no sample']):
        return 'background-color: rgba(255, 0, 85, 0.2); color: #FF0055; font-weight: 700; border-radius: 6px; padding: 4px 10px;'
    elif any(w in val_str for w in ['low opd', 'low footfall', 'training', 'come after', 'delay']):
        return 'background-color: rgba(255, 213, 0, 0.2); color: #FFD500; font-weight: 700; border-radius: 6px; padding: 4px 10px;'
    elif 'never reported' in val_str or 'unknown' in val_str or 'awaiting launch' in val_str:
        return 'background-color: rgba(255, 255, 255, 0.05); color: #94A3B8; font-weight: 700; border-radius: 6px; padding: 4px 10px;'
    return 'background-color: rgba(255, 140, 0, 0.2); color: #FF8C00; font-weight: 700; border-radius: 6px; padding: 4px 10px;'

def format_reason(reason):
    if pd.isna(reason): return reason
    acronyms = ['OPD', 'LT', 'CHC', 'PHC', 'UPHC', 'RH', 'SDH', 'DH']
    words = str(reason).split()
    return ' '.join([w if w.upper() in acronyms else w.capitalize() for w in words])

@st.cache_data(ttl=3600, show_spinner="SYNCING WITH SATELLITE...")
def fetch_google_sheet(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except Exception as e:
        st.error(f"SATELLITE UPLINK FAILED: {e}")
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
        if 'distance from hub' in c_str or 'spokes distance' in c_str: return c
    return None

@st.cache_data(show_spinner=False)
def extract_date(col_name):
    dt = pd.NaT
    if isinstance(col_name, pd.Timestamp): dt = col_name
    else:
        s = str(col_name).lower()
        s = s.replace('\xa0', ' ').replace('\u200b', '').replace('\u200e', '')
        s = s.replace('<br>', ' ').replace('<br/>', ' ').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        s = re.sub(r'total number of patients( on)?', '', s)
        s = re.sub(r'\(.*?\)', '', s) 
        s = s.replace('∕', '/').replace('⁄', '/').replace('‐', '-').replace('–', '-').replace('—', '-')
        s = re.sub(r'-+', '-', s)
        s = re.sub(r'\s*([-/.∕⁄‐–—])\s*', r'\1', s)
        s = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', s)
        s = s.strip()
        if not re.search(r'\d{4}', s):
            if re.search(r'\b\d{1,2}[-/\.\s][a-z]{3}\b', s) or re.search(r'\b\d{1,2}[-/\.\s]\d{1,2}\b', s):
                s = s + " " + str(pd.Timestamp.today().year)
        match = re.search(r'(\d{4}[-/\.\s]\d{1,2}[-/\.\s]\d{1,2})|(\d{1,2}[-/\.\s]\d{1,2}[-/\.\s]\d{2,4})|(\d{1,2}[-/\.\s][a-z]{3}[-/\.\s]\d{2,4})', s)
        if match:
            raw_date = match.group(0)
            if re.match(r'^\d{4}/\d{4}$', raw_date): raw_date = raw_date[:2] + '/' + raw_date[2:]
            try: dt = pd.to_datetime(raw_date, dayfirst=True, errors='coerce')
            except: pass
    if pd.notna(dt) and dt > pd.Timestamp.today().normalize(): return pd.NaT
    return dt

def find_date_columns(df):
    return [c for c in df.columns if pd.notna(extract_date(c))]

def get_facility_mask(df, facility_col):
    mask = df[facility_col].notna()
    mask &= ~df[facility_col].astype(str).str.upper().str.contains('TOTAL', na=False)
    mask &= ~df[facility_col].astype(str).str.upper().str.contains('JAIL', na=False)
    mask &= ~df[facility_col].astype(str).str.strip().str.lower().isin(['nan', 'none', ''])
    mask &= ~df[facility_col].astype(str).str.lower().str.contains('prepared|signature|verified|report', na=False)
    mask &= df[facility_col].astype(str).str.contains('[a-zA-Z]', regex=True, na=False)
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
            'total': 0, 'weighted_avg': 0.0, 'zero_days': 0, 'num_facilities': len(df), 'num_days': 0, 
            'facility_col': facility_col, 'active_date_cols': [], 'active_date_map': {},
            'text_records': [], 'active_facilities': 0, 'total_absolute_facilities': total_absolute_facilities
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
        if len(cols) > 1: clean_df[d] = df[cols].apply(pd.to_numeric, errors='coerce').fillna(0).max(axis=1)
        else: clean_df[d] = pd.to_numeric(df[cols[0]], errors='coerce').fillna(0)
            
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
            'total': 0, 'weighted_avg': 0.0, 'zero_days': 0, 'num_facilities': len(df), 'num_days': 0, 
            'facility_col': facility_col, 'active_date_cols': [], 'active_date_map': {},
            'text_records': [], 'active_facilities': 0, 'total_absolute_facilities': total_absolute_facilities
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
        if window_offset > 0 or time_filter == "Select Dates...":
            plot_df = df[[facility_col]].copy()
            plot_df['Total Patients'] = 0
            plot_df['Average Patients'] = 0.0
            plot_df['Zero Days'] = 0
            plot_df['Uptime %'] = 0.0
            plot_df['Last Sample Date'] = "Never Reported"
            return plot_df, None, {
                'total': 0, 'weighted_avg': 0.0, 'zero_days': 0, 'num_facilities': len(df), 'num_days': 0, 
                'facility_col': facility_col, 'active_date_cols': [], 'active_date_map': {},
                'text_records': [], 'active_facilities': 0, 'total_absolute_facilities': total_absolute_facilities
            }
        active_dates = sorted_dates

    text_records = []
    def is_text_note(x):
        if not isinstance(x, str): return False
        v = x.strip().lower()
        if v in ['', 'nan', 'none', '0', '0.0']: return False
        try: float(v); return False
        except ValueError: return True
            
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
    
    max_allowed_date = active_dates[-1] if active_dates else (sorted_dates[-1] if sorted_dates else None)
    def get_last_sample_date(row):
        if max_allowed_date is None: return "Never Reported"
        for d in reversed(sorted_dates):
            if d > max_allowed_date: continue
            if row[d] > 0: return d.strftime('%d %b %Y')
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
        
    col_map = {d: d.strftime('%d %b %y') for d in active_dates}
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

@st.cache_data(show_spinner=False)
def calculate_all_districts(sheet_names_tuple, file_bytes, time_filter, start_date=None, end_date=None, window_offset=0, _cache_buster="v86.0"):
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    data = []
    for sheet in sheet_names_tuple:
        try:
            sdf = read_sheet_robust(xls, sheet)
            _, _, s = process_district_df(sdf, time_filter, start_date, end_date, window_offset=window_offset)
            if s:
                display_name = REVERSE_DISTRICT_MAP.get(sheet, sheet)
                data.append({
                    'District': display_name, 'Total Patients': s['total'], 'Weighted Avg': s['weighted_avg'], 
                    'Uptime %': calc_uptime(s), 'Facilities': s['total_absolute_facilities'],
                    'Active Spokes': s['active_facilities'], 'Days Reported': s['num_days']
                })
        except Exception: pass
    return pd.DataFrame(data)

@st.cache_data(show_spinner=False)
def get_all_facility_data(sheet_names_tuple, file_bytes, time_filter, start_date=None, end_date=None, _cache_buster="v86.0"):
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
                'District': REVERSE_DISTRICT_MAP.get(sheet, sheet), 'Facility': plot_df[fac_col],
                'Total Patients': plot_df['Total Patients'], 'Avg / Day': plot_df['Average Patients'],
                'Uptime %': plot_df['Uptime %'], 'Last Sample Date': plot_df['Last Sample Date'],
                'Zero Days': plot_df['Zero Days'], 'Status': 'Pending Launch' if is_pending else 'Operational'
            })
            d_df['Grade'] = d_df.apply(lambda r: calculate_grade(r['Uptime %'], r['Avg / Day']), axis=1)
            
            def get_reason(row):
                if row['Total Patients'] > 0: return ""
                fac_texts = [t for t in text_records if t['Facility'] == row['Facility']]
                if fac_texts: return fac_texts[-1]['Raw_Note']
                return "Awaiting Launch" if is_pending else "Unknown / No Note"
            d_df['Primary Reason'] = d_df.apply(get_reason, axis=1)
            all_data.append(d_df)
        except Exception: pass
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

def get_district_monthly_trend(df_raw, facility_col):
    monthly_totals = {}
    df_filtered = df_raw[get_facility_mask(df_raw, facility_col)]
    date_cols = find_date_columns(df_filtered)
    for c in date_cols:
        dt = extract_date(c)
        if pd.isna(dt): continue
        month_key = dt.strftime('%b %Y')
        total_patients = pd.to_numeric(df_filtered[c], errors='coerce').fillna(0).sum()
        if total_patients > 0 or month_key in monthly_totals: monthly_totals[month_key] = monthly_totals.get(month_key, 0) + total_patients
    if not monthly_totals: return pd.DataFrame()
    trend_df = pd.DataFrame(list(monthly_totals.items()), columns=['Month', 'Total Patients'])
    trend_df['Sort_Date'] = pd.to_datetime(trend_df['Month'], format='%b %Y', errors='coerce')
    return trend_df.dropna(subset=['Sort_Date']).sort_values('Sort_Date')

def _zm_aggregates(state_df):
    out = {}
    for zm, dists in ZM_DATA.items():
        subset = state_df[state_df['District'].isin(dists.keys())]
        if subset.empty: continue
        facs = int(subset['Facilities'].sum()); pats = int(subset['Total Patients'].sum())
        fac_days = int((subset['Facilities'] * subset['Days Reported']).sum())
        avg = round(pats / fac_days, 1) if fac_days > 0 else 0.0
        uptime = round(subset['Uptime %'].mean(), 1)
        out[zm] = {'Districts': len(dists), 'Total Patients': pats, 'Weighted Avg': avg, 'Uptime %': uptime, 'Active Spokes': int(subset['Active Spokes'].sum()), 'Total Spokes': facs}
    return out

def get_tick_step(max_val):
    if max_val <= 5: return 1
    if max_val <= 20: return 2
    if max_val <= 50: return 5
    if max_val <= 100: return 10
    if max_val <= 200: return 20
    if max_val <= 500: return 50
    return 100

# --- MAIN AREA ---
file_bytes = fetch_google_sheet(SPREADSHEET_URL)
if file_bytes is None: st.stop()

xls = pd.ExcelFile(io.BytesIO(file_bytes))
valid_keywords = set(DISTRICT_TO_ZM.keys()).union(set(DISTRICT_MAP.values())).union(set(DISTRICT_MAP.keys()))
available_sheets = [s for s in xls.sheet_names if any(kw.lower() in s.lower() or s.lower() in kw.lower() for kw in valid_keywords)]
_DISPLAY_TO_SHEET = {REVERSE_DISTRICT_MAP.get(s, s): s for s in available_sheets}
_DISPLAY_DISTRICTS = sorted(_DISPLAY_TO_SHEET.keys())

# --- HUD COMMAND BAR ---
col_title, col_nav, col_time_ctrl = st.columns([2.5, 5.0, 2.5], vertical_alignment="center")

with col_title:
    st.markdown("""
    <div class="hud-header">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 36px; height: 36px; background: rgba(0, 229, 255, 0.1); border-radius: 8px; display: flex; align-items: center; justify-content: center; border: 1px solid rgba(0, 229, 255, 0.3);">
                <!-- MICROSCOPE SVG -->
                <svg viewBox="0 0 24 24" fill="none" stroke="#00E5FF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 22px; height: 22px;">
                    <path d="M6 18h8" /><path d="M3 22h18" /><path d="M14 22a7 7 0 1 0 0-14h-1" /><path d="M9 14h2" /><path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z" /><path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3" />
                </svg>
            </div>
            <div>
                <div style="font-family: 'JetBrains Mono'; font-size: 14px; font-weight: 800; color: #F8FAFC; letter-spacing: 1px;">BIHAR COMMAND</div>
                <div style="font-family: 'JetBrains Mono'; font-size: 10px; color: #64748B;">PATHOLOGY OPS // LIVE</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_nav:
    _NAV_OPTS = ["District View", "State View", "ZM View", "Active Spokes", "Inactive Spokes"]
    if 'view_mode_override' in st.session_state:
        _override = st.session_state.pop('view_mode_override')
        if _override in _NAV_OPTS: st.session_state['nav_radio'] = _override
    view_mode = st.radio("Navigation", _NAV_OPTS, key='nav_radio', horizontal=True, label_visibility="collapsed")

with col_time_ctrl:
    tc1, tc2 = st.columns([0.2, 0.8], vertical_alignment="bottom")
    with tc1:
        if st.button("↻", help="Force refresh data", use_container_width=True):
            fetch_google_sheet.clear()
            st.rerun()
    with tc2:
        time_filter = st.selectbox("TIME RANGE", ["Full History", "Past Week", "Past 2 Weeks", "Past Month", "Select Dates..."], label_visibility="visible")

    start_date, end_date = None, None
    if time_filter == "Select Dates...":
        c1, c2 = st.columns(2)
        with c1: start_date = st.date_input("Start", value=pd.Timestamp.now() - timedelta(days=7), label_visibility="collapsed")
        with c2: end_date = st.date_input("End", value=pd.Timestamp.now(), label_visibility="collapsed")
        date_range_str = start_date.strftime('%d %b %Y') if start_date == end_date else f"{start_date.strftime('%d %b')} to {end_date.strftime('%d %b')}"
    else:
        date_range_str = time_filter

# PLOTLY LAYOUT (DEEP SPACE)
PLOTLY_LAYOUT = dict(
    template="plotly_dark", 
    font=dict(family="JetBrains Mono, monospace", size=11, color="#94A3B8"), 
    title_font=dict(size=14, color="#F8FAFC", family="Outfit, sans-serif", weight=800), 
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
    margin=dict(l=10, r=10, t=50, b=10),
    xaxis=dict(showgrid=False, linecolor='#334155', tickfont=dict(color="#94A3B8")),
    yaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(255, 255, 255, 0.05)', linecolor='#334155', tickfont=dict(color="#94A3B8"))
)

# ==============================================================================
# VIEW: DISTRICT VIEW (BENTO BOX)
# ==============================================================================
if view_mode == "District View":
    col_d, col_h, col_chk = st.columns([3, 3, 2], vertical_alignment="bottom")
    with col_d: selected_district_zm = st.selectbox("Select District", sorted(DISTRICT_TO_ZM.keys()))
    with col_h:
        zm_name_for_district = DISTRICT_TO_ZM.get(selected_district_zm, "Unknown")
        hub_options = sorted(ZM_DATA[zm_name_for_district][selected_district_zm])
        selected_hub_zm = st.selectbox("Select Hub", hub_options, key=f"hub_select_{selected_district_zm}")
    with col_chk: active_only = st.checkbox("Exclude Inactive", value=False)

    # ZM RIBBON
    zone_name = zm_name_for_district.split("(")[1].replace(")", "").strip() + " Zone" if "(" in zm_name_for_district else "Unknown Zone"
    display_zm = zm_name_for_district.split("(")[0].strip() if "(" in zm_name_for_district else zm_name_for_district
    
    col_ribbon, col_btn = st.columns([4.5, 1], vertical_alignment="center")
    with col_ribbon:
        st.markdown(f'''
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-left: 4px solid #00E5FF; border-radius: 8px; padding: 12px 20px; display: flex; align-items: center; gap: 12px;">
            <span style="font-family: 'JetBrains Mono'; font-size: 10px; color: #64748B; text-transform: uppercase;">Zone Manager</span>
            <span style="font-family: 'Outfit'; font-size: 16px; font-weight: 800; color: #FFF;">{display_zm}</span>
            <span style="font-family: 'JetBrains Mono'; font-size: 12px; color: #00E5FF;">({zone_name})</span>
        </div>
        ''', unsafe_allow_html=True)
    with col_btn:
        if st.button("Analyze →", use_container_width=True):
            st.session_state.zm_view_target = zm_name_for_district
            st.session_state.view_mode_override = "ZM View"
            st.rerun()

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
    is_pending = stats['num_days'] == 0
    inactive_facilities = plot_df[plot_df['Total Patients'] == 0]
    
    d_tab1, d_tab2, d_tab3, d_tab4 = st.tabs(["Dashboard", "Report Card", "Diagnosis", "Logistics"])

    with d_tab1:
        filtered_base = plot_df.copy()
        if active_only: filtered_base = filtered_base[filtered_base['Total Patients'] > 0]
        num_facs = len(filtered_base); dist_total = int(filtered_base['Total Patients'].sum())
        
        if num_facs > 0 and stats['num_days'] > 0:
            new_weighted_avg = round(dist_total / (num_facs * stats['num_days']), 1)
            total_fd = num_facs * stats['num_days']; new_zero_days = int(filtered_base['Zero Days'].sum())
            new_uptime = round(((total_fd - new_zero_days) / total_fd * 100), 1)
        else: new_weighted_avg = 0.0; new_uptime = 0.0

        # BENTO BOX LAYOUT
        col_main, col_side = st.columns([1.6, 1])
        
        with col_main:
            # PULSE MONITOR (Area Chart)
            st.markdown("<h3 style='font-size:16px; margin-bottom:12px;'>Patient Volume Trend</h3>", unsafe_allow_html=True)
            daily_totals = [{'Date': c, 'Patients': filtered_base[c].sum()} for c in stats['active_date_cols']]
            if daily_totals:
                dt_df = pd.DataFrame(daily_totals)
                fig_pulse = px.area(dt_df, x='Date', y='Patients')
                fig_pulse.update_traces(line_color='#00E5FF', line_width=3, fillcolor='rgba(0, 229, 255, 0.1)')
                pulse_layout = PLOTLY_LAYOUT.copy()
                pulse_layout.update(dict(height=280, xaxis=dict(showgrid=False, type='category'), yaxis=dict(showgrid=True, title="Patients"), margin=dict(l=40, r=20, t=10, b=20)))
                fig_pulse.update_layout(**pulse_layout)
                st.plotly_chart(fig_pulse, use_container_width=True)
            
            # HEATMAP
            st.markdown("<h3 style='font-size:16px; margin-top:24px; margin-bottom:12px;'>Spoke Heatmap</h3>", unsafe_allow_html=True)
            if stats['active_date_cols']:
                heatmap_df = plot_df.set_index(facility_col)[stats['active_date_cols']].copy()
                heatmap_df['Total'] = heatmap_df.sum(axis=1)
                heatmap_df = heatmap_df.sort_values(by='Total', ascending=True).drop(columns=['Total'])
                fig_h = px.imshow(heatmap_df, aspect='auto', color_continuous_scale=[[0, '#09090B'], [0.1, '#1E293B'], [1, '#00E5FF']], labels=dict(x="", y="", color=""))
                fig_h.update_traces(xgap=2, ygap=2)
                hm_layout = PLOTLY_LAYOUT.copy()
                hm_layout.update(dict(height=max(400, len(heatmap_df) * 35), yaxis=dict(tickfont=dict(size=11, color="#F8FAFC")), xaxis=dict(tickfont=dict(size=10, color="#64748B"), tickangle=-45), coloraxis_colorbar=dict(title="", thickness=10, tickfont=dict(color="#94A3B8")), margin=dict(l=10, r=10, t=10, b=40)))
                fig_h.update_layout(**hm_layout)
                st.plotly_chart(fig_h, use_container_width=True)

        with col_side:
            # KPI CARDS
            st.markdown(f'''
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 24px;">
                <div class="kpi-card">
                    <div class="kpi-label">Total Patients</div>
                    <div class="kpi-value">{dist_total:,}</div>
                    <div class="kpi-sub">Across {date_range_str}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Weighted Avg</div>
                    <div class="kpi-value">{new_weighted_avg}</div>
                    <div class="kpi-sub">Per facility/day</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Facility Uptime</div>
                    <div class="kpi-value neon-lime">{new_uptime}%</div>
                    <div class="kpi-sub">Reliability score</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Active Spokes</div>
                    <div class="kpi-value">{total_active}</div>
                    <div class="kpi-sub">of {stats['num_facilities']} total</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

            # WATCHLIST (Custom HTML)
            st.markdown("<h3 style='font-size:16px; margin-bottom:12px;'>Facility Watchlist</h3>", unsafe_allow_html=True)
            top_facs = filtered_base.sort_values('Total Patients', ascending=False).head(5)
            bottom_facs = filtered_base[filtered_base['Total Patients'] > 0].sort_values('Total Patients', ascending=True).head(5)
            
            watchlist_html = '<div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 16px;">'
            watchlist_html += '<div style="font-family: JetBrains Mono; font-size: 10px; color: #00FF94; margin-bottom: 8px; font-weight: 800;">▲ TOP PERFORMERS</div>'
            for _, row in top_facs.iterrows():
                fac_name = row[facility_col]
                if len(fac_name) > 22: fac_name = fac_name[:20] + "..."
                watchlist_html += f'<div class="watchlist-item"><span style="font-family: Outfit; font-size: 13px; color: #F8FAFC;"><span class="status-dot dot-green"></span>{fac_name}</span><span style="font-family: JetBrains Mono; font-size: 12px; color: #00E5FF;">{int(row["Total Patients"])}</span></div>'
            
            watchlist_html += '<div style="font-family: JetBrains Mono; font-size: 10px; color: #FF0055; margin-top: 16px; margin-bottom: 8px; font-weight: 800;">▼ CRITICAL ALERTS</div>'
            for _, row in bottom_facs.iterrows():
                fac_name = row[facility_col]
                if len(fac_name) > 22: fac_name = fac_name[:20] + "..."
                watchlist_html += f'<div class="watchlist-item"><span style="font-family: Outfit; font-size: 13px; color: #F8FAFC;"><span class="status-dot dot-red"></span>{fac_name}</span><span style="font-family: JetBrains Mono; font-size: 12px; color: #FF0055;">{int(row["Total Patients"])}</span></div>'
            
            if not bottom_facs.empty:
                watchlist_html += '</div>'
                st.markdown(watchlist_html, unsafe_allow_html=True)

        # DRILL DOWN (Below Bento Box)
        st.markdown("<hr style='margin: 24px 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        st.markdown("<h3 style='font-size:16px; margin-bottom:12px;'>Facility Drill-Down</h3>", unsafe_allow_html=True)
        selected_drill_facility = st.selectbox("Facility", filtered_base[facility_col].tolist(), label_visibility="collapsed")
        if selected_drill_facility:
            fac_row = plot_df[plot_df[facility_col] == selected_drill_facility].iloc[0]
            drill_trend = [{'Date': c, 'Patients': fac_row[c]} for c in stats['active_date_cols']]
            if drill_trend:
                dt_df = pd.DataFrame(drill_trend)
                fig_dt = px.line(dt_df, x='Date', y='Patients', markers=True, line_shape='hv')
                fig_dt.update_traces(line_color='#00E5FF', line_width=2, marker=dict(size=6, color='#09090B', line=dict(width=2, color='#00E5FF')))
                dt_layout = PLOTLY_LAYOUT.copy()
                dt_layout.update(dict(height=250, xaxis=dict(showgrid=False, type='category'), yaxis=dict(showgrid=True, tickformat="d", rangemode="tozero"), margin=dict(l=40, r=10, t=10, b=10)))
                fig_dt.update_layout(**dt_layout)
                st.plotly_chart(fig_dt, use_container_width=True)

    with d_tab2:
        st.markdown("<h3 style='font-size:18px; margin-bottom:16px;'>Spoke Scorecard</h3>", unsafe_allow_html=True)
        scorecard = plot_df.copy()
        scorecard['Grade'] = scorecard.apply(lambda r: calculate_grade(r['Uptime %'], r['Average Patients']), axis=1)
        scorecard = scorecard.sort_values(by=['Grade', 'Uptime %', 'Average Patients'], ascending=[True, False, False])
        
        display = pd.DataFrame()
        display['Facility'] = scorecard[facility_col]
        display['Grade'] = scorecard['Grade']
        display['Uptime %'] = scorecard['Uptime %']
        display['Avg / Day'] = scorecard['Average Patients']
        display['Total Patients'] = scorecard['Total Patients'].astype(int)
        display['Zero Days'] = scorecard['Zero Days'].astype(int)
        
        st.dataframe(display, use_container_width=True, hide_index=True, column_config={
            "Facility": st.column_config.TextColumn("Facility", width="large"),
            "Grade": st.column_config.TextColumn("Grade", width="small"),
            "Uptime %": st.column_config.NumberColumn("Uptime %", format="%.1f%%"),
            "Avg / Day": st.column_config.NumberColumn("Avg / Day", format="%.1f"),
            "Total Patients": st.column_config.NumberColumn("Total Patients", format="%d"),
            "Zero Days": st.column_config.NumberColumn("Zero Days", format="%d")
        })
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer: display.to_excel(writer, index=False, sheet_name='Scorecard')
        st.download_button(label="Download Report", data=buffer.getvalue(), file_name=f"{selected_district_zm}_Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with d_tab3:
        st.markdown("<h3 style='font-size:18px; margin-bottom:16px;'>Diagnosis & Tracking</h3>", unsafe_allow_html=True)
        inactive_df = plot_df[plot_df['Total Patients'] == 0].copy()
        if inactive_df.empty: st.success("✅ All operational facilities reported patients in this period.")
        else:
            text_records = stats.get('text_records', [])
            def get_reason(row):
                fac_texts = [t for t in text_records if t['Facility'] == row[facility_col]]
                if fac_texts: return fac_texts[-1]['Raw_Note']
                return "Unknown / No Note"
            inactive_df['Primary Reason'] = inactive_df.apply(get_reason, axis=1).apply(format_reason)
            inactive_df['Days Inactive'] = inactive_df['Last Sample Date'].apply(lambda x: (pd.Timestamp.now().normalize() - pd.to_datetime(x, format='%d %b %Y')).days if x != "Never Reported" else "-")
            
            display_inactive = inactive_df[[facility_col, 'Last Sample Date', 'Days Inactive', 'Primary Reason']].copy().rename(columns={facility_col: 'Facility'})
            styled_inactive = display_inactive.style.map(style_reason, subset=['Primary Reason'])
            st.dataframe(styled_inactive, use_container_width=True, hide_index=True, column_config={"Facility": st.column_config.TextColumn("Facility", width="large"), "Last Sample Date": st.column_config.TextColumn("Last Sample Date", width="medium"), "Days Inactive": st.column_config.TextColumn("Days Inactive", width="small"), "Primary Reason": st.column_config.TextColumn("Primary Reason", width="large")})

    with d_tab4:
        st.markdown("<h3 style='font-size:18px; margin-bottom:16px;'>Hub Logistics</h3>", unsafe_allow_html=True)
        dist_col = find_distance_column(df_raw)
        if dist_col:
            dist_data = df_raw[[facility_col, dist_col]].copy().rename(columns={facility_col: 'Facility', dist_col: 'Raw_Distance'})
            def clean_distance(val):
                if pd.isna(val): return None
                s = str(val).strip()
                if s == '' or s.lower() in ('nan', 'none', '-', 'na', 'n/a'): return None
                try: return float(s)
                except ValueError: pass
                cleaned = re.sub(r'[~<>≈]', '', s)
                cleaned = re.sub(r'\s*(kms?|kilometers?|kilo\s*meters?|mi|miles?)\s*$', '', cleaned, flags=re.IGNORECASE).strip()
                try: return float(cleaned)
                except ValueError: return DISTANCE_FALLBACK.get(s, None)
                    
            dist_data['Distance'] = dist_data['Raw_Distance'].apply(clean_distance)
            polar_df = pd.merge(scorecard[[facility_col, 'Grade', 'Uptime %', 'Average Patients']], dist_data[['Facility', 'Distance']], left_on=facility_col, right_on='Facility')
            valid_polar_df = polar_df.dropna(subset=['Distance']).copy()
            
            if not valid_polar_df.empty:
                valid_polar_df['Display_Name'] = valid_polar_df[facility_col].apply(lambda x: x if len(x) <= 25 else x[:22] + "...")
                valid_polar_df = valid_polar_df.sort_values(by='Distance', ascending=True)
                grade_color_map = {'A': '#00FF94', 'B': '#00E5FF', 'C': '#FFD500', 'D': '#FF8C00', 'F': '#FF0055'}
                fig_dist = px.bar(valid_polar_df, y='Display_Name', x='Distance', orientation='h', color='Grade', color_discrete_map=grade_color_map, text='Distance')
                fig_dist.update_traces(texttemplate='%{text:.1f} km', textposition='outside', textfont=dict(color="#FFF", weight=700))
                dist_layout = PLOTLY_LAYOUT.copy()
                dist_layout.update(dict(height=max(400, len(valid_polar_df) * 35), yaxis=dict(autorange="reversed", showgrid=False), xaxis=dict(showgrid=True, title="Distance (km)"), showlegend=False, coloraxis_showscale=False))
                fig_dist.update_layout(**dist_layout)
                st.plotly_chart(fig_dist, use_container_width=True)
        else: st.warning("⚠️ Distance column not found.")

# ==============================================================================
# VIEW: STATE VIEW
# ==============================================================================
elif view_mode == "State View":
    st.markdown("<h2 style='font-size:20px; margin-bottom:16px;'>Statewide Overview</h2>", unsafe_allow_html=True)
    state_df = calculate_all_districts(tuple(available_sheets), file_bytes, time_filter, start_date, end_date)
    all_fac_df = get_all_facility_data(tuple(available_sheets), file_bytes, time_filter, start_date, end_date)
    
    if not state_df.empty and not all_fac_df.empty:
        total_active = state_df['Active Spokes'].sum()
        total_pending = len(all_fac_df[all_fac_df['Status'] == 'Pending Launch'])
        total_operational = len(all_fac_df) - total_pending
        total_failures = total_operational - total_active
        reporting_districts = state_df[state_df['Days Reported'] > 0]
        avg_state_uptime = round(reporting_districts['Uptime %'].mean(), 1) if not reporting_districts.empty else 0.0
        
        # RESTORED KPI CARDS
        st.markdown(f'''
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
            <div class="kpi-card">
                <div class="kpi-label">Network Status</div>
                <div class="kpi-value neon-cyan">{total_active} <span style="font-size:14px; color:#64748B;">Active</span></div>
                <div class="kpi-sub" style="display:flex; gap:12px; margin-top:8px;">
                    <span style="color:#FF0055;">{total_failures} Failures</span>
                    <span style="color:#FFD500;">{total_pending} Pending</span>
                </div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Statewide Avg Uptime</div>
                <div class="kpi-value neon-lime">{avg_state_uptime}%</div>
                <div class="kpi-sub">Across all operational facilities</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        s_tab1, s_tab2 = st.tabs(["District Leaderboard", "Compare Districts"])
        
        with s_tab1:
            # RESTORED BAR CHART
            st.markdown("<h4 style='font-size:16px; margin-bottom:12px;'>Top 5 / Bottom 5 Districts (Total Patients)</h4>", unsafe_allow_html=True)
            sorted_dist = state_df.sort_values('Total Patients', ascending=True)
            top5 = sorted_dist.tail(5)
            bottom5 = sorted_dist.head(5)
            chart_data = pd.concat([bottom5, top5]).drop_duplicates()
            
            fig_s = px.bar(chart_data, y='District', x='Total Patients', orientation='h', text='Total Patients')
            fig_s.update_traces(marker_color='#00E5FF', textposition='outside', textfont=dict(color="#FFF", weight=700))
            s_layout = PLOTLY_LAYOUT.copy()
            s_layout.update(dict(height=350, yaxis=dict(showgrid=False, tickfont=dict(color="#F8FAFC")), xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'), margin=dict(l=20, r=20, t=10, b=10)))
            fig_s.update_layout(**s_layout)
            st.plotly_chart(fig_s, use_container_width=True)

            # RESTORED TABLE (WITH DARK CSS)
            lb_df = state_df.sort_values('Total Patients', ascending=False).reset_index(drop=True)
            lb_df['Rank'] = lb_df.index + 1
            lb_df['District'] = lb_df.apply(lambda row: f"{'🥇' if row['Rank']==1 else '🥈' if row['Rank']==2 else '🥉' if row['Rank']==3 else ''} {row['District']}".strip(), axis=1)
            
            st.dataframe(lb_df[['Rank', 'District', 'Total Patients', 'Weighted Avg', 'Uptime %', 'Facilities', 'Active Spokes']], use_container_width=True, hide_index=True, column_config={
                "Rank": st.column_config.TextColumn("Rank", width="small"),
                "Uptime %": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100)
            })

        with s_tab2:
            col_a, col_b = st.columns(2)
            with col_a: dist_a = st.selectbox("District A", _DISPLAY_DISTRICTS)
            with col_b: dist_b = st.selectbox("District B", _DISPLAY_DISTRICTS, index=1)
            
            sa = state_df[state_df['District'] == dist_a].iloc[0] if not state_df[state_df['District'] == dist_a].empty else None
            sb = state_df[state_df['District'] == dist_b].iloc[0] if not state_df[state_df['District'] == dist_b].empty else None
            
            if sa is not None and sb is not None:
                st.markdown(f'''
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px;">
                    <div class="kpi-card" style="border-top: 2px solid #00E5FF;">
                        <div class="kpi-label" style="color: #00E5FF !important;">{dist_a}</div>
                        <div class="kpi-value">{sa['Total Patients']:,} <span style="font-size:12px; color:#64748B;">Patients</span></div>
                        <div class="kpi-sub">Uptime: {sa['Uptime %']}% | Weighted Avg: {sa['Weighted Avg']}</div>
                    </div>
                    <div class="kpi-card" style="border-top: 2px solid #FF0055;">
                        <div class="kpi-label" style="color: #FF0055 !important;">{dist_b}</div>
                        <div class="kpi-value">{sb['Total Patients']:,} <span style="font-size:12px; color:#64748B;">Patients</span></div>
                        <div class="kpi-sub">Uptime: {sb['Uptime %']}% | Weighted Avg: {sb['Weighted Avg']}</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)

# ==============================================================================
# VIEW: ZM VIEW
# ==============================================================================
elif view_mode == "ZM View":
    st.markdown("<h2 style='font-size:20px; margin-bottom:16px;'>Zone Manager View</h2>", unsafe_allow_html=True)
    state_df_lb = calculate_all_districts(tuple(available_sheets), file_bytes, time_filter, start_date, end_date)
    
    # RESTORED TWO TABS
    zm_drill_tab, zm_lb_tab = st.tabs(["🔍 Zone Drill-Down", "🏆 ZM Leaderboard"])
    
    with zm_drill_tab:
        _zm_opts = sorted(ZM_DATA.keys())
        selected_zm = st.selectbox("Select Zone Manager", _zm_opts, key='zm_sel')
        zm_districts = list(ZM_DATA[selected_zm].keys())
        
        zm_df = state_df_lb[state_df_lb['District'].isin(zm_districts)].copy()
        if zm_df.empty:
            st.warning(f"No data available for {selected_zm}'s districts in the selected time range.")
        else:
            total_patients = zm_df['Total Patients'].sum()
            total_active = zm_df['Active Spokes'].sum()
            total_facilities = zm_df['Facilities'].sum()
            
            zone_fac_days = int((zm_df['Facilities'] * zm_df['Days Reported']).sum())
            zone_weighted_avg = round(total_patients / zone_fac_days, 1) if zone_fac_days > 0 else 0.0
            avg_uptime = round(zm_df['Uptime %'].mean(), 1)
            
            # RESTORED KPI CARDS WITH WEIGHTED AVG
            st.markdown(f'''
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; margin-top:16px;">
                <div class="kpi-card">
                    <div class="kpi-label">Coverage</div>
                    <div class="kpi-value">{len(zm_districts)}</div>
                    <div class="kpi-sub">Districts</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Weighted Avg / Day</div>
                    <div class="kpi-value">{zone_weighted_avg}</div>
                    <div class="kpi-sub">Efficiency score</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Active Spokes</div>
                    <div class="kpi-value">{total_active} <span style="font-size:14px; color:#64748B;">/ {total_facilities}</span></div>
                    <div class="kpi-sub">Operational facilities</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Avg Zone Uptime</div>
                    <div class="kpi-value neon-lime">{avg_uptime}%</div>
                    <div class="kpi-sub">Reliability score</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            st.markdown(f"<h4 style='font-size:16px; margin-bottom:12px;'>District Breakdown — {selected_zm}</h4>", unsafe_allow_html=True)
            st.dataframe(zm_df[['District', 'Total Patients', 'Weighted Avg', 'Uptime %', 'Facilities', 'Active Spokes']], use_container_width=True, hide_index=True, column_config={
                "Uptime %": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
                "Total Patients": st.column_config.NumberColumn(format="%d"),
                "Weighted Avg": st.column_config.NumberColumn(format="%.1f")
            })

    with zm_lb_tab:
        zm_metric = st.radio("Rank by:", ["Total Patients", "Uptime %"], horizontal=True)
        cur_zm = _zm_aggregates(state_df_lb)
        
        if cur_zm:
            sorted_zm = sorted(cur_zm.items(), key=lambda kv: kv[1][zm_metric], reverse=True)
            max_val = max(m[zm_metric] for _, m in sorted_zm) if sorted_zm else 1
            
            for rank, (zm, m) in enumerate(sorted_zm):
                val = m[zm_metric]
                width_pct = (val / max_val) * 100
                color = "#00FF94" if rank == 0 else "#00E5FF" if rank < 3 else "#FF8C00" if rank < 6 else "#FF0055"
                
                # NO MORE "PTS" - NOW SAYS "PATIENTS"
                st.markdown(f'''
                <div class="race-track">
                    <div class="race-label">
                        <span>{rank+1}. {zm} <span style="color:#64748B; margin-left:8px;">({m['Districts']} districts)</span></span>
                        <span style="color: {color};">{val:,} {"Patients" if zm_metric == "Total Patients" else "%"} <span style="color:#64748B; font-size:11px; margin-left:8px;">| Weighted Avg: {m['Weighted Avg']}</span></span>
                    </div>
                    <div class="race-bar-bg">
                        <div class="race-bar-fill" style="width: {width_pct}%; background-color: {color}; color: {color};"></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)

# ==============================================================================
# VIEW: ACTIVE / INACTIVE SPOKES
# ==============================================================================
elif view_mode in ["Active Spokes", "Inactive Spokes"]:
    st.markdown(f"<h2 style='font-size:20px; margin-bottom:16px;'>{view_mode}</h2>", unsafe_allow_html=True)
    all_fac_df = get_all_facility_data(tuple(available_sheets), file_bytes, time_filter, start_date, end_date)
    
    if not all_fac_df.empty:
        # RESTORED KPI CARDS
        if view_mode == "Active Spokes":
            active_df = all_fac_df[all_fac_df['Total Patients'] > 0].copy()
            total_pending = len(all_fac_df[all_fac_df['Status'] == 'Pending Launch'])
            total_operational = len(all_fac_df) - total_pending
            
            st.markdown(f'''
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
                <div class="kpi-card">
                    <div class="kpi-label">Active Spokes Shown</div>
                    <div class="kpi-value neon-cyan">{len(active_df)} <span style="font-size:14px; color:#64748B;">/ {total_operational} Operational</span></div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Total Patients</div>
                    <div class="kpi-value">{active_df['Total Patients'].sum():,}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Filters
            col1, col2 = st.columns(2)
            with col1: dist_filter = st.multiselect("Filter by District", sorted(active_df['District'].unique()), default=[])
            with col2: grade_filter = st.multiselect("Filter by Grade", ["A", "B", "C", "D", "F"], default=[])
            if dist_filter: active_df = active_df[active_df['District'].isin(dist_filter)]
            if grade_filter: active_df = active_df[active_df['Grade'].isin(grade_filter)]
            
            active_df = active_df.sort_values('Total Patients', ascending=False)
            st.dataframe(active_df[['District', 'Facility', 'Grade', 'Total Patients', 'Uptime %', 'Last Sample Date']], use_container_width=True, hide_index=True)
            
        else: # Inactive Spokes
            inactive_df = all_fac_df[all_fac_df['Total Patients'] == 0].copy()
            op_failures = inactive_df[inactive_df['Status'] == 'Operational'].reset_index(drop=True)
            pending_launch = inactive_df[inactive_df['Status'] == 'Pending Launch'].reset_index(drop=True)
            
            st.markdown(f'''
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
                <div class="kpi-card" style="border-top: 2px solid #FF0055;">
                    <div class="kpi-label" style="color: #FF0055 !important;">Operational Failures</div>
                    <div class="kpi-value neon-magenta">{len(op_failures)}</div>
                </div>
                <div class="kpi-card" style="border-top: 2px solid #FFD500;">
                    <div class="kpi-label" style="color: #FFD500 !important;">Pending Launch</div>
                    <div class="kpi-value" style="color: #FFD500 !important;">{len(pending_launch)}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            z_tab1, z_tab2 = st.tabs([f"🔴 True Operational Failures ({len(op_failures)})", f"🚧 Pending Launch ({len(pending_launch)})"])
            with z_tab1:
                if not op_failures.empty:
                    op_failures['SortDate'] = pd.to_datetime(op_failures['Last Sample Date'], errors='coerce')
                    op_failures = op_failures.sort_values(by=['SortDate', 'Last Sample Date'], ascending=[True, True], na_position='first').drop(columns=['SortDate'])
                    display_tracker = op_failures[['District', 'Facility', 'Last Sample Date', 'Primary Reason']].copy()
                    display_tracker['Primary Reason'] = display_tracker['Primary Reason'].apply(format_reason)
                    styled_tracker = display_tracker.style.map(style_reason, subset=['Primary Reason'])
                    st.dataframe(styled_tracker, use_container_width=True, hide_index=True)
                else: st.success("✅ Excellent! No operational facilities found with 0 patients.")
            
            with z_tab2:
                if not pending_launch.empty:
                    st.dataframe(pending_launch[['District', 'Facility', 'Last Sample Date']], use_container_width=True, hide_index=True)
                else: st.success("✅ All facilities have launched!")