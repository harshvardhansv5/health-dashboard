import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta, datetime
import re
import io

# --- PAGE SETUP ---
st.set_page_config(page_title="Bihar Health Dashboard", page_icon="🏥", layout="wide")

# --- CLEAN ENTERPRISE UI CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    .material-symbols-rounded, [data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }
    .stApp { background-color: #F8FAFC !important; }
    section[data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
    
    /* Metric Cards */
    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .metric-card {
        background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px;
        padding: 20px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1); display: flex; flex-direction: column;
    }
    .metric-label { color: #64748B; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
    .metric-value { color: #0F172A; font-size: 28px; font-weight: 700; line-height: 1; }

    /* Tables & Cards */
    [data-testid="stDataFrame"] { background-color: #FFFFFF !important; border-radius: 10px; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.1); padding: 4px; }
    .zm-card { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin-bottom: 24px; }
    .zm-card-header { color: #64748B; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 4px;}
    .zm-card-name { color: #0F172A; font-size: 15px; font-weight: 600; margin-bottom: 2px;}
    .zm-card-zone { color: #2563EB; font-size: 13px; font-weight: 500;}

    /* Report Header */
    .report-header { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.1); }
    .report-title { color: #0F172A; font-size: 22px; font-weight: 700; margin-bottom: 8px; }
    .report-meta { color: #64748B; font-size: 14px; line-height: 1.6; }
    
    /* Grades */
    .grade-badge { display: inline-block; padding: 6px 16px; border-radius: 6px; font-size: 20px; font-weight: 700; }
    .grade-A { background-color: #D1FAE5; color: #065F46; border: 1px solid #34D399; }
    .grade-B { background-color: #ECFCCB; color: #3F6212; border: 1px solid #A3E635; }
    .grade-C { background-color: #FEF3C7; color: #92400E; border: 1px solid #FBBF24; }
    .grade-D { background-color: #FFEDD5; color: #9A3412; border: 1px solid #FB923C; }
    .grade-F { background-color: #FEE2E2; color: #991B1B; border: 1px solid #F87171; }

    /* Header */
    .app-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 24px; background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.05); margin-bottom: 20px; }
    .header-left { display: flex; align-items: center; gap: 16px; }
    .header-icon { display: flex; align-items: center; justify-content: center; width: 44px; height: 44px; background-color: #EFF6FF; border-radius: 10px; font-size: 22px; }
    .header-title { font-size: 22px; font-weight: 700; color: #0F172A; letter-spacing: -0.5px; }
    .header-right { display: flex; align-items: center; gap: 16px; }
    .status-badge { background-color: #D1FAE5; color: #065F46; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
    .status-dot { width: 8px; height: 8px; background-color: #10B981; border-radius: 50%; }
    .header-date { font-size: 13px; color: #64748B; font-weight: 500; }

    /* --- DEFINITIVE DROPDOWN STYLING --- */
    div[data-testid="stSelectbox"] { margin-bottom: 12px; }
    div[data-testid="stSelectbox"] div[role="combobox"] { background-color: #F8FAFC !important; border: 2px solid #CBD5E1 !important; border-radius: 8px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important; transition: all 0.2s ease-in-out !important; min-height: 44px !important; }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div { background-color: transparent !important; border: none !important; }
    div[data-testid="stSelectbox"] div[role="combobox"]:hover { border-color: #2563EB !important; background-color: #FFFFFF !important; }
    div[data-testid="stSelectbox"] div[role="combobox"]:focus-within { border-color: #2563EB !important; background-color: #FFFFFF !important; box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2) !important; }
    div[data-testid="stSelectbox"] div[role="combobox"] * { color: #0F172A !important; font-weight: 600 !important; }
    div[data-testid="stSelectbox"] div[role="combobox"] svg { fill: #64748B !important; }
    label[data-testid="stWidgetLabel"] p { color: #1E293B !important; font-weight: 600 !important; font-size: 14px !important; margin-bottom: 4px !important; }

    /* Date Picker */
    div[data-testid="stDateInput"] div[data-baseweb="input"] { border: 2px solid #CBD5E1 !important; border-radius: 8px !important; background-color: #F8FAFC !important; min-height: 44px !important; }
    div[data-testid="stDateInput"] div[data-baseweb="input"]:focus-within { border-color: #2563EB !important; background-color: #FFFFFF !important; box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2) !important; }

    /* Segmented Control (Radio Buttons) */
    div[data-testid="stRadio"] label > div:first-child { display: none !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] { display: inline-flex !important; background-color: #F1F5F9 !important; padding: 4px !important; border-radius: 10px !important; gap: 4px !important; border: 1px solid #E2E8F0 !important; }
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
    mask &= ~df[facility_col].astype(str).str.strip().str.lower().isin(['nan', 'none', ''])
    return mask

def process_district_df(df, time_filter, start_date=None, end_date=None):
    if df is None: return None, None, None
    facility_col = find_facility_column(df)
    if not facility_col: return None, None, None
    df = df[get_facility_mask(df, facility_col)].copy()
    
    date_cols = find_date_columns(df)
    if not date_cols: return None, None, None
    paired = [(c, extract_date(c)) for c in date_cols]
    paired = [(c, d) for c, d in paired if pd.notna(d)]
    paired.sort(key=lambda x: x[1])
    sorted_cols = [c for c, d in paired]
    
    if time_filter == "Custom Range" and start_date and end_date:
        active_date_cols = [c for c, d in paired if start_date <= d.date() <= end_date]
    else:
        latest_data_idx = next((i for i in range(len(sorted_cols) - 1, -1, -1) if pd.to_numeric(df[sorted_cols[i]], errors='coerce').fillna(0).sum() > 0), len(sorted_cols) - 1)
        if time_filter == "Last 7 Days": active_date_cols = sorted_cols[max(0, latest_data_idx - 6): latest_data_idx + 1]
        elif time_filter == "Last 15 Days": active_date_cols = sorted_cols[max(0, latest_data_idx - 14): latest_data_idx + 1]
        elif time_filter == "Last 30 Days": active_date_cols = sorted_cols[max(0, latest_data_idx - 29): latest_data_idx + 1]
        else: active_date_cols = sorted_cols

    if not active_date_cols: active_date_cols = sorted_cols
    
    plot_df = df[[facility_col] + active_date_cols].copy()
    for col in active_date_cols: plot_df[col] = pd.to_numeric(plot_df[col], errors='coerce').fillna(0)
        
    plot_df['Total Patients'] = plot_df[active_date_cols].sum(axis=1)
    plot_df['Average Patients'] = plot_df[active_date_cols].mean(axis=1).round(1)
    plot_df['Zero Days'] = (plot_df[active_date_cols] == 0).sum(axis=1)
    
    district_total = int(plot_df['Total Patients'].sum())
    num_facilities = len(plot_df)
    num_days = len(active_date_cols)
    weighted_avg = round(district_total / (num_facilities * num_days), 1) if num_facilities > 0 and num_days > 0 else 0
    total_zero = int(plot_df['Zero Days'].sum())
    
    if num_days > 0: plot_df['Uptime %'] = ((num_days - plot_df['Zero Days']) / num_days * 100).round(1)
    else: plot_df['Uptime %'] = 0
        
    return plot_df, None, {'total': district_total, 'weighted_avg': weighted_avg, 'zero_days': total_zero, 'num_facilities': num_facilities, 'num_days': num_days, 'facility_col': facility_col, 'active_date_cols': active_date_cols}

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
    return reverse_map[max(1, min(5, int(round(sum(grades) / len(grades)))))] if grades else "F"

def grade_emoji(g): return {"A": "🟢 A", "B": "🟢 B", "C": "🟡 C", "D": "🟠 D", "F": "🔴 F"}.get(g, g)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color:#0F172A; margin-bottom:20px;'>Control Panel</h3>", unsafe_allow_html=True)
    uploaded_data_file = st.file_uploader("Upload Data File", type=["xlsx", "csv"])
    
    if uploaded_data_file is not None:
        try:
            file_bytes = uploaded_data_file.getvalue()
            xls = pd.ExcelFile(uploaded_data_file)
            available_sheets = xls.sheet_names
            
            st.markdown("<hr style='margin: 20px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
            
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
        <div class="header-left"><div class="header-icon">🏥</div><div class="header-title">Bihar Health Dashboard</div></div>
        <div class="header-right"><div class="status-badge"><div class="status-dot"></div> System Active</div></div>
    </div>
    <div class="info-banner" style="background-color:#EFF6FF; border:1px solid #BFDBFE; border-radius:8px; padding:16px; color:#1E3A8A; display:flex; align-items:center; gap:12px; margin-top:20px;">
        <span style="font-size: 20px;">👈</span><span style="font-weight: 500;">Please upload the Main Data File from the sidebar to begin.</span>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

st.markdown(f"""
<div class="app-header">
    <div class="header-left"><div class="header-icon">🏥</div><div class="header-title">Bihar Health Dashboard</div></div>
    <div class="header-right">
        <div class="status-badge"><div class="status-dot"></div> System Active</div>
        <div class="header-date">Refreshed: {pd.Timestamp.now().strftime('%d %b %Y, %H:%M')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

view_mode = st.radio("Navigation", ["📊 District View", "🌐 State View"], horizontal=True, label_visibility="collapsed")

with st.expander("ℹ️ Metric Definitions & Grading System"):
    st.markdown("""
    **📊 Weighted Avg / Day** — *The efficiency score.* Total patients divided by (facilities × days). This accounts for all facility-days equally.
    **⏱️ Uptime %** — *The reliability score.* The percentage of days each facility reported more than 0 patients. 
    **📉 Zero Days** — *The failure indicator.* The total number of days a facility reported exactly 0 patients.
    **🏆 Grading System** — **A (Excellent):** Uptime > 85% AND Avg > 10 | **B (Good):** Uptime > 70% AND Avg > 5 | **C (Fair):** Uptime > 50% AND Avg > 2 | **D (Poor):** Uptime > 30% AND Avg > 1 | **F (Critical):** Uptime < 30% OR Avg = 0
    """)
st.markdown("<br>", unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(template="plotly_white", font=dict(family="Inter, sans-serif", size=13, color="#475569"), title_font=dict(size=16, color="#0F172A", family="Inter, sans-serif", weight="bold"), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=60, b=10))

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

    d_tab1, d_tab2, d_tab3 = st.tabs(["Dashboard", "Report Card", "Trends & Analytics"])

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
            layout_dict["margin"] = dict(l=10, r=60, t=80, b=10)
            fig.update_layout(**layout_dict, height=max(500, len(sorted_df) * 30), yaxis=dict(autorange="reversed", showgrid=False, tickfont=dict(size=13, color="#1E293B", weight="bold")), xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#E2E8F0', tickfont=dict(size=12, color="#64748B")), showlegend=False, xaxis_title=metric_option, yaxis_title="")
            
            fig.update_traces(textposition='outside', textfont=dict(color="#1E293B", size=12, weight="bold"), cliponaxis=False)
            st.plotly_chart(fig, use_container_width=True)

            # --- FEATURE: FACILITY DRILL-DOWN ---
            st.markdown("<hr style='margin: 30px 0 20px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
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
                    dt_layout["margin"] = dict(l=10, r=10, t=20, b=10)
                    fig_dt.update_layout(**dt_layout, height=300, xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#E2E8F0'), yaxis=dict(showgrid=True, gridwidth=1, gridcolor='#E2E8F0'))
                    
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
            <div class="report-title">District Report Card — {selected_district_zm}</div>
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
        
        # --- FEATURE: EXCEL EXPORT ---
        col_dl1, col_dl2 = st.columns([1, 2])
        
        # Prepare the Excel file in memory
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Sheet 1: Summary
            summary_df = pd.DataFrame({
                'Metric': ['District', 'ZM', 'Hub', 'Period', 'Total Patients', 'Weighted Avg / Day', 'Facility Uptime', 'District Grade'],
                'Value': [selected_district_zm, zm_name_for_district, selected_hub_zm, date_range_str, stats['total'], stats['weighted_avg'], f"{calc_uptime(stats)}%", d_grade]
            })
            summary_df.to_excel(writer, index=False, sheet_name='Summary')
            
            # Sheet 2: Scorecard
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
                fig_t.update_layout(**PLOTLY_LAYOUT, xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#E2E8F0'), yaxis=dict(showgrid=True, gridwidth=1, gridcolor='#E2E8F0'))
                st.plotly_chart(fig_t, use_container_width=True)
                
        st.markdown("<h4 style='color:#0F172A; margin-top:30px; margin-bottom:10px;'>Spoke Heatmap</h4>", unsafe_allow_html=True)
        heatmap_df = plot_df.set_index(facility_col)[stats['active_date_cols']].copy()
        heatmap_df['Total'] = heatmap_df.sum(axis=1)
        heatmap_df = heatmap_df.sort_values(by='Total', ascending=True).drop(columns=['Total'])
        heatmap_df.columns = [extract_date(c).strftime('%d %b') if pd.notna(extract_date(c)) else c for c in heatmap_df.columns]

        fig_h = px.imshow(heatmap_df, aspect='auto', color_continuous_scale=[[0, '#F8FAFC'], [0.1, '#DBEAFE'], [1, '#1E3A8A']], labels=dict(x="Date", y="", color="Patients"))
        fig_h.update_traces(xgap=2, ygap=2)
        fig_h.update_layout(**PLOTLY_LAYOUT, height=max(400, len(heatmap_df) * 35), yaxis=dict(tickfont=dict(size=12, color="#1E293B", weight="bold")), xaxis=dict(tickfont=dict(size=11, color="#475569")), coloraxis_colorbar=dict(title="Patients", thickness=15))
        st.plotly_chart(fig_h, use_container_width=True)

# ==============================================================================
# VIEW: STATE VIEW
# ==============================================================================
else:
    st.markdown("<h3 style='color:#0F172A; margin-bottom:20px;'>Bihar State Master View</h3>", unsafe_allow_html=True)
    st.info("State View does not support Custom Date Ranges yet. Please switch to District View for deep-dive analysis.")