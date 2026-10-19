import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta, datetime
import re
import io
import math

# --- PAGE SETUP ---
st.set_page_config(page_title="Bihar Health Dashboard", page_icon="🏥", layout="wide")

# --- CLEAN ENTERPRISE UI CSS (Cool Steel Theme) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    .material-symbols-rounded, [data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }
    
    /* --- THE SLATE CANVAS --- */
    .stApp { background-color: #E2E8F0 !important; } 
    section[data-testid="stSidebar"] { background-color: #F8FAFC !important; border-right: 1px solid #CBD5E1; }
    
    /* Metric Cards */
    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .metric-card {
        background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px;
        padding: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); display: flex; flex-direction: column;
    }
    .metric-label { color: #64748B; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
    .metric-value { color: #0F172A; font-size: 28px; font-weight: 700; line-height: 1; display: flex; align-items: baseline; gap: 8px; }
    .metric-sub { font-size: 16px; font-weight: 500; color: #64748B; }

    /* Tables & Cards */
    [data-testid="stDataFrame"] { background-color: #FFFFFF !important; border-radius: 10px; border: 1px solid #CBD5E1; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); padding: 4px; }
    .zm-card { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; padding: 16px; margin-bottom: 24px; box-shadow: 0 2px 4px 0 rgba(0,0,0,0.05); }
    .zm-card-header { color: #64748B; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 4px;}
    .zm-card-name { color: #0F172A; font-size: 15px; font-weight: 600; margin-bottom: 2px;}
    .zm-card-zone { color: #2563EB; font-size: 13px; font-weight: 500;}

    /* Report Header */
    .report-header { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px; padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    .report-title { color: #0F172A; font-size: 22px; font-weight: 700; margin-bottom: 8px; }
    .report-meta { color: #64748B; font-size: 14px; line-height: 1.6; }
    
    /* Grades */
    .grade-badge { display: inline-block; padding: 6px 16px; border-radius: 6px; font-size: 20px; font-weight: 700; }
    .grade-A { background-color: #D1FAE5; color: #065F46; border: 1px solid #34D399; }
    .grade-B { background-color: #ECFCCB; color: #3F6212; border: 1px solid #A3E635; }
    .grade-C { background-color: #FEF3C7; color: #92400E; border: 1px solid #FBBF24; }
    .grade-D { background-color: #FFEDD5; color: #9A3412; border: 1px solid #FB923C; }
    .grade-F { background-color: #FEE2E2; color: #991B1B; border: 1px solid #F87171; }

    /* --- UPGRADED HEADER & PULSING DOT --- */
    .app-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 24px; background-color: #FFFFFF; border-radius: 12px; border: 1px solid #CBD5E1; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .header-left { display: flex; align-items: center; gap: 16px; }
    .header-icon { display: flex; align-items: center; justify-content: center; width: 44px; height: 44px; background-color: #EFF6FF; border-radius: 10px; font-size: 22px; }
    
    .header-title { font-size: 22px; font-weight: 800; color: #0F172A; letter-spacing: -0.5px; line-height: 1.1; }
    .header-subtitle { font-size: 13px; font-weight: 500; color: #64748B; margin-top: 2px; }

    .header-right { display: flex; align-items: center; gap: 16px; }
    .status-badge { background-color: #D1FAE5; color: #065F46; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; display: flex; align-items: center; gap: 8px; border: 1px solid #A7F3D0; }
    
    /* Blinking Radar Dot */
    .status-dot { 
        width: 8px; height: 8px; background-color: #10B981; border-radius: 50%; 
        animation: pulse-green 2s infinite; 
    }
    @keyframes pulse-green {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    
    .header-date { font-size: 13px; color: #64748B; font-weight: 500; }

    /* Compare Battle Cards */
    .battle-card { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 16px; }
    .battle-card-blue { border-top: 4px solid #2563EB; }
    .battle-card-red { border-top: 4px solid #DC2626; }
    .battle-title { font-size: 18px; font-weight: 700; margin-bottom: 16px; }
    .battle-row { display: flex; justify-content: space-between; border-bottom: 1px solid #F1F5F9; padding: 10px 0; font-size: 14px; color: #475569; }
    .battle-row:last-child { border-bottom: none; }
    .battle-val { font-weight: 600; color: #0F172A; }

    /* --- DEFINITIVE DROPDOWN STYLING --- */
    div[data-testid="stSelectbox"] { margin-bottom: 12px; }
    div[data-testid="stSelectbox"] div[role="combobox"] { 
        background-color: #F8FAFC !important; border: 1px solid #94A3B8 !important; border-radius: 8px !important; 
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important; transition: all 0.2s ease-in-out !important; min-height: 44px !important; 
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div { background-color: transparent !important; border: none !important; }
    div[data-testid="stSelectbox"] div[role="combobox"]:hover { border-color: #2563EB !important; background-color: #FFFFFF !important; }
    div[data-testid="stSelectbox"] div[role="combobox"]:focus-within { border-color: #2563EB !important; background-color: #FFFFFF !important; box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2) !important; }
    div[data-testid="stSelectbox"] div[role="combobox"] * { color: #0F172A !important; font-weight: 600 !important; }
    div[data-testid="stSelectbox"] div[role="combobox"] svg { fill: #64748B !important; }
    label[data-testid="stWidgetLabel"] p { color: #1E293B !important; font-weight: 600 !important; font-size: 14px !important; margin-bottom: 4px !important; }

    /* Date Picker */
    div[data-testid="stDateInput"] div[data-baseweb="input"] { border: 1px solid #94A3B8 !important; border-radius: 8px !important; background-color: #F8FAFC !important; min-height: 44px !important; }
    div[data-testid="stDateInput"] div[data-baseweb="input"]:focus-within { border-color: #2563EB !important; background-color: #FFFFFF !important; box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2) !important; }

    /* Segmented Control (Radio Buttons) */
    div[data-testid="stRadio"] label > div:first-child { display: none !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] { display: inline-flex !important; background-color: #E2E8F0 !important; padding: 4px !important; border-radius: 10px !important; gap: 4px !important; border: 1px solid #CBD5E1 !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] label { padding: 8px 16px !important; border-radius: 6px !important; cursor: pointer !important; transition: all 0.2s ease !important; color: #475569 !important; font-weight: 600 !important; font-size: 14px !important; margin: 0 !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) { background-color: #FFFFFF !important; color: #2563EB !important; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1) !important; }
</style>
""", unsafe_allow_html=True)

# --- DATA & HELPERS ---
ZM_DATA = {
    "Keshav Kumar (Patna)": {"Bhojpur": ["DH Ara Bhojpur"], "Nalanda": ["DH Bihar Sharif Nalanda"], "Patna": ["DH (Guru Gobind Singh Hospital, Patna City)"], "Barh": ["SDH Barh Patna"], "Danapur": ["SDH Danapur Patna"]},
    "Samir Kumar Singh (Bhagalpur)": {"Banka": ["DH Banka"], "Bhagalpur": ["DH LNJP Bhagalpur"], "Jamui": ["DH Jamui"], "Munger": ["DH Munger"]},
    "Manish Rai (Champaran)": {"East Champaran": ["DH Motihari"], "Sitamarhi": ["DH Sitamarhi"], "West Champaran": ["SDH Narkatiyaganj"]},
    "Mohammad Asif Nasir (Darbhanga)": {"Darbhanga": ["DH Darbhanga"], "Madhubani": ["DH Madhubani"], "Samastipur": ["DH Samastipur"]},
    "Narendra Kumar Pal (Gaya)": {"Aurangabad": ["DH Aurangabad"], "Gaya": ["Prabhawati Hospital Gaya"], "Nawada": ["DH Nawada"], "Arwal": ["DH Arwal"], "Jehanabad": ["DH Jehanabad"]},
    "Santosh Kumar (Khagaria)": {"Begusarai": ["DH Begusarai"], "Khagaria": ["DH Khagaria"], "Lakhisarai": ["DH Lakhisarai"], "Seikhpura": ["DH Sheikhpura"]},
    "Rupesh Kumar (Muzaffarpur)": {"Muzaffarpur": ["DH Muzaffarpur"], "Sheohar": ["Saroja Sitaram Sadar Hospital Sheohar"], "Vaishali": ["DH Hajipur"]},
    "Paras kumar Jaiswal (Purnia)": {"Araria": ["DH Araria"], "Katihar": ["DH Katihar"], "Kishanganj": ["DH Kishanganj"], "Purnia": ["CHC Krityanand Nagar"]},
    "Umesh Tiwari (Rohtas)": {"Buxar": ["DH Buxar"], "Kaimur": ["DH Kaimur"], "Rohtas": ["DH Sasaram"]},
    "Anant Kumar Ray (Saharsa)": {"Madhepura": ["DH Madhepura"], "Saharsa": ["DH Saharsa"], "Supaul": ["DH Supaul"]},
    "Krishna Prakash (Saran)": {"Gopalganj": ["DH Gopalganj"], "Saran": ["DH Saran"], "Siwan": ["DH Siwan"]}
}
DISTRICT_TO_ZM = {d: zm for zm, dists in ZM_DATA.items() for d in dists}
DISTRICT_MAP = {"Seikhpura": "Sheikhpura", "Rohtas": "Sasaram"}
REVERSE_DISTRICT_MAP = {v: k for k, v in DISTRICT_MAP.items()}

def read_sheet_robust(xls, sheet_name):
    try:
        df_raw = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        header_idx = next((i for i in range(min(15, len(df_raw))) for cell in df_raw.iloc[i] if 'name of the hospital' in str(cell).lower()), None)
        df = pd.read_excel(xls, sheet_name=sheet_name, header=header_idx) if header_idx is not None else pd.read_excel(xls, sheet_name=sheet_name)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

def find_facility_column(df):
    # REVERTED: Strict column matching to avoid counting random notes as facilities
    for c in df.columns:
        if 'name of the hospital' in str(c).lower() or ('hospital' in str(c).lower() and 'name' in str(c).lower()): return c
    return None

def extract_date(col_name):
    if isinstance(col_name, pd.Timestamp): return col_name
    s = str(col_name)
    for pattern, fmt in [(r'(\d{4}-\d{2}-\d{2})', None), (r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', True), (r'(\d{1,2}-\w{3}-\d{2,4})', None)]:
        match = re.search(pattern, s)
        if match: return pd.to_datetime(match.group(1), dayfirst=fmt if fmt else False, errors='coerce')
    return pd.NaT

def find_date_columns(df):
    date_cols = [c for c in df.columns if 'Total number of patients' in str(c)]
    if date_cols: return date_cols
    return [c for c in df.columns if pd.notna(extract_date(c))]

def get_facility_mask(df, facility_col):
    mask = df[facility_col].notna()
    mask &= ~df[facility_col].astype(str).str.upper().str.contains('TOTAL', na=False)
    mask &= ~df[facility_col].astype(str).str.upper().str.contains('JAIL', na=False)
    mask &= ~df[facility_col].astype(str).str.strip().str.lower().isin(['nan', 'none', ''])
    return mask

def categorize_reason(text):
    if not text or str(text).strip().lower() in ['nan', 'none', '', '0', '0.0']: return 'Unknown'
    t = str(text).lower()
    if any(w in t for w in ['leave', 'nahi', 'nhi', 'unavailable', 'absent', 'lt']): return 'Staffing / Leave'
    if any(w in t for w in ['denied', 'prescribing', 'refuse', 'no test']): return 'Refusal'
    if any(w in t for w in ['closed', 'machine', 'breakdown']): return 'Infrastructure'
    return 'Other / Unspecified'

def process_district_df(df, time_filter, start_date=None, end_date=None, anchor_date=None):
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
        return plot_df, None, {
            'total': 0, 'weighted_avg': 0.0, 'zero_days': 0, 
            'num_facilities': len(df), 'num_days': 0, 
            'facility_col': facility_col, 'active_date_cols': [], 
            'text_records': [], 'active_facilities': 0,
            'total_absolute_facilities': total_absolute_facilities
        }

    paired = [(c, extract_date(c)) for c in date_cols]
    paired = [(c, d) for c, d in paired if pd.notna(d)]
    paired.sort(key=lambda x: x[1])
    sorted_cols = [c for c, d in paired]
    
    if time_filter == "All Available Data" and anchor_date:
        active_date_cols = [c for c, d in paired if d.date() <= anchor_date]
    elif time_filter == "Custom Range" and start_date and end_date:
        active_date_cols = [c for c, d in paired if start_date <= d.date() <= end_date]
    else:
        latest_data_idx = next((i for i in range(len(sorted_cols) - 1, -1, -1) if pd.to_numeric(df[sorted_cols[i]], errors='coerce').fillna(0).sum() > 0), len(sorted_cols) - 1)
        if time_filter == "Last 7 Days": active_date_cols = sorted_cols[max(0, latest_data_idx - 6): latest_data_idx + 1]
        elif time_filter == "Last 15 Days": active_date_cols = sorted_cols[max(0, latest_data_idx - 14): latest_data_idx + 1]
        elif time_filter == "Last 30 Days": active_date_cols = sorted_cols[max(0, latest_data_idx - 29): latest_data_idx + 1]
        else: active_date_cols = sorted_cols[:latest_data_idx + 1]

    if not active_date_cols: active_date_cols = sorted_cols
    
    # TEXT SCAVENGER
    text_records = []
    def is_text_note(x):
        if not isinstance(x, str): return False
        v = x.strip().lower()
        if v in ['', 'nan', 'none', '0', '0.0']: return False
        try:
            float(v); return False
        except ValueError:
            return True
            
    for col in active_date_cols:
        str_mask = df[col].apply(is_text_note)
        if str_mask.any():
            for idx in df[str_mask].index:
                raw_note = str(df.loc[idx, col]).strip()
                text_records.append({
                    'Facility': df.loc[idx, facility_col],
                    'Date': extract_date(col),
                    'Raw_Note': raw_note,
                    'Category': categorize_reason(raw_note)
                })
            
    plot_df = df[[facility_col] + active_date_cols].copy()
    for col in active_date_cols: plot_df[col] = pd.to_numeric(plot_df[col], errors='coerce').fillna(0)
        
    plot_df['Total Patients'] = plot_df[active_date_cols].sum(axis=1)
    plot_df['Average Patients'] = plot_df[active_date_cols].mean(axis=1).round(1)
    plot_df['Zero Days'] = (plot_df[active_date_cols] == 0).sum(axis=1)
    
    last_day_col = active_date_cols[-1]
    active_facilities = int((plot_df[last_day_col] > 0).sum())
    
    district_total = int(plot_df['Total Patients'].sum())
    num_facilities = len(plot_df)
    num_days = len(active_date_cols)
    weighted_avg = round(district_total / (num_facilities * num_days), 1) if num_facilities > 0 and num_days > 0 else 0
    total_zero = int(plot_df['Zero Days'].sum())
    
    if num_days > 0: plot_df['Uptime %'] = ((num_days - plot_df['Zero Days']) / num_days * 100).round(1)
    else: plot_df['Uptime %'] = 0
        
    return plot_df, None, {'total': district_total, 'weighted_avg': weighted_avg, 'zero_days': total_zero, 'num_facilities': num_facilities, 'num_days': num_days, 'facility_col': facility_col, 'active_date_cols': active_date_cols, 'text_records': text_records, 'active_facilities': active_facilities, 'total_absolute_facilities': total_absolute_facilities}

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

def find_global_latest_date(sheet_names_tuple, uploaded_file_bytes):
    xls = pd.ExcelFile(io.BytesIO(uploaded_file_bytes))
    latest_dates = []
    for sheet in sheet_names_tuple:
        try:
            df = read_sheet_robust(xls, sheet)
            fac_col = find_facility_column(df)
            if not fac_col: continue
            df = df[get_facility_mask(df, fac_col)]
            date_cols = find_date_columns(df)
            if not date_cols: continue
            
            paired = [(c, extract_date(c)) for c in date_cols]
            paired = [(c, d) for c, d in paired if pd.notna(d)]
            paired.sort(key=lambda x: x[1])
            sorted_cols = [c for c, d in paired]
            
            latest_idx = next((i for i in range(len(sorted_cols) - 1, -1, -1) if pd.to_numeric(df[sorted_cols[i]], errors='coerce').fillna(0).sum() > 0), -1)
            if latest_idx != -1:
                latest_dates.append(paired[latest_idx][1].date())
        except Exception:
            pass
    return min(latest_dates) if latest_dates else None

@st.cache_data(show_spinner=False)
def calculate_all_districts(sheet_names_tuple, uploaded_file_bytes, time_filter, _cache_buster="v4.0"):
    xls = pd.ExcelFile(io.BytesIO(uploaded_file_bytes))
    
    anchor_date = None
    if time_filter == "All Available Data":
        anchor_date = find_global_latest_date(sheet_names_tuple, uploaded_file_bytes)
        
    data = []
    for sheet in sheet_names_tuple:
        try:
            sdf = read_sheet_robust(xls, sheet)
            _, _, s = process_district_df(sdf, time_filter, anchor_date=anchor_date)
            if s:
                data.append({
                    'District': sheet, 
                    'Total Patients': s['total'], 
                    'Weighted Avg': s['weighted_avg'], 
                    'Uptime %': calc_uptime(s), 
                    'Facilities': s['total_absolute_facilities'],
                    'Days Reported': s['num_days'],
                    'Active Spokes': s['active_facilities']
                })
        except Exception: pass
    return pd.DataFrame(data), anchor_date

@st.cache_data(show_spinner=False)
def generate_zero_tracker_data(sheet_names_tuple, uploaded_file_bytes, _cache_buster="v4.0"):
    xls = pd.ExcelFile(io.BytesIO(uploaded_file_bytes))
    tracker_data = []
    
    for sheet in sheet_names_tuple:
        try:
            sdf = read_sheet_robust(xls, sheet)
            plot_df, _, stats = process_district_df(sdf, "All Available Data")
            if plot_df is None: continue
            
            facility_col = stats['facility_col']
            active_cols = stats['active_date_cols']
            max_days = len(active_cols)
            text_records = stats.get('text_records', [])
            
            if max_days == 0: continue
            
            original_district_name = REVERSE_DISTRICT_MAP.get(sheet, sheet)
            raw_zm = DISTRICT_TO_ZM.get(original_district_name, "Unknown")
            zm_name = raw_zm.split(" (")[0] if " (" in raw_zm else raw_zm
            
            rev_cols = active_cols[::-1]
            is_zero = plot_df[rev_cols].eq(0)
            streaks = is_zero.cumprod(axis=1).sum(axis=1)
            
            for idx, row in plot_df.iterrows():
                streak = int(streaks[idx])
                if streak == 0: continue
                
                fac_name = row[facility_col]
                last_active_date = "Never Reported"
                
                if streak < max_days:
                    last_active_idx = (max_days - 1) - streak
                    date_obj = extract_date(active_cols[last_active_idx])
                    if pd.notna(date_obj):
                        last_active_date = date_obj.strftime('%d %b %Y')
                        
                primary_reason = "No Note"
                fac_texts = [t for t in text_records if t['Facility'] == fac_name]
                if fac_texts:
                    fac_texts.sort(key=lambda x: x['Date'] if pd.notna(x['Date']) else pd.Timestamp.min, reverse=True)
                    primary_reason = fac_texts[0]['Raw_Note']
                    
                if streak >= 30: severity = "🔴 Critical"
                elif streak >= 15: severity = "🟠 High Risk"
                elif streak >= 7: severity = "🟡 Warning"
                else: severity = "⚪ Monitor"
                
                tracker_data.append({
                    'ZM': zm_name,
                    'District': sheet,
                    'Facility Name': fac_name,
                    'Last Active Date': last_active_date,
                    'Inactive Days': streak,
                    'Severity': severity,
                    'Primary Reason': primary_reason
                })
        except Exception:
            pass
            
    tracker_df = pd.DataFrame(tracker_data)
    if not tracker_df.empty:
        tracker_df = tracker_df.sort_values(by=['Inactive Days', 'District', 'Facility Name'], ascending=[False, True, True]).reset_index(drop=True)
    return tracker_df

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color:#0F172A; margin-bottom:20px;'>Control Panel</h3>", unsafe_allow_html=True)
    uploaded_data_file = st.file_uploader("Upload Data File", type=["xlsx", "csv"])
    
    if uploaded_data_file is not None:
        try:
            file_bytes = uploaded_data_file.getvalue()
            xls = pd.ExcelFile(uploaded_data_file)
            available_sheets = xls.sheet_names
            
            st.markdown("<hr style='margin: 20px 0; border-color: #CBD5E1;'>", unsafe_allow_html=True)
            
            st.markdown("<p style='font-size:13px; font-weight:600; color:#64748B; text-transform:uppercase; margin-bottom:5px;'>Time Range</p>", unsafe_allow_html=True)
            time_filter = st.selectbox("Time Range", ["All Available Data", "Last 7 Days", "Last 15 Days", "Last 30 Days", "Custom Range"], label_visibility="collapsed")
            
            start_date, end_date = None, None
            if time_filter == "Custom Range":
                col1, col2 = st.columns(2)
                start_date = col1.date_input("Start Date", value=pd.Timestamp.now() - timedelta(days=30))
                end_date = col2.date_input("End Date", value=pd.Timestamp.now())
                date_range_str = f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}"
            else:
                date_range_str = time_filter

        except Exception as e:
            st.error(f"Error: {e}")

# --- MAIN AREA ---
if uploaded_data_file is None:
    st.markdown("""
    <div class="app-header">
        <div class="header-left">
            <div class="header-icon">🏥</div>
            <div>
                <div class="header-title">Bihar Health Dashboard</div>
                <div class="header-subtitle">Statewide Operations & Pathology Management</div>
            </div>
        </div>
        <div class="header-right">
            <div class="status-badge"><div class="status-dot"></div> System Active</div>
            <div class="header-date">Refreshed: --</div>
        </div>
    </div>
    <div class="info-banner" style="background-color:#EFF6FF; border:1px solid #BFDBFE; border-radius:8px; padding:16px; color:#1E3A8A; display:flex; align-items:center; gap:12px; margin-top:20px;">
        <span style="font-size: 20px;">👈</span><span style="font-weight: 500;">Please upload the Main Data File from the sidebar to begin.</span>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

st.markdown(f"""
<div class="app-header">
    <div class="header-left">
        <div class="header-icon">🏥</div>
        <div>
            <div class="header-title">Bihar Health Dashboard</div>
            <div class="header-subtitle">Statewide Operations & Pathology Management</div>
        </div>
    </div>
    <div class="header-right">
        <div class="status-badge"><div class="status-dot"></div> System Active</div>
        <div class="header-date">Refreshed: {pd.Timestamp.now().strftime('%d %b %Y, %H:%M')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

view_mode = st.radio("Navigation", ["📊 District View", "🌐 State View", "⚠️ Zero-Sample Tracker"], horizontal=True, label_visibility="collapsed")

with st.expander("ℹ️ Metric Definitions & Grading System"):
    st.markdown("""
    **📊 Weighted Avg / Day** — *The efficiency score.*  
    Total patients divided by (facilities × days). This accounts for all facility-days equally.
    
    **⏱️ Uptime %** — *The reliability score.*  
    The percentage of days each facility reported more than 0 patients.
    
    **📉 Zero Days** — *The failure indicator.*  
    The total number of days a facility reported exactly 0 patients.
    
    **🏆 Grading System**  
    Grades are assigned based on a combination of Uptime (Reliability) and Average Patients (Volume):
    """)
    
    grade_data = pd.DataFrame({
        "Grade": ["A (Excellent)", "B (Good)", "C (Fair)", "D (Poor)", "F (Critical)"],
        "Uptime Requirement": ["> 85%", "> 70%", "> 50%", "> 30%", "< 30%"],
        "Avg Patients Requirement": ["> 10", "> 5", "> 2", "> 1", "0"]
    })
    
    st.dataframe(
        grade_data, hide_index=True, use_container_width=True,
        column_config={
            "Grade": st.column_config.TextColumn("Grade", width="medium"),
            "Uptime Requirement": st.column_config.TextColumn("Uptime Requirement", width="medium"),
            "Avg Patients Requirement": st.column_config.TextColumn("Avg Patients Requirement", width="medium"),
        }
    )
st.markdown("<br>", unsafe_allow_html=True)

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
if view_mode == "📊 District View":
    col_d, col_h = st.columns(2)
    with col_d: selected_district_zm = st.selectbox("Select District", sorted(DISTRICT_TO_ZM.keys()))
    with col_h:
        zm_name_for_district = DISTRICT_TO_ZM.get(selected_district_zm, "Unknown")
        selected_hub_zm = st.selectbox("Select Hub", sorted(ZM_DATA[zm_name_for_district][selected_district_zm]))

    zone_name = zm_name_for_district.split("(")[1].replace(")", "").strip() + " Zone" if "(" in zm_name_for_district else "Unknown Zone"
    display_zm = zm_name_for_district.split("(")[0].strip() if "(" in zm_name_for_district else zm_name_for_district
    st.markdown(f'<div class="zm-card"><div class="zm-card-header">Zone Manager</div><div class="zm-card-name">{display_zm}</div><div class="zm-card-zone">{zone_name}</div></div>', unsafe_allow_html=True)

    target_district = DISTRICT_MAP.get(selected_district_zm, selected_district_zm)
    sheet_found = any(s == target_district or target_district.lower() in s.lower() for s in available_sheets)
    sheet_to_load = next((s for s in available_sheets if s == target_district or target_district.lower() in s.lower()), None)
            
    if not sheet_found:
        st.warning(f"⏳ **Data Not Yet Available for {selected_district_zm}**"); st.stop()
        
    df_raw = read_sheet_robust(xls, sheet_to_load)
    plot_df, _, stats = process_district_df(df_raw, time_filter, start_date, end_date)
    if plot_df is None: st.error(f"Could not process data."); st.stop()
    facility_col = stats['facility_col']

    d_tab1, d_tab2, d_tab3, d_tab4 = st.tabs(["Dashboard", "Report Card", "Trends & Analytics", "🩺 Diagnosis"])

    with d_tab1:
        st.markdown(f'''
        <div class="metric-grid">
            <div class="metric-card"><div class="metric-label">Total Patients</div><div class="metric-value">{stats['total']:,}</div></div>
            <div class="metric-card"><div class="metric-label">Weighted Avg / Day</div><div class="metric-value">{stats['weighted_avg']}</div></div>
            <div class="metric-card"><div class="metric-label">Facility Uptime</div><div class="metric-value">{calc_uptime(stats)}%</div></div>
        </div>
        ''', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1: metric_option = st.radio("Metric:", ("Average Patients", "Total Patients", "Uptime %"), horizontal=True, key="d1")
        with c2: sort_option = st.selectbox("Sort:", ["Highest to Lowest", "Lowest to Highest"], key="d2")
        with c3: active_only = st.checkbox("Exclude Inactive", value=False, key="d3")
        
        metric_col = {'Average Patients': 'Average Patients', 'Total Patients': 'Total Patients', 'Uptime %': 'Uptime %'}[metric_option]
        filtered = plot_df.copy()
        if active_only: filtered = filtered[filtered['Total Patients'] > 0]
            
        if filtered.empty: st.warning("No data matches the filters.")
        else:
            sorted_df = filtered.sort_values(by=metric_col, ascending=(sort_option == "Lowest to Highest"))
            sorted_df['Highlight'] = 'Others'
            if len(sorted_df) > 10:
                sorted_df.loc[sorted_df.nlargest(5, metric_col).index, 'Highlight'] = 'Top 5'
                sorted_df.loc[sorted_df.nsmallest(5, metric_col).index, 'Highlight'] = 'Bottom 5'
            
            text_labels = [f"{v:.1f}%" if metric_col == 'Uptime %' else (f"{v:.1f}" if v % 1 != 0 else f"{int(v)}") for v in sorted_df[metric_col]]
                
            fig = px.bar(sorted_df, y=facility_col, x=metric_col, orientation='h', color='Highlight', color_discrete_map={'Top 5': '#10B981', 'Bottom 5': '#EF4444', 'Others': '#94A3B8'}, text=text_labels, title=f"<b>{metric_option} per Facility</b><br><span style='font-size:13px;color:#64748B;font-weight:500;'>{selected_district_zm} District | {date_range_str}</span>")
            
            current_avg = round(filtered[metric_col].mean(), 1) if metric_col in ['Uptime %', 'Total Patients'] else round(filtered['Total Patients'].sum() / (len(filtered) * stats['num_days']), 1) if len(filtered) > 0 and stats['num_days'] > 0 else 0
                
            fig.add_vline(x=current_avg, line_dash="dash", line_color="#2563EB", line_width=2, annotation_text=f"Avg: {current_avg}", annotation_position="top right", annotation_font_color="#2563EB", annotation_font_weight="bold", annotation_bgcolor="rgba(255,255,255,0.9)", annotation_bordercolor="#2563EB", annotation_borderwidth=1, annotation_borderpad=4)
            
            layout_dict = PLOTLY_LAYOUT.copy()
            layout_dict.update(dict(
                height=max(500, len(sorted_df) * 30),
                yaxis=dict(autorange="reversed", showgrid=False, tickfont=dict(size=13, color="#1E293B", weight="bold")),
                xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#CBD5E1', tickfont=dict(size=12, color="#64748B")),
                showlegend=False,
                xaxis_title=metric_option,
                yaxis_title="",
                margin=dict(l=10, r=60, t=80, b=10)
            ))
            fig.update_layout(**layout_dict)
            
            fig.update_traces(textposition='outside', textfont=dict(color="#1E293B", size=12, weight="bold"), cliponaxis=False)
            st.plotly_chart(fig, use_container_width=True)

            # --- FEATURE: FACILITY DRILL-DOWN ---
            st.markdown("<hr style='margin: 30px 0 20px 0; border-color: #CBD5E1;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color:#0F172A; margin-bottom:10px;'>🔍 Facility Drill-Down</h4>", unsafe_allow_html=True)
            
            drill_options = ["-- Select a facility to investigate --"] + sorted_df[facility_col].tolist()
            selected_drill_facility = st.selectbox("Facility", drill_options, label_visibility="collapsed")
            
            if selected_drill_facility != "-- Select a facility to investigate --":
                fac_row = plot_df[plot_df[facility_col] == selected_drill_facility].iloc[0]
                
                m1, m2, m3 = st.columns(3)
                m1.markdown(f"<div class='metric-card'><div class='metric-label'>Avg / Day</div><div class='metric-value'>{fac_row['Average Patients']}</div></div>", unsafe_allow_html=True)
                m2.markdown(f"<div class='metric-card'><div class='metric-label'>Uptime</div><div class='metric-value'>{fac_row['Uptime %']}%</div></div>", unsafe_allow_html=True)
                m3.markdown(f"<div class='metric-card'><div class='metric-label'>Zero Days</div><div class='metric-value'>{fac_row['Zero Days']}</div></div>", unsafe_allow_html=True)
                
                drill_trend = [{'Date': extract_date(c), 'Patients': fac_row[c]} for c in stats['active_date_cols'] if pd.notna(extract_date(c))]
                if drill_trend:
                    dt_df = pd.DataFrame(drill_trend).sort_values('Date')
                    fig_dt = px.area(dt_df, x='Date', y='Patients', markers=True)
                    fig_dt.update_traces(line_color='#2563EB', line_width=3, marker=dict(size=6, color='#FFFFFF', line=dict(width=2, color='#2563EB')), fillcolor='rgba(37, 99, 235, 0.1)')
                    
                    dt_layout = PLOTLY_LAYOUT.copy()
                    dt_layout.update(dict(
                        height=300,
                        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#CBD5E1'),
                        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='#CBD5E1'),
                        margin=dict(l=10, r=10, t=20, b=10)
                    ))
                    fig_dt.update_layout(**dt_layout)
                    
                    st.plotly_chart(fig_dt, use_container_width=True)

    with d_tab2:
        period_str = "N/A"
        if stats['active_date_cols']:
            fd, ld = extract_date(stats['active_date_cols'][0]), extract_date(stats['active_date_cols'][-1])
            if pd.notna(fd) and pd.notna(ld): period_str = f"{fd.strftime('%d %b %Y')} – {ld.strftime('%d %b %Y')}"
        
        scorecard = plot_df.copy()
        scorecard['Grade'] = scorecard.apply(lambda r: calculate_grade(r['Uptime %'], r['Average Patients']), axis=1)
        scorecard = scorecard.sort_values(by=['Grade', 'Uptime %', 'Average Patients'], ascending=[True, False, False])
        
        d_grade = district_grade(plot_df)
        
        st.markdown(f'''
        <div class="report-header">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div class="report-title" style="margin-bottom: 0;">District Report Card — {selected_district_zm}</div>
                <div style="background-color: #EFF6FF; color: #1D4ED8; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 14px; border: 1px solid #BFDBFE; display: flex; align-items: center; gap: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    🏥 <span>Total Spokes: {stats['num_facilities']}</span>
                </div>
            </div>
            <div class="report-meta"><strong>ZM:</strong> {zm_name_for_district} &nbsp;|&nbsp; <strong>Hub:</strong> {selected_hub_zm} &nbsp;|&nbsp; <strong>Period:</strong> {period_str} ({stats["num_days"]} days)</div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown(f'''
        <div class="metric-grid">
            <div class="metric-card"><div class="metric-label">Total Patients</div><div class="metric-value">{stats['total']:,}</div></div>
            <div class="metric-card"><div class="metric-label">Weighted Avg / Day</div><div class="metric-value">{stats['weighted_avg']}</div></div>
            <div class="metric-card"><div class="metric-label">Facility Uptime</div><div class="metric-value">{calc_uptime(stats)}%</div></div>
            <div class="metric-card" style="background-color:#F8FAFC;"><div class="metric-label">District Grade</div><div><span class="grade-badge grade-{d_grade}">{d_grade}</span></div></div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown("<h4 style='color:#0F172A; margin-top:20px; margin-bottom:10px;'>Spoke Scorecard</h4>", unsafe_allow_html=True)
        display = pd.DataFrame()
        display['Facility'] = scorecard[facility_col]
        display['Grade'] = scorecard['Grade'].apply(grade_emoji)
        display['Uptime %'] = scorecard['Uptime %']
        display['Avg / Day'] = scorecard['Average Patients']
        display['Total Patients'] = scorecard['Total Patients'].astype(int)
        display['Zero Days'] = scorecard['Zero Days'].astype(int)
        
        st.dataframe(display, use_container_width=True, hide_index=True, column_config={"Facility": st.column_config.TextColumn("Facility", width="large"), "Grade": st.column_config.TextColumn("Grade", width="small"), "Uptime %": st.column_config.NumberColumn("Uptime %", format="%.1f%%"), "Avg / Day": st.column_config.NumberColumn("Avg / Day", format="%.1f"), "Total Patients": st.column_config.NumberColumn("Total Patients", format="%d"), "Zero Days": st.column_config.NumberColumn("Zero Days", format="%d")})
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_dl1, col_dl2 = st.columns([1, 2])
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            summary_df = pd.DataFrame({
                'Metric': ['District', 'ZM', 'Hub', 'Period', 'Total Patients', 'Weighted Avg / Day', 'Facility Uptime', 'District Grade'],
                'Value': [selected_district_zm, zm_name_for_district, selected_hub_zm, date_range_str, stats['total'], stats['weighted_avg'], f"{calc_uptime(stats)}%", d_grade]
            })
            summary_df.to_excel(writer, index=False, sheet_name='Summary')
            display.to_excel(writer, index=False, sheet_name='Scorecard')
            
        with col_dl1:
            st.download_button(
                label="📥 Download Excel Report",
                data=buffer.getvalue(),
                file_name=f"{selected_district_zm}_Report_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        with col_dl2:
            st.info("The Excel file contains two sheets: one for the District Summary and one for the full Spoke Scorecard.")

    with d_tab3:
        st.markdown("<h4 style='color:#0F172A; margin-bottom:10px;'>Daily Patient Trend</h4>", unsafe_allow_html=True)
        if stats['active_date_cols']:
            trend_data = [{'Date': extract_date(c), 'Patients': pd.to_numeric(plot_df[c], errors='coerce').fillna(0).sum()} for c in stats['active_date_cols'] if pd.notna(extract_date(c))]
            if trend_data:
                fig_t = px.area(pd.DataFrame(trend_data).sort_values('Date'), x='Date', y='Patients', markers=True)
                fig_t.update_traces(line_color='#2563EB', line_width=3, marker=dict(size=6, color='#FFFFFF', line=dict(width=2, color='#2563EB')), fillcolor='rgba(37, 99, 235, 0.1)')
                fig_t.update_layout(**PLOTLY_LAYOUT)
                st.plotly_chart(fig_t, use_container_width=True)
                
        st.markdown("<h4 style='color:#0F172A; margin-top:30px; margin-bottom:10px;'>Spoke Heatmap</h4>", unsafe_allow_html=True)
        if stats['active_date_cols']:
            heatmap_df = plot_df.set_index(facility_col)[stats['active_date_cols']].copy()
            heatmap_df['Total'] = heatmap_df.sum(axis=1)
            heatmap_df = heatmap_df.sort_values(by='Total', ascending=True).drop(columns=['Total'])
            
            _new_cols = []
            _seen = {}
            for _c in heatmap_df.columns:
                _d = extract_date(_c)
                _lbl = _d.strftime('%d %b') if pd.notna(_d) else str(_c)
                if _lbl in _seen:
                    _seen[_lbl] += 1
                    _lbl = f"{_lbl} ({_seen[_lbl]})"
                else:
                    _seen[_lbl] = 0
                _new_cols.append(_lbl)
            heatmap_df.columns = _new_cols

            fig_h = px.imshow(heatmap_df, aspect='auto', color_continuous_scale=[[0, '#F8FAFC'], [0.1, '#DBEAFE'], [1, '#1E3A8A']], labels=dict(x="Date", y="", color="Patients"))
            fig_h.update_traces(xgap=2, ygap=2)
            
            hm_layout = PLOTLY_LAYOUT.copy()
            hm_layout.update(dict(
                height=max(400, len(heatmap_df) * 35),
                yaxis=dict(tickfont=dict(size=12, color="#1E293B", weight="bold")),
                xaxis=dict(tickfont=dict(size=11, color="#475569")),
                coloraxis_colorbar=dict(title="Patients", thickness=15)
            ))
            fig_h.update_layout(**hm_layout)
            st.plotly_chart(fig_h, use_container_width=True)
        else:
            st.info("No date data available to display heatmap.")

    # ==============================================================================
    # NEW TAB: DIAGNOSIS
    # ==============================================================================
    with d_tab4:
        st.markdown("<h4 style='color:#0F172A; margin-bottom:10px;'>🩺 Diagnosis & Root Cause Analysis</h4>", unsafe_allow_html=True)
        text_records = stats.get('text_records', [])
        
        if not text_records:
            st.success("✅ No text notes (reasons) were found for this district in the selected time range. All zero days are pure numerical zeroes.")
        else:
            df_texts = pd.DataFrame(text_records)
            
            top_cat = df_texts['Category'].value_counts().idxmax() if not df_texts.empty else "N/A"
            worst_fac = plot_df.nsmallest(1, 'Uptime %')[facility_col].iloc[0] if not plot_df.empty else "N/A"
            
            st.markdown(f'''
            <div class="metric-grid" style="grid-template-columns: repeat(3, 1fr);">
                <div class="metric-card"><div class="metric-label">Total Missing Days (Zero Days)</div><div class="metric-value">{stats['zero_days']}</div></div>
                <div class="metric-card"><div class="metric-label">Top Problem Category</div><div class="metric-value" style="font-size: 20px;">{top_cat}</div></div>
                <div class="metric-card"><div class="metric-label">Worst Facility (Lowest Uptime)</div><div class="metric-value" style="font-size: 18px;">{worst_fac}</div></div>
            </div>
            ''', unsafe_allow_html=True)

            st.markdown("<h5 style='color:#0F172A; margin-top:20px;'>Root Cause Breakdown</h5>", unsafe_allow_html=True)
            cat_counts = df_texts['Category'].value_counts().reset_index()
            cat_counts.columns = ['Category', 'Count']
            
            fig_diag = px.bar(cat_counts, x='Count', y='Category', orientation='h', color='Category', 
                              color_discrete_sequence=['#EF4444', '#F59E0B', '#10B981', '#64748B'])
            fig_diag.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False, xaxis_title="Days Affected", yaxis_title="")
            st.plotly_chart(fig_diag, use_container_width=True)

            st.markdown("<h5 style='color:#0F172A; margin-top:20px;'>Facility Offenders</h5>", unsafe_allow_html=True)
            offense_data = []
            for _, row in plot_df.iterrows():
                fac_name = row[facility_col]
                z_days = row['Zero Days']
                if z_days > 0:
                    fac_texts = df_texts[df_texts['Facility'] == fac_name]
                    primary_reason = fac_texts['Raw_Note'].value_counts().idxmax() if not fac_texts.empty else "Unknown / No Note"
                    offense_data.append({
                        'Facility': fac_name,
                        'Zero Days': z_days,
                        'Uptime %': row['Uptime %'],
                        'Primary Reason': primary_reason
                    })
            if offense_data:
                offense_df = pd.DataFrame(offense_data).sort_values('Zero Days', ascending=False)
                st.dataframe(offense_df, use_container_width=True, hide_index=True)
            else:
                st.info("No facilities had zero days in this period.")

# ==============================================================================
# VIEW: STATE VIEW
# ==============================================================================
elif view_mode == "🌐 State View":
    st.markdown("<h3 style='color:#0F172A; margin-bottom:20px;'>Bihar State Master View</h3>", unsafe_allow_html=True)
    
    with st.spinner("Loading State Data..."):
        state_df, anchor_date = calculate_all_districts(tuple(available_sheets), file_bytes, time_filter)
        
    if not state_df.empty:
        total_active = state_df['Active Spokes'].sum()
        total_facilities = state_df['Facilities'].sum()
        avg_state_uptime = round(state_df['Uptime %'].mean(), 1)
        
        if time_filter == "All Available Data" and anchor_date:
            st.caption(f"ℹ️ **Statewide Totals are anchored to {anchor_date.strftime('%d %b %Y')}.** Data after this date is excluded to ensure a fair comparison across all districts.")
        
        st.markdown(f'''
        <div class="metric-grid" style="grid-template-columns: repeat(2, 1fr);">
            <div class="metric-card">
                <div class="metric-label">Active Spokes (Latest Date)</div>
                <div class="metric-value">{total_active} <span class="metric-sub">/ {total_facilities} Total</span></div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Statewide Avg Uptime</div>
                <div class="metric-value">{avg_state_uptime}%</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        s_tab1, s_tab2 = st.tabs(["Leaderboard", "District vs District"])
        with s_tab1:
            state_metric_label = st.radio("Rank & Compare by:", ["Total Patient Count", "Weighted Avg", "Uptime %"], horizontal=True)
            state_metric_col = {"Total Patient Count": "Total Patients", "Weighted Avg": "Weighted Avg", "Uptime %": "Uptime %"}[state_metric_label]
            lb_df = state_df.copy()
            if state_metric_col == "Weighted Avg":
                lb_df = lb_df[lb_df['Days Reported'] >= 7]
                st.caption("⚠️ Districts with less than 7 days of data are hidden to ensure fair comparison.")
            lb_df = lb_df.sort_values(state_metric_col, ascending=False).reset_index(drop=True)
            lb_df.index = lb_df.index + 1; lb_df.index.name = 'Rank'
            def medal(r): return "🥇" if r == 1 else "🥈" if r == 2 else "🥉" if r == 3 else ""
            lb_df['District'] = lb_df.apply(lambda row: f"{medal(row.name)} {row['District']}".strip(), axis=1)
            st.dataframe(lb_df, use_container_width=True, column_config={"Uptime %": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100)})
            
            st.markdown(f"<h4 style='color:#0F172A; margin-top:20px; margin-bottom:10px;'>Top 15 Districts (Ranked by {state_metric_label})</h4>", unsafe_allow_html=True)
            top15 = lb_df.head(15)
            fig_lb = px.bar(top15, x=state_metric_col, y='District', orientation='h', color='Uptime %', color_continuous_scale='Blues')
            
            lb_layout = PLOTLY_LAYOUT.copy()
            lb_layout.update(dict(
                yaxis=dict(autorange="reversed", showgrid=False, tickfont=dict(size=13, color="#1E293B", weight="bold")), 
                height=500
            ))
            fig_lb.update_layout(**lb_layout)
            st.plotly_chart(fig_lb, use_container_width=True)
            
        with s_tab2:
            sorted_sheets = sorted(available_sheets)
            ca, cb = st.columns(2)
            with ca: district_a = st.selectbox("District A", sorted_sheets, index=0, key='cmp_a')
            with cb: district_b = st.selectbox("District B", sorted_sheets, index=min(1, len(sorted_sheets) - 1), key='cmp_b')
            
            if district_a and district_b:
                df_a = read_sheet_robust(xls, district_a); df_b = read_sheet_robust(xls, district_b)
                pa, ra, sa = process_district_df(df_a, time_filter, anchor_date=anchor_date); pb, rb, sb = process_district_df(df_b, time_filter, anchor_date=anchor_date)
                if pa is None or pb is None: st.error("Could not process one of the selected districts.")
                else:
                    col1, col2 = st.columns(2)
                    with col1: st.markdown(f'<div class="battle-card battle-card-blue"><div class="battle-title" style="color: #2563EB;">{district_a}</div><div class="battle-row"><span>Total Patients</span> <span class="battle-val">{sa["total"]:,}</span></div><div class="battle-row"><span>Weighted Avg / Day</span> <span class="battle-val">{sa["weighted_avg"]}</span></div><div class="battle-row"><span>Facility Uptime</span> <span class="battle-val">{calc_uptime(sa)}%</span></div><div class="battle-row"><span>Total Spokes</span> <span class="battle-val">{sa["total_absolute_facilities"]}</span></div></div>', unsafe_allow_html=True)
                    with col2: st.markdown(f'<div class="battle-card battle-card-red"><div class="battle-title" style="color: #DC2626;">{district_b}</div><div class="battle-row"><span>Total Patients</span> <span class="battle-val">{sb["total"]:,}</span></div><div class="battle-row"><span>Weighted Avg / Day</span> <span class="battle-val">{sb["weighted_avg"]}</span></div><div class="battle-row"><span>Facility Uptime</span> <span class="battle-val">{calc_uptime(sb)}%</span></div><div class="battle-row"><span>Total Spokes</span> <span class="battle-val">{sb["total_absolute_facilities"]}</span></div></div>', unsafe_allow_html=True)
                    
                    st.markdown("#### Daily Patient Trend — Overlaid")
                    def get_trend(p, cols, name):
                        d = []
                        for c in cols:
                            dv = extract_date(c); t = pd.to_numeric(p[c], errors='coerce').fillna(0).sum()
                            if pd.notna(dv): d.append({'Date': dv, 'Patients': t, 'District': name})
                        return pd.DataFrame(d)
                    combined = pd.concat([get_trend(pa, sa['active_date_cols'], district_a), get_trend(pb, sb['active_date_cols'], district_b)])
                    fig_c = px.line(combined, x='Date', y='Patients', color='District', markers=True, color_discrete_map={district_a: '#2563EB', district_b: '#DC2626'})
                    
                    cmp_layout = PLOTLY_LAYOUT.copy()
                    cmp_layout.update(dict(
                        height=450,
                        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#CBD5E1'), 
                        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='#CBD5E1')
                    ))
                    fig_c.update_layout(**cmp_layout)
                    
                    st.plotly_chart(fig_c, use_container_width=True)
    else:
        st.warning("No district data available for the selected time range.")

# ==============================================================================
# VIEW: ZERO-SAMPLE TRACKER
# ==============================================================================
else:
    st.markdown("<h3 style='color:#0F172A; margin-bottom:20px;'>⚠️ Statewide Zero-Sample Tracker</h3>", unsafe_allow_html=True)
    st.markdown("This table lists all facilities that are **currently inactive** (a streak of 0 patients ending on the latest date).")
    
    col_filter, _ = st.columns([1, 2])
    with col_filter:
        streak_threshold = st.selectbox("Show facilities inactive for at least:", [7, 14, 21, 30], format_func=lambda x: f"{x} days")
    
    with st.spinner("Scanning all districts for inactive facilities..."):
        tracker_df = generate_zero_tracker_data(tuple(available_sheets), file_bytes)
        
    if not tracker_df.empty:
        filtered_tracker = tracker_df[tracker_df['Inactive Days'] >= streak_threshold].copy()
        
        if not filtered_tracker.empty:
            total_inactive = len(filtered_tracker)
            critical_count = len(filtered_tracker[filtered_tracker['Severity'] == "🔴 Critical"])
            high_risk_count = len(filtered_tracker[filtered_tracker['Severity'] == "🟠 High Risk"])
            
            st.markdown(f'''
            <div class="metric-grid" style="grid-template-columns: repeat(3, 1fr);">
                <div class="metric-card">
                    <div class="metric-label">Total Inactive Facilities</div>
                    <div class="metric-value">{total_inactive}</div>
                </div>
                <div class="metric-card" style="border-left: 4px solid #DC2626;">
                    <div class="metric-label">Critical (30+ Days)</div>
                    <div class="metric-value" style="color:#DC2626;">{critical_count}</div>
                </div>
                <div class="metric-card" style="border-left: 4px solid #F97316;">
                    <div class="metric-label">High Risk (15-29 Days)</div>
                    <div class="metric-value" style="color:#F97316;">{high_risk_count}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            display_tracker = filtered_tracker.copy()
            display_tracker = display_tracker.reset_index(drop=True)
            display_tracker.index = display_tracker.index + 1
            display_tracker.index.name = 'S.No.'
            display_tracker = display_tracker.reset_index()
            
            display_tracker = display_tracker[['S.No.', 'Severity', 'ZM', 'District', 'Facility Name', 'Last Active Date', 'Inactive Days', 'Primary Reason']]
            
            st.dataframe(
                display_tracker, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "S.No.": st.column_config.NumberColumn("S.No.", width="small"),
                    "Severity": st.column_config.TextColumn("Severity", width="small"),
                    "ZM": st.column_config.TextColumn("Zone Manager", width="medium"),
                    "District": st.column_config.TextColumn("District", width="medium"),
                    "Facility Name": st.column_config.TextColumn("Facility Name", width="large"),
                    "Last Active Date": st.column_config.TextColumn("Last Active Date", width="medium"),
                    "Inactive Days": st.column_config.NumberColumn("Inactive Days", format="%d days"),
                    "Primary Reason": st.column_config.TextColumn("Primary Reason", width="large"),
                }
            )
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                display_tracker.to_excel(writer, index=False, sheet_name='Inactive Facilities')
                
            st.download_button(
                label=f"📥 Download List ({streak_threshold}+ Days)",
                data=buffer.getvalue(),
                file_name=f"Statewide_Inactive_Tracker_{streak_threshold}Days_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.success(f"✅ Excellent! No facilities found with an inactive streak of {streak_threshold}+ days.")
    else:
        st.success("✅ Excellent! No facilities found with any inactive streaks in the state.")