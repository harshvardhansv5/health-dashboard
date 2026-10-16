import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
import re
import io

# --- PAGE SETUP ---
st.set_page_config(page_title="Bihar Health Dashboard", page_icon="🏥", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .info-card, .metric-card, .zm-card, .report-header {
        background: linear-gradient(135deg, #1a2a3a 0%, #0E1117 100%);
        border: 1px solid #2a3a4a;
        border-radius: 10px;
        padding: 16px 20px;
    }
    .info-card {border-left: 4px solid #00D4FF;}
    .info-card.green {border-left: 4px solid #2ecc71;}
    .info-card.green .info-value {color: #2ecc71;}
    .info-label {color: #8fa5bb; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 6px;}
    .info-value {color: #FFFFFF; font-size: 17px; font-weight: 700; line-height: 1.3;}
    .info-sub {color: #8fa5bb; font-size: 12px; margin-top: 3px;}
    .info-sub.accent {color: #00D4FF; font-weight: 500;}

    .metric-card {padding: 18px 20px; border-left: 4px solid #6c757d;}
    .metric-card.blue {border-left-color: #3498db;}
    .metric-card.purple {border-left-color: #9b59b6;}
    .metric-card.green {border-left-color: #2ecc71;}
    .metric-card.yellow {border-left-color: #fbbf24;}
    .metric-card.orange {border-left-color: #f97316;}
    .metric-card.red {border-left-color: #e74c3c;}
    .metric-value {color: #FFFFFF; font-size: 30px; font-weight: 700; line-height: 1.1; margin-top: 4px;}
    .metric-label {color: #8fa5bb; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700;}
    .metric-progress-bg {background: #1a2a3a; height: 6px; border-radius: 3px; margin-top: 12px; overflow: hidden;}
    .metric-progress-fill {height: 100%; border-radius: 3px;}

    .zm-card {background: linear-gradient(135deg, #1e3a5f 0%, #0E1117 100%); border: 1px solid #2a4a6f; border-left: 4px solid #00D4FF; padding: 14px 16px; margin-top: 8px; margin-bottom: 8px;}
    .zm-card-header {color: #00D4FF; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 6px;}
    .zm-card-name {color: #FFFFFF; font-size: 15px; font-weight: 700; line-height: 1.3; margin-bottom: 4px;}
    .zm-card-zone {color: #8fa5bb; font-size: 12px; font-style: italic;}
    .zm-card-stats {color: #00D4FF; font-size: 12px; font-weight: 600; margin-top: 6px;}

    .report-header {border-left: 5px solid #00D4FF; padding: 20px 28px; margin-bottom: 20px;}
    .report-title {color: #FFFFFF; font-size: 24px; font-weight: 700; margin-bottom: 8px;}
    .report-meta {color: #8fa5bb; font-size: 14px; line-height: 1.6;}
    .report-meta strong {color: #CCCCCC;}

    .district-grade-badge {display: inline-block; padding: 6px 18px; border-radius: 8px; font-size: 22px; font-weight: 800; margin-left: 10px;}
    .grade-A {background-color: #2ecc71; color: #000;}
    .grade-B {background-color: #a3e635; color: #000;}
    .grade-C {background-color: #fbbf24; color: #000;}
    .grade-D {background-color: #f97316; color: #FFF;}
    .grade-F {background-color: #e74c3c; color: #FFF;}

    .bottom-spoke {background: #1a1010; border: 1px solid #4a2a2a; border-left: 4px solid #e74c3c; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;}
    .bottom-spoke-name {color: #FFFFFF; font-size: 13px; font-weight: 600;}
    .bottom-spoke-meta {color: #f97316; font-size: 11px; margin-top: 2px;}

    hr {border-color: #2a3a4a !important; margin: 12px 0 !important;}

    div[data-testid="stMetric"] {background-color: #1E1E1E; border: 1px solid #333333; padding: 15px; border-radius: 10px;}
    div[data-testid="stMetric"] label {color: #AAAAAA !important;}
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {color: #FFFFFF !important;}

    /* View mode pills styling */
    .view-mode-title {color: #8fa5bb; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 4px;}
</style>
""", unsafe_allow_html=True)

# --- HARDCODED ZM DATA ---
ZM_DATA = {
    "Keshav Kumar (Patna)": {"Bhojpur": ["DH Ara Bhojpur"], "Nalanda": ["DH Bihar Sharif Nalanda"], "Patna": ["DH (Guru Gobind Singh Hospital, Patna City)", "SDH Barh Patna", "SDH Danapur Patna"]},
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

DISTRICT_TO_ZM = {}
for zm_name, districts in ZM_DATA.items():
    for d in districts.keys():
        DISTRICT_TO_ZM[d] = zm_name

ZM_SHORT = {full: full.split("(")[0].strip() for full in ZM_DATA.keys()}

DISTRICT_MAP = {"Seikhpura": "Sheikhpura", "Rohtas": "Sasaram"}
REVERSE_DISTRICT_MAP = {"Sheikhpura": "Seikhpura", "Sasaram": "Rohtas", "Barh": "Patna", "Danapur": "Patna"}
HUB_TO_SHEET_MAP = {"SDH Barh Patna": "Barh", "SDH Danapur Patna": "Danapur"}

# --- HELPERS ---
def read_sheet_robust(xls, sheet_name):
    try:
        df_raw = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        header_idx = None
        for i in range(min(15, len(df_raw))):
            row = df_raw.iloc[i]
            for cell in row:
                if 'name of the hospital' in str(cell).lower():
                    header_idx = i
                    break
            if header_idx is not None:
                break
        if header_idx is None:
            df = pd.read_excel(xls, sheet_name=sheet_name)
        else:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=header_idx)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception:
        return None

def find_facility_column(df):
    for c in df.columns:
        if 'name of the hospital' in str(c).lower(): return c
    for c in df.columns:
        if 'hospital' in str(c).lower() and 'name' in str(c).lower(): return c
    for c in df.columns:
        if 'hospital' in str(c).lower(): return c
    return None

def extract_date(col_name):
    if isinstance(col_name, pd.Timestamp): return col_name
    s = str(col_name)
    match = re.search(r'(\d{4}-\d{2}-\d{2})', s)
    if match: return pd.to_datetime(match.group(1), errors='coerce')
    match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', s)
    if match: return pd.to_datetime(match.group(1), dayfirst=True, errors='coerce')
    match = re.search(r'(\d{1,2}-\w{3}-\d{2,4})', s)
    if match: return pd.to_datetime(match.group(1), errors='coerce')
    return pd.NaT

def find_date_columns(df):
    date_cols = [c for c in df.columns if 'Total number of patients' in str(c)]
    if date_cols: return date_cols
    date_cols = []
    for c in df.columns:
        parsed = extract_date(c)
        if pd.notna(parsed): date_cols.append(c)
    return date_cols

def get_facility_mask(df, facility_col):
    mask = df[facility_col].notna()
    mask &= ~df[facility_col].astype(str).str.upper().str.contains('TOTAL', na=False)
    mask &= ~df[facility_col].astype(str).str.strip().str.lower().isin(['nan', 'none', ''])
    return mask

def process_district_df(df, time_filter):
    if df is None: return None, None, None
    facility_col = find_facility_column(df)
    if not facility_col: return None, None, None
    df = df[get_facility_mask(df, facility_col)].copy()
    all_facilities = df[facility_col].dropna().tolist()
    date_cols = find_date_columns(df)
    if not date_cols: return None, None, None
    paired = [(c, extract_date(c)) for c in date_cols]
    paired = [(c, d) for c, d in paired if pd.notna(d)]
    paired.sort(key=lambda x: x[1])
    sorted_cols = [c for c, d in paired]
    latest_data_idx = -1
    for i in range(len(sorted_cols) - 1, -1, -1):
        c = sorted_cols[i]
        col_values = pd.to_numeric(df[c], errors='coerce').fillna(0)
        if col_values.sum() > 0:
            latest_data_idx = i
            break
    if latest_data_idx == -1 and sorted_cols:
        latest_data_idx = len(sorted_cols) - 1
    if time_filter == "Last 7 Days":
        active_date_cols = sorted_cols[max(0, latest_data_idx - 6): latest_data_idx + 1]
    elif time_filter == "Last 15 Days":
        active_date_cols = sorted_cols[max(0, latest_data_idx - 14): latest_data_idx + 1]
    elif time_filter == "Last 30 Days":
        active_date_cols = sorted_cols[max(0, latest_data_idx - 29): latest_data_idx + 1]
    else:
        active_date_cols = sorted_cols
    if not active_date_cols: active_date_cols = sorted_cols
    plot_df = df[[facility_col] + active_date_cols].copy()
    raw_text_df = plot_df.copy()
    for col in active_date_cols:
        plot_df[col] = pd.to_numeric(plot_df[col], errors='coerce').fillna(0)
    plot_df['Total Patients'] = plot_df[active_date_cols].sum(axis=1)
    plot_df['Average Patients'] = plot_df[active_date_cols].mean(axis=1).round(1)
    plot_df['Zero Days'] = (plot_df[active_date_cols] == 0).sum(axis=1)
    district_total = int(plot_df['Total Patients'].sum())
    num_facilities = len(plot_df)
    num_days = len(active_date_cols)
    weighted_avg = round(district_total / (num_facilities * num_days), 1) if num_facilities > 0 and num_days > 0 else 0
    total_zero = int(plot_df['Zero Days'].sum())
    if num_days > 0:
        plot_df['Uptime %'] = ((num_days - plot_df['Zero Days']) / num_days * 100).round(1)
    else:
        plot_df['Uptime %'] = 0
    return plot_df, raw_text_df, {
        'total': district_total, 'weighted_avg': weighted_avg, 'zero_days': total_zero,
        'num_facilities': num_facilities, 'num_days': num_days,
        'facility_col': facility_col, 'active_date_cols': active_date_cols
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
    avg = sum(grades) / len(grades)
    return reverse_map[max(1, min(5, int(round(avg))))]

def grade_emoji(g):
    return {"A": "🟢 A", "B": "🟢 B", "C": "🟡 C", "D": "🟠 D", "F": "🔴 F"}.get(g, g)

def uptime_color(uptime_pct):
    if uptime_pct >= 85: return "green"
    if uptime_pct >= 70: return "yellow"
    if uptime_pct >= 50: return "orange"
    return "red"

def uptime_hex(uptime_pct):
    if uptime_pct >= 85: return "#2ecc71"
    if uptime_pct >= 70: return "#fbbf24"
    if uptime_pct >= 50: return "#f97316"
    return "#e74c3c"

@st.cache_data(show_spinner=False)
def calculate_all_districts(sheet_names_tuple, uploaded_file_bytes, time_filter):
    xls = pd.ExcelFile(io.BytesIO(uploaded_file_bytes))
    data = []
    for sheet in sheet_names_tuple:
        try:
            sdf = read_sheet_robust(xls, sheet)
            pdf, _, s = process_district_df(sdf, time_filter)
            if s:
                d_grade = district_grade(pdf) if pdf is not None else "F"
                lookup_name = REVERSE_DISTRICT_MAP.get(sheet, sheet)
                zm_full = DISTRICT_TO_ZM.get(lookup_name, "—")
                zm_display = ZM_SHORT.get(zm_full, zm_full) if zm_full != "—" else "—"
                data.append({
                    'District': sheet, 'ZM': zm_display, 'ZM_Full': zm_full,
                    'Grade': d_grade, 'Total Patients': s['total'],
                    'Weighted Avg': s['weighted_avg'], 'Uptime %': calc_uptime(s),
                    'Facilities': s['num_facilities']
                })
        except Exception:
            pass
    return pd.DataFrame(data)

@st.cache_data(show_spinner=False)
def get_zm_rankings(sheet_names_tuple, uploaded_file_bytes, time_filter):
    lb = calculate_all_districts(sheet_names_tuple, uploaded_file_bytes, time_filter)
    if lb.empty: return {}
    zm_agg = lb[lb['ZM_Full'] != "—"].groupby('ZM_Full').agg(
        Districts=('District', 'count'), Total=('Total Patients', 'sum')
    ).reset_index().sort_values('Total', ascending=False).reset_index(drop=True)
    zm_agg['Rank'] = range(1, len(zm_agg) + 1)
    return dict(zip(zm_agg['ZM_Full'], zip(zm_agg['Rank'], zm_agg['Districts'])))

# ============================================================================
# TOP-LEVEL VIEW MODE SELECTOR (rendered in main area, at the top)
# ============================================================================
st.title("🏥 Bihar District Hub & Spoke Dashboard")

# Use pills if available, else fallback to radio
try:
    view_mode = st.pills(
        "view_mode_selector",
        ["🏥 District View", "🌐 State View"],
        selection_mode="single",
        default="🏥 District View",
        label_visibility="collapsed"
    )
except AttributeError:
    view_mode = st.radio(
        "view_mode_selector",
        ["🏥 District View", "🌐 State View"],
        horizontal=True,
        index=0,
        label_visibility="collapsed"
    )

if view_mode is None:
    view_mode = "🏥 District View"

# ============================================================================
# SIDEBAR — CONDITIONAL ON VIEW MODE
# ============================================================================
with st.sidebar:
    st.title("Control Panel")
    uploaded_data_file = st.file_uploader("Upload Main Data File", type=["xlsx", "csv"])

    if uploaded_data_file is not None:
        try:
            file_bytes = uploaded_data_file.getvalue()
            xls = pd.ExcelFile(uploaded_data_file)
            available_sheets = xls.sheet_names
            st.markdown("---")

            if view_mode == "🏥 District View":
                # ---- DISTRICT VIEW SIDEBAR ----
                all_districts = sorted(DISTRICT_TO_ZM.keys())
                selected_district_zm = st.selectbox("Select District", all_districts)

                zm_name_for_district = DISTRICT_TO_ZM.get(selected_district_zm, "Unknown")
                zone_name = "Unknown Zone"
                display_zm = zm_name_for_district
                if "(" in zm_name_for_district and ")" in zm_name_for_district:
                    display_zm = zm_name_for_district.split("(")[0].strip()
                    zone_name = zm_name_for_district.split("(")[1].replace(")", "").strip() + " Zone"

                districts_count = len(ZM_DATA.get(zm_name_for_district, {}))

                zm_rank_info = ""
                try:
                    ranks = get_zm_rankings(tuple(available_sheets), file_bytes, "Last 7 Days")
                    if zm_name_for_district in ranks:
                        rank, _ = ranks[zm_name_for_district]
                        zm_rank_info = f'<div class="zm-card-stats">🏆 Rank #{rank} among {len(ranks)} ZMs · Manages {districts_count} districts</div>'
                    else:
                        zm_rank_info = f'<div class="zm-card-stats">Manages {districts_count} districts</div>'
                except Exception:
                    zm_rank_info = f'<div class="zm-card-stats">Manages {districts_count} districts</div>'

                st.markdown(f'''
                <div class="zm-card">
                    <div class="zm-card-header">👤 Zone Manager</div>
                    <div class="zm-card-name">{display_zm}</div>
                    <div class="zm-card-zone">{zone_name}</div>
                    {zm_rank_info}
                </div>
                ''', unsafe_allow_html=True)

                hub_list = sorted(ZM_DATA[zm_name_for_district][selected_district_zm])
                selected_hub_zm = st.selectbox("Select Hub", hub_list)

                st.markdown("---")
                time_filter = st.selectbox("Select Time Range:",
                    ["All Available Data", "Last 7 Days", "Last 15 Days", "Last 30 Days"],
                    key="district_tf")
                st.markdown("---")

                target_district = DISTRICT_MAP.get(selected_district_zm, selected_district_zm)
                if selected_hub_zm in HUB_TO_SHEET_MAP:
                    target_district = HUB_TO_SHEET_MAP[selected_hub_zm]
                sheet_found = False
                for s in available_sheets:
                    if s == target_district or target_district.lower() in s.lower() or s.lower() in target_district.lower():
                        sheet_to_load = s
                        sheet_found = True
                        break
                if sheet_found:
                    st.success(f"✅ Data Available: {selected_district_zm}")
                else:
                    st.warning(f"⏳ Data Pending: {selected_district_zm}")

            else:
                # ---- STATE VIEW SIDEBAR ----
                st.markdown('<div class="view-mode-title">🌐 Statewide Analysis</div>', unsafe_allow_html=True)

                zm_options = ["🏢 All Zones"] + sorted(list(ZM_DATA.keys()))
                selected_zm_filter = st.selectbox("Filter by ZM:", zm_options, key="state_zm_filter")

                st.markdown("---")
                time_filter = st.selectbox("Select Time Range:",
                    ["All Available Data", "Last 7 Days", "Last 15 Days", "Last 30 Days"],
                    key="state_tf")
                st.markdown("---")

                st.success(f"✅ Ready for statewide analysis")
                st.caption(f"{len(available_sheets)} districts loaded")

        except Exception as e:
            st.error(f"Error: {e}")

# ============================================================================
# MAIN AREA ROUTING
# ============================================================================
if uploaded_data_file is None:
    st.info("👈 Please upload the Main Data File from the sidebar to begin.")
    st.stop()

# ---------------------------------------------------------------------------
# DISTRICT VIEW
# ---------------------------------------------------------------------------
if view_mode == "🏥 District View":
    if not sheet_found:
        st.warning(f"⏳ **Data Not Yet Available for {selected_district_zm}**")
        st.stop()

    df_raw = read_sheet_robust(xls, sheet_to_load)
    plot_df, raw_text_df, stats = process_district_df(df_raw, time_filter)
    if plot_df is None:
        st.error(f"Could not process the sheet '{sheet_to_load}'.")
        st.stop()
    facility_col = stats['facility_col']

    # --- COMPUTE BEST & WORST SPOKES ---
    plot_df['Grade'] = plot_df.apply(lambda r: calculate_grade(r['Uptime %'], r['Average Patients']), axis=1)
    grade_order = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'F': 5}
    plot_df['Grade_Order'] = plot_df['Grade'].map(grade_order)
    ranked_df = plot_df.sort_values(['Grade_Order', 'Average Patients'], ascending=[True, False])
    best_row = ranked_df.iloc[0] if not ranked_df.empty else None
    worst_df = ranked_df.tail(3).iloc[::-1] if len(ranked_df) >= 3 else ranked_df

    # --- 3-CARD INFO BAR ---
    uptime_val = calc_uptime(stats)
    uptime_cls = uptime_color(uptime_val)

    col1, col2, col3 = st.columns([1, 1, 1.2])
    with col1:
        st.markdown(f'''
        <div class="info-card">
            <div class="info-label">📍 Total Spokes</div>
            <div class="info-value">{stats['num_facilities']}</div>
            <div class="info-sub">Reporting facilities</div>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
        <div class="info-card">
            <div class="info-label">🏥 Hub Lab</div>
            <div class="info-value">{selected_hub_zm}</div>
            <div class="info-sub">Central processing facility</div>
        </div>
        ''', unsafe_allow_html=True)
    with col3:
        if best_row is not None:
            st.markdown(f'''
            <div class="info-card green">
                <div class="info-label">⭐ Best Performing Spoke</div>
                <div class="info-value">🏆 {best_row[facility_col]}</div>
                <div class="info-sub accent">Ranked #1 of {stats['num_facilities']} · Grade {best_row['Grade']} · {best_row['Average Patients']} /day</div>
            </div>
            ''', unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # --- 3 METRIC CARDS ---
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f'''
        <div class="metric-card blue">
            <div class="metric-label">Total Patients ({time_filter})</div>
            <div class="metric-value">{stats['total']:,}</div>
        </div>
        ''', unsafe_allow_html=True)
    with m2:
        st.markdown(f'''
        <div class="metric-card purple">
            <div class="metric-label">Weighted Avg Daily Patients</div>
            <div class="metric-value">{stats['weighted_avg']}</div>
        </div>
        ''', unsafe_allow_html=True)
    with m3:
        bar_color = uptime_hex(uptime_val)
        st.markdown(f'''
        <div class="metric-card {uptime_cls}">
            <div class="metric-label">Facility Uptime %</div>
            <div class="metric-value">{uptime_val}%</div>
            <div class="metric-progress-bg">
                <div class="metric-progress-fill" style="width: {min(uptime_val, 100)}%; background: {bar_color};"></div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # --- DISTRICT TABS ---
    tab1, tab2, tab3 = st.tabs(["📊 District Dashboard", "📋 Report Card", "📈 Trends & Analytics"])

    # ===== TAB 1: DISTRICT DASHBOARD =====
    with tab1:
        c1, c2 = st.columns([3, 2])
        with c1:
            metric_option = st.radio("Metric:", ("Average Patients", "Total Patients", "Uptime %"), horizontal=True, key="d1")
        with c2:
            cc1, cc2 = st.columns(2)
            with cc1:
                sort_option = st.selectbox("Sort:", ["Highest to Lowest", "Lowest to Highest"], key="d2", label_visibility="collapsed")
            with cc2:
                active_only = st.checkbox("Exclude Inactive", value=False, key="d3")

        metric_col = {'Average Patients': 'Average Patients', 'Total Patients': 'Total Patients', 'Uptime %': 'Uptime %'}[metric_option]
        filtered = plot_df.copy()
        if active_only:
            filtered = filtered[filtered['Total Patients'] > 0]

        if filtered.empty:
            st.warning("No data matches the filters.")
        else:
            sorted_df = filtered.sort_values(by=metric_col, ascending=(sort_option == "Lowest to Highest"))
            chart_title = f"{metric_option} per Facility — {selected_district_zm} ({time_filter}) · {len(sorted_df)} Facilities"
            fig = px.bar(
                sorted_df, y=facility_col, x=metric_col, orientation='h',
                color='Grade',
                color_discrete_map={'A': '#2ecc71', 'B': '#a3e635', 'C': '#fbbf24', 'D': '#f97316', 'F': '#e74c3c'},
                labels={facility_col: '', metric_col: metric_option, 'Grade': 'Grade'},
                title=chart_title
            )
            avg_val = sorted_df[metric_col].mean()
            fig.add_vline(x=avg_val, line_dash="dash", line_color="#e74c3c", line_width=2,
                          annotation_text=f"Avg: {avg_val:.1f}", annotation_position="top")
            chart_height = max(340, len(sorted_df) * 34)
            fig.update_layout(
                height=chart_height, yaxis=dict(autorange="reversed"),
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, title=""),
                margin=dict(l=0, r=20, t=60, b=20), font=dict(size=12)
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        left_col, right_col = st.columns([1, 2])
        with left_col:
            st.markdown("#### 🔴 Attention Needed")
            st.caption("Bottom 3 spokes by grade & volume")
            for _, row in worst_df.iterrows():
                st.markdown(f'''
                <div class="bottom-spoke">
                    <div class="bottom-spoke-name">{row[facility_col]}</div>
                    <div class="bottom-spoke-meta">Grade {row['Grade']} · Uptime {row['Uptime %']}% · {row['Average Patients']} /day</div>
                </div>
                ''', unsafe_allow_html=True)
        with right_col:
            st.markdown("#### 📋 All Facilities")
            st.caption("Sorted by grade and performance")
            display = ranked_df[[facility_col, 'Grade', 'Uptime %', 'Average Patients', 'Total Patients']].copy()
            display.columns = ['Facility', 'Grade', 'Uptime %', 'Avg / Day', 'Total']
            st.dataframe(
                display, use_container_width=True, hide_index=True,
                height=min(420, 35 * len(display) + 40),
                column_config={
                    "Facility": st.column_config.TextColumn("Facility", width="large"),
                    "Grade": st.column_config.TextColumn("Grade", width="small"),
                    "Uptime %": st.column_config.NumberColumn("Uptime %", format="%.1f%%"),
                    "Avg / Day": st.column_config.NumberColumn("Avg / Day", format="%.1f"),
                    "Total": st.column_config.NumberColumn("Total", format="%d"),
                }
            )

        st.markdown("---")
        st.caption(f"💡 Data: **{sheet_to_load}** | Range: **{time_filter}** | Refreshed: {pd.Timestamp.now().strftime('%d-%b-%Y %H:%M')}")

    # ===== TAB 2: REPORT CARD =====
    with tab2:
        period_str = "N/A"
        if stats['active_date_cols']:
            fd = extract_date(stats['active_date_cols'][0])
            ld = extract_date(stats['active_date_cols'][-1])
            if pd.notna(fd) and pd.notna(ld):
                period_str = f"{fd.strftime('%d %b %Y')} – {ld.strftime('%d %b %Y')}"
                if fd == ld: period_str = fd.strftime('%d %b %Y')

        d_grade = district_grade(plot_df)
        grade_class = f"grade-{d_grade}"

        st.markdown(f'''
        <div class="report-header">
            <div class="report-title">📋 District Report Card — {selected_district_zm}</div>
            <div class="report-meta">
                <strong>ZM:</strong> {zm_name_for_district} &nbsp;|&nbsp; 
                <strong>Hub:</strong> {selected_hub_zm} &nbsp;|&nbsp; 
                <strong>Period:</strong> {period_str} <span style="color: #666;">({stats['num_days']} days)</span>
                <br>
                <strong>Generated:</strong> {pd.Timestamp.now().strftime('%d %b %Y, %H:%M')}
            </div>
        </div>
        ''', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Total Patients", f"{stats['total']:,}")
        with col2: st.metric("Weighted Avg / Day", f"{stats['weighted_avg']}")
        with col3: st.metric("Facility Uptime", f"{calc_uptime(stats)}%")
        with col4:
            st.markdown(f'''
            <div style="background-color:#1E1E1E; border:1px solid #333; padding:15px; border-radius:10px; text-align:center;">
                <div style="color:#AAAAAA; font-size:13px; text-transform:uppercase; letter-spacing:1px;">District Grade</div>
                <div style="margin-top:8px;"><span class="district-grade-badge {grade_class}">{d_grade}</span></div>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🏥 Spoke Scorecard")
        st.caption("Every facility in the district, graded on reliability (60%) and volume (40%). Sorted best to worst.")

        scorecard = plot_df.copy()
        scorecard['Grade'] = scorecard.apply(lambda r: calculate_grade(r['Uptime %'], r['Average Patients']), axis=1)
        scorecard = scorecard.sort_values(by=['Grade', 'Uptime %', 'Average Patients'], ascending=[True, False, False])

        display = pd.DataFrame()
        display['Facility'] = scorecard[facility_col]
        display['Grade'] = scorecard['Grade'].apply(grade_emoji)
        display['Uptime %'] = scorecard['Uptime %']
        display['Avg / Day'] = scorecard['Average Patients']
        display['Total Patients'] = scorecard['Total Patients'].astype(int)
        display['Zero Days'] = scorecard['Zero Days'].astype(int)

        st.dataframe(
            display, use_container_width=True, hide_index=True,
            column_config={
                "Facility": st.column_config.TextColumn("Facility", width="large"),
                "Grade": st.column_config.TextColumn("Grade", width="small"),
                "Uptime %": st.column_config.NumberColumn("Uptime %", format="%.1f%%"),
                "Avg / Day": st.column_config.NumberColumn("Avg / Day", format="%.1f"),
                "Total Patients": st.column_config.NumberColumn("Total Patients", format="%d"),
                "Zero Days": st.column_config.NumberColumn("Zero Days", format="%d"),
            }
        )

        st.markdown("---")
        export = scorecard[[facility_col, 'Grade', 'Uptime %', 'Average Patients', 'Total Patients', 'Zero Days']].copy()
        export.columns = ['Facility', 'Grade', 'Uptime %', 'Avg Per Day', 'Total Patients', 'Zero Days']
        csv = export.to_csv(index=False).encode('utf-8')
        period_file = pd.Timestamp.now().strftime('%b_%Y')
        st.download_button(
            label=f"📥 Download Report Card ({selected_district_zm})",
            data=csv,
            file_name=f'{selected_district_zm}_ReportCard_{time_filter.replace(" ", "_")}_{period_file}.csv',
            mime='text/csv', key='download_report'
        )

    # ===== TAB 3: TRENDS & ANALYTICS =====
    with tab3:
        st.markdown(f"### 📈 Trends for {selected_district_zm}")
        st.markdown("#### Daily Patient Trend")
        if stats['active_date_cols']:
            trend_data = []
            for col in stats['active_date_cols']:
                d = extract_date(col)
                dt = pd.to_numeric(plot_df[col], errors='coerce').fillna(0).sum()
                if pd.notna(d): trend_data.append({'Date': d, 'Patients': dt})
            if trend_data:
                trend_df = pd.DataFrame(trend_data).sort_values('Date')
                trend_df['Day'] = trend_df['Date'].dt.day_name()
                holidays = {'2026-09-16': 'Milad-un-Nabi', '2026-10-02': 'Gandhi Jayanti', '2026-10-20': 'Dussehra', '2026-10-21': 'Dussehra Holiday', '2026-11-08': 'Diwali', '2026-11-10': 'Bhai Dooj', '2026-11-13': 'Chhath Day 1', '2026-11-14': 'Chhath Day 2'}
                trend_df['Holiday'] = trend_df['Date'].dt.strftime('%Y-%m-%d').map(holidays).fillna(trend_df['Day'])
                fig_t = px.line(trend_df, x='Date', y='Patients', markers=True, hover_data={'Day': True, 'Holiday': True})
                fig_t.update_traces(line_color='#00D4FF', line_width=3)
                for _, row in trend_df.iterrows():
                    if row['Day'] == 'Sunday':
                        fig_t.add_vrect(x0=row['Date'] - pd.Timedelta(hours=12), x1=row['Date'] + pd.Timedelta(hours=12), fillcolor="gray", opacity=0.1, layer="below", line_width=0)
                    if row['Holiday'] not in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                        fig_t.add_vrect(x0=row['Date'] - pd.Timedelta(hours=12), x1=row['Date'] + pd.Timedelta(hours=12), fillcolor="#e74c3c", opacity=0.15, layer="below", line_width=0)
                        fig_t.add_annotation(x=row['Date'], y=row['Patients'], text=row['Holiday'], showarrow=True, yshift=20, font=dict(color="#e74c3c"))
                fig_t.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_t, use_container_width=True)

        st.markdown("---")
        st.markdown("#### Spoke Heatmap (Facility vs. Date)")
        heatmap_df = plot_df.set_index(facility_col)[stats['active_date_cols']].copy()
        heatmap_df.columns = [extract_date(c).strftime('%d-%b') if pd.notna(extract_date(c)) else c for c in heatmap_df.columns]
        fig_h = px.imshow(heatmap_df, aspect='auto', color_continuous_scale='RdYlGn')
        fig_h.update_layout(height=max(600, len(heatmap_df) * 20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_colorbar=dict(title="Patients"))
        st.plotly_chart(fig_h, use_container_width=True)

        st.markdown("---")
        st.markdown("#### ⚠️ Anomaly Detector")
        if len(stats['active_date_cols']) >= 8:
            rc = stats['active_date_cols'][-8:-1]
            lc = stats['active_date_cols'][-1]
            anomalies = []
            for _, row in plot_df.iterrows():
                pa = pd.to_numeric(row[rc], errors='coerce').fillna(0).mean()
                lv = 0 if pd.isna(row[lc]) else pd.to_numeric(row[lc], errors='coerce')
                lv = 0 if pd.isna(lv) else lv
                if pa > 5 and lv < (pa * 0.2):
                    anomalies.append({'Facility': row[facility_col], 'Prev 7-day Avg': round(pa, 1), 'Latest Day': int(lv), 'Drop %': f"-{round((1 - lv/pa) * 100)}%"})
            if anomalies:
                st.error(f"⚠️ {len(anomalies)} anomalies detected!")
                st.dataframe(pd.DataFrame(anomalies), use_container_width=True, hide_index=True)
            else:
                st.success("✅ No anomalies detected.")

# ---------------------------------------------------------------------------
# STATE VIEW
# ---------------------------------------------------------------------------
else:
    # --- STATE VIEW TABS ---
    tab1, tab2 = st.tabs(["🏆 State Leaderboard", "⚖️ Compare Districts"])

    # ===== TAB 1: STATE LEADERBOARD =====
    with tab1:
        st.markdown("### 🏆 All Districts Ranked")
        with st.expander("ℹ️ How is this ranked?", expanded=False):
            st.markdown("""
            - **Reliability (Uptime %)** — % of facility-days with at least 1 patient.
            - **Efficiency (Weighted Avg)** — Avg patients per facility per day.
            - **Volume (Total Patients)** — Raw total across all facilities.
            - **Grade** — A/B/C/D/F combined score.
            """)

        rank_by = st.radio("Rank by:",
            ("Reliability (Uptime %)", "Efficiency (Weighted Avg)", "Volume (Total Patients)"),
            horizontal=True, key="lb_rank")

        if st.button("🔄 Calculate Leaderboard", key="lb"):
            with st.spinner("Processing all districts..."):
                lb_df = calculate_all_districts(tuple(available_sheets), file_bytes, time_filter)

            if lb_df.empty:
                st.warning("No districts with data found.")
            else:
                if "Reliability" in rank_by: sort_col = 'Uptime %'
                elif "Efficiency" in rank_by: sort_col = 'Weighted Avg'
                else: sort_col = 'Total Patients'

                lb_df = lb_df.sort_values(sort_col, ascending=False).reset_index(drop=True)
                n_total = len(lb_df)
                lb_df.insert(0, 'Rank', range(1, n_total + 1))

                is_filtered = selected_zm_filter != "🏢 All Zones"
                if is_filtered:
                    lb_df_display = lb_df[lb_df['ZM_Full'] == selected_zm_filter].reset_index(drop=True)
                    if lb_df_display.empty:
                        st.warning(f"No districts found for {selected_zm_filter}.")
                        st.stop()
                    n = len(lb_df_display)
                else:
                    lb_df_display = lb_df.copy()
                    n = n_total

                def add_medal(row):
                    r = row['Rank']
                    m = '🥇' if r == 1 else '🥈' if r == 2 else '🥉' if r == 3 else ''
                    return f"{m} {row['District']}".strip()
                lb_df_display['District'] = lb_df_display.apply(add_medal, axis=1)

                if not is_filtered:
                    if n >= 10: top_n, bottom_n = 5, 5
                    elif n >= 6: top_n, bottom_n = 3, 3
                    elif n >= 4: top_n, bottom_n = 2, 2
                    else: top_n, bottom_n = 1, 1
                    lb_df_display['Highlight'] = ''
                    lb_df_display.loc[lb_df_display['Rank'] <= top_n, 'Highlight'] = f'🟢 Top {top_n}'
                    lb_df_display.loc[lb_df_display['Rank'] > n - bottom_n, 'Highlight'] = f'🔴 Bottom {bottom_n}'
                else:
                    lb_df_display['Highlight'] = ''

                lb_df_display = lb_df_display[['Rank', 'District', 'ZM', 'Grade', 'Highlight', 'Uptime %', 'Weighted Avg', 'Total Patients', 'Facilities']]

                def style_row(row):
                    if is_filtered: return [''] * len(row)
                    rank = row['Rank']
                    if rank <= top_n: return ['background-color: #0e2a1a; color: #e8f5e9;'] * len(row)
                    elif rank > n - bottom_n: return ['background-color: #2a0e0e; color: #fce4e4;'] * len(row)
                    return [''] * len(row)

                def style_grade(val):
                    colors = {'A': ('#2ecc71', '#000'), 'B': ('#a3e635', '#000'), 'C': ('#fbbf24', '#000'), 'D': ('#f97316', '#FFF'), 'F': ('#e74c3c', '#FFF')}
                    bg, txt = colors.get(val, ('#333', '#FFF'))
                    return f'background-color: {bg}; color: {txt}; font-weight: bold; text-align: center;'

                def style_highlight(val):
                    if 'Top' in str(val): return 'color: #2ecc71; font-weight: bold;'
                    elif 'Bottom' in str(val): return 'color: #e74c3c; font-weight: bold;'
                    return ''

                styled = lb_df_display.style.apply(style_row, axis=1)
                try:
                    styled = styled.map(style_grade, subset=['Grade'])
                    styled = styled.map(style_highlight, subset=['Highlight'])
                except AttributeError:
                    styled = styled.applymap(style_grade, subset=['Grade'])
                    styled = styled.applymap(style_highlight, subset=['Highlight'])

                styled = styled.format({'Uptime %': '{:.1f}%', 'Weighted Avg': '{:.1f}', 'Total Patients': '{:,}'})

                if is_filtered:
                    st.caption(f"Showing **{n}** districts managed by **{ZM_SHORT.get(selected_zm_filter, selected_zm_filter)}** — ranks preserve their position in the statewide leaderboard.")

                st.dataframe(styled, use_container_width=True, hide_index=True)

                st.markdown("---")
                if is_filtered:
                    st.markdown(f"#### 📊 {ZM_SHORT.get(selected_zm_filter, selected_zm_filter)} — Districts Ranked")
                else:
                    st.markdown("#### 📊 Top 15 Districts — Statewide")

                top15_chart = lb_df_display.head(min(15, n)).copy()
                top15_chart = top15_chart.sort_values('Rank', ascending=False)

                if is_filtered:
                    top15_chart['Color'] = 'Neutral'
                    color_map = {'Neutral': '#3498db'}
                else:
                    top15_chart['Color'] = top15_chart['Rank'].apply(lambda r: f'Top {top_n}' if r <= top_n else 'Others')
                    color_map = {f'Top {top_n}': '#2ecc71', 'Others': '#95a5a6'}

                fig_lb = px.bar(top15_chart, x=sort_col, y='District', orientation='h',
                                color='Color', color_discrete_map=color_map,
                                labels={sort_col: sort_col, 'District': ''},
                                height=max(350, 40 * len(top15_chart)))
                fig_lb.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                     legend_title="", showlegend=False, margin=dict(l=0, r=20, t=20, b=20))
                st.plotly_chart(fig_lb, use_container_width=True)
        else:
            st.info("Click the button above to generate the statewide leaderboard.")

    # ===== TAB 2: COMPARE DISTRICTS =====
    with tab2:
        st.markdown("### ⚖️ Compare Two Districts Head-to-Head")
        sorted_sheets = sorted(available_sheets)
        ca, cb = st.columns(2)
        with ca: district_a = st.selectbox("🔵 District A", sorted_sheets, index=0, key='cmp_a')
        with cb: district_b = st.selectbox("🔴 District B", sorted_sheets, index=min(1, len(sorted_sheets) - 1), key='cmp_b')

        if district_a and district_b:
            df_a = read_sheet_robust(xls, district_a)
            df_b = read_sheet_robust(xls, district_b)
            pa, ra, sa = process_district_df(df_a, time_filter)
            pb, rb, sb = process_district_df(df_b, time_filter)

            if pa is None:
                st.error(f"❌ Could not process **{district_a}**.")
            elif pb is None:
                st.error(f"❌ Could not process **{district_b}**.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"#### 🔵 {district_a}")
                    r1c1, r1c2 = st.columns(2)
                    r1c1.metric("Total Patients", f"{sa['total']:,}")
                    r1c2.metric("Avg/Day", sa['weighted_avg'])
                    r2c1, r2c2 = st.columns(2)
                    r2c1.metric("Uptime", f"{calc_uptime(sa)}%")
                    r2c2.metric("Spokes", f"{sa['num_facilities']}")
                with col2:
                    st.markdown(f"#### 🔴 {district_b}")
                    r1c1, r1c2 = st.columns(2)
                    r1c1.metric("Total Patients", f"{sb['total']:,}")
                    r1c2.metric("Avg/Day", sb['weighted_avg'])
                    r2c1, r2c2 = st.columns(2)
                    r2c1.metric("Uptime", f"{calc_uptime(sb)}%")
                    r2c2.metric("Spokes", f"{sb['num_facilities']}")
                st.markdown("---")
                st.markdown("#### 📈 Daily Trend — Overlaid")
                def get_trend(p, cols, name):
                    d = []
                    for c in cols:
                        dv = extract_date(c)
                        t = pd.to_numeric(p[c], errors='coerce').fillna(0).sum()
                        if pd.notna(dv): d.append({'Date': dv, 'Patients': t, 'District': name})
                    return pd.DataFrame(d)
                combined = pd.concat([get_trend(pa, sa['active_date_cols'], district_a), get_trend(pb, sb['active_date_cols'], district_b)])
                fig_c = px.line(combined, x='Date', y='Patients', color='District', markers=True, color_discrete_map={district_a: '#3498db', district_b: '#e74c3c'})
                fig_c.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=450)
                st.plotly_chart(fig_c, use_container_width=True)
                st.markdown("---")
                st.markdown("#### 🏥 Top 10 Facilities — Side-by-Side")
                cA, cB = st.columns(2)
                with cA:
                    st.markdown(f"**🔵 {district_a}**")
                    top_a = pa.nlargest(min(10, len(pa)), 'Average Patients')[[sa['facility_col'], 'Average Patients']]
                    top_a.columns = ['Facility', 'Avg/Day']
                    st.dataframe(top_a, hide_index=True, use_container_width=True)
                with cB:
                    st.markdown(f"**🔴 {district_b}**")
                    top_b = pb.nlargest(min(10, len(pb)), 'Average Patients')[[sb['facility_col'], 'Average Patients']]
                    top_b.columns = ['Facility', 'Avg/Day']
                    st.dataframe(top_b, hide_index=True, use_container_width=True)