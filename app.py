import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta
import re
import io

# --- PAGE SETUP ---
st.set_page_config(page_title="Bihar Health Dashboard", page_icon="🏥", layout="wide")

# --- CUSTOM CSS (Clinical Light Theme) ---
st.markdown("""
<style>
    /* Global Typography */
    h1, h2, h3 { color: #1E293B !important; font-weight: 600; }
    p { color: #475569; }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetric"] label { color: #64748B !important; font-size: 14px; font-weight: 500; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #0F172A !important; font-weight: 700; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
    
    /* Custom ZM Card */
    .zm-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #0057B8;
        border-radius: 8px;
        padding: 16px;
        margin-top: 10px;
        margin-bottom: 16px;
    }
    .zm-card-header { color: #64748B; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;}
    .zm-card-name { color: #0F172A; font-size: 16px; font-weight: 700; margin-bottom: 2px;}
    .zm-card-zone { color: #0057B8; font-size: 13px; font-weight: 500;}

    /* Report Header */
    .report-header {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-top: 4px solid #0057B8;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .report-title { color: #0F172A; font-size: 24px; font-weight: 700; margin-bottom: 8px; }
    .report-meta { color: #64748B; font-size: 14px; line-height: 1.6; }
    .report-meta strong { color: #1E293B; }

    /* Grade Badges */
    .grade-badge { display: inline-block; padding: 8px 20px; border-radius: 8px; font-size: 24px; font-weight: 800; }
    .grade-A { background-color: #D1FAE5; color: #065F46; }
    .grade-B { background-color: #ECFCCB; color: #3F6212; }
    .grade-C { background-color: #FEF3C7; color: #92400E; }
    .grade-D { background-color: #FFEDD5; color: #9A3412; }
    .grade-F { background-color: #FEE2E2; color: #991B1B; }

    /* Info Bar (Top 3 Cards) */
    .info-bar { display: flex; gap: 16px; margin-bottom: 24px; }
    .info-card { 
        flex: 1; background-color: #FFFFFF; border: 1px solid #E2E8F0; 
        border-top: 3px solid #0057B8; border-radius: 10px; padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .info-label { color: #64748B; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
    .info-value { color: #0F172A; font-size: 20px; font-weight: 700; line-height: 1.2; }
    .info-sub { color: #0057B8; font-size: 13px; font-weight: 600; margin-top: 4px; }

    /* Compare Battle Cards */
    .battle-card { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 16px; }
    .battle-card-blue { border-top: 4px solid #3B82F6; }
    .battle-card-red { border-top: 4px solid #EF4444; }
    .battle-title { font-size: 20px; font-weight: 700; margin-bottom: 16px; }
    .battle-row { display: flex; justify-content: space-between; border-bottom: 1px solid #F1F5F9; padding: 8px 0; font-size: 15px; color: #475569; }
    .battle-row:last-child { border-bottom: none; }
    .battle-val { font-weight: 700; color: #0F172A; }
</style>
""", unsafe_allow_html=True)

# --- HARDCODED ZM DATA ---
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

DISTRICT_TO_ZM = {}
for zm_name, districts in ZM_DATA.items():
    for d in districts.keys():
        DISTRICT_TO_ZM[d] = zm_name

DISTRICT_MAP = {"Seikhpura": "Sheikhpura", "Rohtas": "Sasaram"}

# --- HELPER FUNCTIONS ---
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
        if 'name of the hospital' in str(c).lower():
            return c
    for c in df.columns:
        if 'hospital' in str(c).lower() and 'name' in str(c).lower():
            return c
    for c in df.columns:
        if 'hospital' in str(c).lower():
            return c
    return None

def extract_date(col_name):
    if isinstance(col_name, pd.Timestamp):
        return col_name
    s = str(col_name)
    match = re.search(r'(\d{4}-\d{2}-\d{2})', s)
    if match:
        return pd.to_datetime(match.group(1), errors='coerce')
    match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', s)
    if match:
        return pd.to_datetime(match.group(1), dayfirst=True, errors='coerce')
    match = re.search(r'(\d{1,2}-\w{3}-\d{2,4})', s)
    if match:
        return pd.to_datetime(match.group(1), errors='coerce')
    return pd.NaT

def find_date_columns(df):
    date_cols = [c for c in df.columns if 'Total number of patients' in str(c)]
    if date_cols:
        return date_cols
    date_cols = []
    for c in df.columns:
        parsed = extract_date(c)
        if pd.notna(parsed):
            date_cols.append(c)
    return date_cols

def get_facility_mask(df, facility_col):
    mask = df[facility_col].notna()
    mask &= ~df[facility_col].astype(str).str.upper().str.contains('TOTAL', na=False)
    mask &= ~df[facility_col].astype(str).str.strip().str.lower().isin(['nan', 'none', ''])
    return mask

def process_district_df(df, time_filter):
    if df is None:
        return None, None, None
    facility_col = find_facility_column(df)
    if not facility_col:
        return None, None, None

    df = df[get_facility_mask(df, facility_col)].copy()
    all_facilities = df[facility_col].dropna().tolist()

    date_cols = find_date_columns(df)
    if not date_cols:
        return None, None, None

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

    if not active_date_cols:
        active_date_cols = sorted_cols

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

@st.cache_data(show_spinner=False)
def calculate_all_districts(sheet_names_tuple, uploaded_file_bytes, time_filter):
    xls = pd.ExcelFile(io.BytesIO(uploaded_file_bytes))
    data = []
    for sheet in sheet_names_tuple:
        try:
            sdf = read_sheet_robust(xls, sheet)
            _, _, s = process_district_df(sdf, time_filter)
            if s:
                data.append({
                    'District': sheet, 'Total Patients': s['total'],
                    'Weighted Avg': s['weighted_avg'], 'Uptime %': calc_uptime(s),
                    'Facilities': s['num_facilities']
                })
        except Exception:
            pass
    return pd.DataFrame(data)

# --- SIDEBAR ---
with st.sidebar:
    st.title("Control Panel")
    uploaded_data_file = st.file_uploader("Upload Main Data File", type=["xlsx", "csv"])
    if uploaded_data_file is not None:
        try:
            file_bytes = uploaded_data_file.getvalue()
            xls = pd.ExcelFile(uploaded_data_file)
            available_sheets = xls.sheet_names
            st.divider()

            all_districts = sorted(DISTRICT_TO_ZM.keys())
            selected_district_zm = st.selectbox("Select District", all_districts)

            zm_name_for_district = DISTRICT_TO_ZM.get(selected_district_zm, "Unknown")
            zone_name = "Unknown Zone"
            display_zm = zm_name_for_district
            if "(" in zm_name_for_district and ")" in zm_name_for_district:
                display_zm = zm_name_for_district.split("(")[0].strip()
                zone_name = zm_name_for_district.split("(")[1].replace(")", "").strip() + " Zone"

            st.markdown(f'''
            <div class="zm-card">
                <div class="zm-card-header">👤 Zone Manager</div>
                <div class="zm-card-name">{display_zm}</div>
                <div class="zm-card-zone">{zone_name}</div>
            </div>
            ''', unsafe_allow_html=True)

            hub_list = sorted(ZM_DATA[zm_name_for_district][selected_district_zm])
            selected_hub_zm = st.selectbox("Select Hub", hub_list)

            st.divider()
            time_filter = st.selectbox("Select Time Range:", ["All Available Data", "Last 7 Days", "Last 15 Days", "Last 30 Days"])
            st.divider()

            target_district = DISTRICT_MAP.get(selected_district_zm, selected_district_zm)
            sheet_found = False
            for s in available_sheets:
                if s == target_district or target_district.lower() in s.lower() or s.lower() in target_district.lower():
                    sheet_to_load = s
                    sheet_found = True
                    break
            if sheet_found: st.success(f"✅ Data Available: {selected_district_zm}")
            else: st.warning(f"⏳ Data Pending: {selected_district_zm}")
        except Exception as e:
            st.error(f"Error: {e}")

# --- MAIN AREA ---
st.title("🏥 Bihar District Hub & Spoke Dashboard")
if uploaded_data_file is None:
    st.info("👈 Please upload the Main Data File from the sidebar to begin.")
    st.stop()
if not sheet_found:
    st.warning(f"⏳ **Data Not Yet Available for {selected_district_zm}**")
    st.stop()

df_raw = read_sheet_robust(xls, sheet_to_load)
plot_df, raw_text_df, stats = process_district_df(df_raw, time_filter)
if plot_df is None:
    st.error(f"Could not process the sheet '{sheet_to_load}'.")
    st.stop()
facility_col = stats['facility_col']

# --- SPOKE INFO BAR ---
best_name, best_grade, best_avg = "N/A", "—", 0
if not plot_df.empty:
    scorecard_tmp = plot_df.copy()
    scorecard_tmp['Grade'] = scorecard_tmp.apply(lambda r: calculate_grade(r['Uptime %'], r['Average Patients']), axis=1)
    grade_order = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'F': 5}
    scorecard_tmp['Grade_Order'] = scorecard_tmp['Grade'].map(grade_order)
    scorecard_tmp = scorecard_tmp.sort_values(by=['Grade_Order', 'Average Patients'], ascending=[True, False])
    if not scorecard_tmp.empty:
        best_name = scorecard_tmp.iloc[0][facility_col]
        best_grade = scorecard_tmp.iloc[0]['Grade']
        best_avg = scorecard_tmp.iloc[0]['Average Patients']

st.markdown(f'''
<div class="info-bar">
    <div class="info-card">
        <div class="info-label">📍 Total Spokes</div>
        <div class="info-value">{stats['num_facilities']}</div>
        <div class="info-sub">Reporting facilities</div>
    </div>
    <div class="info-card">
        <div class="info-label">🏥 Hub Lab</div>
        <div class="info-value">{selected_hub_zm}</div>
        <div class="info-sub">{selected_district_zm} District</div>
    </div>
    <div class="info-card">
        <div class="info-label">⭐ Best Performing Spoke</div>
        <div class="info-value">{best_name}</div>
        <div class="info-sub">Grade {best_grade} · {best_avg} /day</div>
    </div>
</div>
''', unsafe_allow_html=True)

# --- TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 District Dashboard",
    "📋 Report Card",
    "🏆 State Leaderboard",
    "📈 Trends & Analytics",
    "⚖️ Compare Districts"
])

# ===== TAB 1: DISTRICT DASHBOARD =====
with tab1:
    col1, col2, col3 = st.columns(3)
    with col1: st.metric(label=f"Total Patients ({time_filter})", value=f"{stats['total']:,}")
    with col2: st.metric(label="Weighted Avg Daily Patients", value=f"{stats['weighted_avg']}")
    with col3: st.metric(label="Facility Uptime %", value=f"{calc_uptime(stats)}%")

    st.divider()

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: metric_option = st.radio("Metric:", ("Average Patients", "Total Patients", "Uptime %"), horizontal=True, key="d1")
    with c2: sort_option = st.selectbox("Sort:", ["Highest to Lowest", "Lowest to Highest"], key="d2")
    with c3: active_only = st.checkbox("Exclude Inactive", value=False, key="d3")
    
    metric_col = {'Average Patients': 'Average Patients', 'Total Patients': 'Total Patients', 'Uptime %': 'Uptime %'}[metric_option]
    filtered = plot_df.copy()
    if active_only: filtered = filtered[filtered['Total Patients'] > 0]
        
    if filtered.empty:
        st.warning("No data matches the filters.")
    else:
        sorted_df = filtered.sort_values(by=metric_col, ascending=(sort_option == "Lowest to Highest"))
        sorted_df['Highlight'] = 'Others'
        if len(sorted_df) > 10:
            sorted_df.loc[sorted_df.nlargest(5, metric_col).index, 'Highlight'] = 'Top 5'
            sorted_df.loc[sorted_df.nsmallest(5, metric_col).index, 'Highlight'] = 'Bottom 5'
            
        fig = px.bar(sorted_df, y=facility_col, x=metric_col, orientation='h', color='Highlight', color_discrete_map={'Top 5': '#10B981', 'Bottom 5': '#EF4444', 'Others': '#94A3B8'}, title=f"{metric_option} per Facility")
        
        if metric_col == 'Uptime %' or metric_col == 'Total Patients':
            current_avg = round(filtered[metric_col].mean(), 1)
        else:
            current_avg = round(filtered['Total Patients'].sum() / (len(filtered) * stats['num_days']), 1) if len(filtered) > 0 and stats['num_days'] > 0 else 0
            
        fig.add_vline(x=current_avg, line_dash="dash", line_color="#0057B8", annotation_text=f"Avg: {current_avg}", annotation_font_color="#0057B8")

        fig.update_layout(
            height=max(500, len(sorted_df) * 25), 
            yaxis=dict(autorange="reversed"), 
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)', 
            legend_title="", xaxis_title=metric_option, yaxis_title="",
            title_font_color="#1E293B", font_color="#475569"
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#F1F5F9')
        fig.update_yaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)
        
    st.divider()
    st.caption(f"💡 Data: **{sheet_to_load}** | Range: **{time_filter}** | Refreshed: {pd.Timestamp.now().strftime('%d-%b-%Y %H:%M')}")

# ===== TAB 2: REPORT CARD =====
with tab2:
    period_str = "N/A"
    if stats['active_date_cols']:
        fd = extract_date(stats['active_date_cols'][0])
        ld = extract_date(stats['active_date_cols'][-1])
        if pd.notna(fd) and pd.notna(ld):
            period_str = f"{fd.strftime('%d %b %Y')} – {ld.strftime('%d %b %Y')}"

    d_grade = district_grade(plot_df)
    
    st.markdown(f'''
    <div class="report-header">
        <div class="report-title">📋 District Report Card — {selected_district_zm}</div>
        <div class="report-meta">
            <strong>ZM:</strong> {zm_name_for_district} &nbsp;|&nbsp; 
            <strong>Hub:</strong> {selected_hub_zm} &nbsp;|&nbsp; 
            <strong>Period:</strong> {period_str} ({stats['num_days']} days) &nbsp;|&nbsp; 
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
        <div style="background-color:#FFFFFF; border:1px solid #E2E8F0; padding:15px; border-radius:12px; text-align:center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
            <div style="color:#64748B; font-size:13px; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">District Grade</div>
            <span class="grade-badge grade-{d_grade}">{d_grade}</span>
        </div>
        ''', unsafe_allow_html=True)

    st.divider()

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

    st.divider()

    export = scorecard[[facility_col, 'Grade', 'Uptime %', 'Average Patients', 'Total Patients', 'Zero Days']].copy()
    export.columns = ['Facility', 'Grade', 'Uptime %', 'Avg Per Day', 'Total Patients', 'Zero Days']
    csv = export.to_csv(index=False).encode('utf-8')
    period_file = pd.Timestamp.now().strftime('%b_%Y')

    st.download_button(
        label=f"📥 Download Report Card ({selected_district_zm})",
        data=csv, file_name=f'{selected_district_zm}_ReportCard_{time_filter.replace(" ", "_")}_{period_file}.csv', mime='text/csv'
    )

# ===== TAB 3: STATE LEADERBOARD =====
with tab3:
    st.markdown("### 🏆 Bihar State Leaderboard")
    
    with st.spinner("Loading State Data..."):
        state_df = calculate_all_districts(tuple(available_sheets), file_bytes, time_filter)
        
    if not state_df.empty:
        # Statewide Metrics
        total_state_patients = state_df['Total Patients'].sum()
        avg_state_uptime = round(state_df['Uptime %'].mean(), 1)
        
        sc1, sc2, sc3 = st.columns(3)
        with sc1: st.metric("Total Bihar Patients", f"{total_state_patients:,}")
        with sc2: st.metric("Active Districts", f"{len(state_df)}")
        with sc3: st.metric("Statewide Avg Uptime", f"{avg_state_uptime}%")
        
        st.divider()
        
        state_df = state_df.sort_values('Total Patients', ascending=False).reset_index(drop=True)
        state_df.index = state_df.index + 1
        state_df.index.name = 'Rank'
        
        def medal(r): return "🥇" if r == 1 else "🥈" if r == 2 else "🥉" if r == 3 else ""
        state_df['District'] = state_df.apply(lambda row: f"{medal(row.name)} {row['District']}".strip(), axis=1)
        
        st.dataframe(
            state_df, 
            use_container_width=True, 
            column_config={
                "Uptime %": st.column_config.ProgressColumn("Uptime %", format="%.1f%%", min_value=0, max_value=100)
            }
        )
        
        st.divider()
        st.markdown("#### 📊 Top 15 Districts")
        top15 = state_df.head(15)
        fig_lb = px.bar(top15, x='Total Patients', y='District', orientation='h', color='Uptime %', color_continuous_scale='Blues')
        fig_lb.update_layout(
            yaxis=dict(autorange="reversed"), height=500, 
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            title_font_color="#1E293B", font_color="#475569"
        )
        fig_lb.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#F1F5F9')
        st.plotly_chart(fig_lb, use_container_width=True)
    else:
        st.warning("No district data available for the selected time range.")

# ===== TAB 4: TRENDS =====
with tab4:
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
            fig_t = px.line(trend_df, x='Date', y='Patients', markers=True)
            fig_t.update_traces(line_color='#0057B8', line_width=3)
            fig_t.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', title_font_color="#1E293B", font_color="#475569")
            fig_t.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#F1F5F9')
            fig_t.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#F1F5F9')
            st.plotly_chart(fig_t, use_container_width=True)
    st.divider()
    st.markdown("#### Spoke Heatmap (Facility vs. Date)")
    heatmap_df = plot_df.set_index(facility_col)[stats['active_date_cols']].copy()
    heatmap_df.columns = [extract_date(c).strftime('%d-%b') if pd.notna(extract_date(c)) else c for c in heatmap_df.columns]
    fig_h = px.imshow(heatmap_df, aspect='auto', color_continuous_scale='RdYlGn')
    fig_h.update_layout(height=max(600, len(heatmap_df) * 20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_h, use_container_width=True)

# ===== TAB 5: COMPARE DISTRICTS (UI FIXED) =====
with tab5:
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
        
        if pa is None or pb is None:
            st.error("Could not process one of the selected districts.")
        else:
            col1, col2 = st.columns(2)
            
            # District A Card
            with col1:
                st.markdown(f'''
                <div class="battle-card battle-card-blue">
                    <div class="battle-title" style="color: #3B82F6;">🔵 {district_a}</div>
                    <div class="battle-row"><span>Total Patients</span> <span class="battle-val">{sa['total']:,}</span></div>
                    <div class="battle-row"><span>Weighted Avg / Day</span> <span class="battle-val">{sa['weighted_avg']}</span></div>
                    <div class="battle-row"><span>Facility Uptime</span> <span class="battle-val">{calc_uptime(sa)}%</span></div>
                    <div class="battle-row"><span>Total Spokes</span> <span class="battle-val">{sa['num_facilities']}</span></div>
                </div>
                ''', unsafe_allow_html=True)
                
            # District B Card
            with col2:
                st.markdown(f'''
                <div class="battle-card battle-card-red">
                    <div class="battle-title" style="color: #EF4444;">🔴 {district_b}</div>
                    <div class="battle-row"><span>Total Patients</span> <span class="battle-val">{sb['total']:,}</span></div>
                    <div class="battle-row"><span>Weighted Avg / Day</span> <span class="battle-val">{sb['weighted_avg']}</span></div>
                    <div class="battle-row"><span>Facility Uptime</span> <span class="battle-val">{calc_uptime(sb)}%</span></div>
                    <div class="battle-row"><span>Total Spokes</span> <span class="battle-val">{sb['num_facilities']}</span></div>
                </div>
                ''', unsafe_allow_html=True)

            st.divider()
            st.markdown("#### 📈 Daily Trend — Overlaid")
            
            def get_trend(p, cols, name):
                d = []
                for c in cols:
                    dv = extract_date(c)
                    t = pd.to_numeric(p[c], errors='coerce').fillna(0).sum()
                    if pd.notna(dv): d.append({'Date': dv, 'Patients': t, 'District': name})
                return pd.DataFrame(d)
                
            combined = pd.concat([get_trend(pa, sa['active_date_cols'], district_a), get_trend(pb, sb['active_date_cols'], district_b)])
            
            fig_c = px.line(combined, x='Date', y='Patients', color='District', markers=True, color_discrete_map={district_a: '#3B82F6', district_b: '#EF4444'})
            fig_c.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=450,
                title_font_color="#1E293B", font_color="#475569"
            )
            fig_c.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#F1F5F9')
            fig_c.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#F1F5F9')
            st.plotly_chart(fig_c, use_container_width=True)