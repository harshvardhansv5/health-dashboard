import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta
import re

# --- PAGE SETUP ---
st.set_page_config(page_title="Bihar Health Dashboard", page_icon="🏥", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    div[data-testid="stMetric"] {background-color: #1E1E1E; border: 1px solid #333333; padding: 15px; border-radius: 10px;}
    div[data-testid="stMetric"] label {color: #AAAAAA !important;}
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {color: #FFFFFF !important;}
    .news-ticker-container {background-color: #1a1a1a; border: 1px solid #333; border-left: 5px solid #00D4FF; border-radius: 8px; padding: 12px 0; margin-bottom: 15px; overflow: hidden; position: relative;}
    .news-ticker-label {position: absolute; left: 0; top: 0; bottom: 0; background-color: #00D4FF; color: #000; font-weight: bold; padding: 12px 15px; z-index: 10; font-size: 14px;}
    .news-ticker-scroll {display: inline-block; white-space: nowrap; padding-left: 100%; animation: scroll 60s linear infinite; font-size: 14px;}
    .news-ticker-scroll:hover {animation-play-state: paused;}
    @keyframes scroll {0% {transform: translateX(0);} 100% {transform: translateX(-100%);}}
    .news-item-up {color: #2ecc71; font-weight: 600; padding: 0 30px;}
    .news-item-down {color: #e74c3c; font-weight: 600; padding: 0 30px;}
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

DISTRICT_MAP = {"Seikhpura": "Sheikhpura", "Rohtas": "Sasaram"}
HUB_TO_SHEET_MAP = {"SDH Barh Patna": "Barh", "SDH Danapur Patna": "Danapur"}

# --- BIHAR DISTRICT CENTROIDS (Lat, Lon) for Map Rendering ---
BIHAR_COORDS = {
    "Araria": (26.1350, 87.5132), "Arwal": (25.2446, 84.6665), "Aurangabad": (24.7520, 84.3730),
    "Banka": (24.8830, 86.9216), "Begusarai": (25.4182, 86.1270), "Bhagalpur": (25.2447, 86.9893),
    "Bhojpur": (25.5609, 84.6199), "Buxar": (25.5647, 83.9771), "Darbhanga": (26.1542, 85.8918),
    "Purbi Champaran": (26.6472, 84.9217), "Gaya": (24.7955, 85.0002), "Gopalganj": (26.4673, 84.4392),
    "Jamui": (24.9258, 86.2252), "Jehanabad": (25.2135, 84.9895), "Kaimur": (25.0405, 83.6037),
    "Katihar": (25.5541, 87.5587), "Khagaria": (25.5016, 86.4667), "Kishanganj": (26.0892, 87.9415),
    "Lakhisarai": (25.4061, 86.0906), "Madhepura": (25.9215, 86.7926), "Madhubani": (26.3548, 86.4907),
    "Munger": (25.3812, 86.4728), "Muzaffarpur": (26.1209, 85.3647), "Nalanda": (25.2016, 85.5222),
    "Nawada": (24.8845, 85.5430), "Patna": (25.5941, 85.1376), "Purnia": (25.7771, 87.4753),
    "Rohtas": (24.9572, 84.0283), "Saharsa": (25.8798, 86.6027), "Samastipur": (25.8629, 85.7811),
    "Saran": (25.7814, 84.7477), "Sheikhpura": (25.1392, 85.8500), "Sheohar": (26.5154, 85.2934),
    "Sitamarhi": (26.5934, 85.4913), "Siwan": (26.2194, 84.3559), "Supaul": (26.1244, 86.6054),
    "Vaishali": (25.6921, 85.2150), "Pashchim Champaran": (27.1041, 84.5099),
}

SHEET_TO_GEO = {
    "Sasaram": "Rohtas", "Danapur": "Patna", "Barh": "Patna", "Sheikhpura": "Sheikhpura", "Purnia": "Purnia", "Saharsa": "Saharsa",
    "Madhepura": "Madhepura", "Supaul": "Supaul", "Araria": "Araria", "Katihar": "Katihar", "Kishanganj": "Kishanganj", "Banka": "Banka",
    "Bhagalpur": "Bhagalpur", "Jamui": "Jamui", "Munger": "Munger", "Begusarai": "Begusarai", "Khagaria": "Khagaria", "Lakhisarai": "Lakhisarai",
    "Muzaffarpur": "Muzaffarpur", "Sheohar": "Sheohar", "Vaishali": "Vaishali", "Bhojpur": "Bhojpur", "Nalanda": "Nalanda", "Patna": "Patna",
    "East Champaran": "Purbi Champaran", "West Champaran": "Pashchim Champaran", "Sitamarhi": "Sitamarhi", "Darbhanga": "Darbhanga",
    "Madhubani": "Madhubani", "Samastipur": "Samastipur", "Aurangabad": "Aurangabad", "Gaya": "Gaya", "Nawada": "Nawada", "Arwal": "Arwal",
    "Jehanabad": "Jehanabad", "Buxar": "Buxar", "Kaimur": "Kaimur", "Gopalganj": "Gopalganj", "Saran": "Saran", "Siwan": "Siwan"
}

# --- HELPER FUNCTIONS ---
def extract_date(col_name):
    match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', str(col_name))
    if match:
        return pd.to_datetime(match.group(1), dayfirst=True, errors='coerce')
    return pd.NaT

def process_district_df(df, time_filter):
    df.columns = [str(c).strip() for c in df.columns]
    facility_col = [c for c in df.columns if 'Name of the Hospital' in c]
    if not facility_col:
        return None, None, None
    facility_col = facility_col[0]
    all_facilities = df[facility_col].dropna().tolist()
    all_facilities = [f for f in all_facilities if 'TOTAL' not in str(f).upper()]
    date_cols = [c for c in df.columns if 'Total number of patients' in c]
    if not date_cols:
        return None, None, None
    parsed_dates = [extract_date(c) for c in date_cols]
    valid_dates = [d for d in parsed_dates if pd.notna(d)]
    latest_date = max(valid_dates) if valid_dates else None
    if time_filter == "Last 30 Days" and latest_date:
        start_date = latest_date - timedelta(days=30)
        active_date_cols = [c for c, d in zip(date_cols, parsed_dates) if pd.notna(d) and d > start_date]
    elif time_filter == "Last 7 Days" and latest_date:
        start_date = latest_date - timedelta(days=7)
        active_date_cols = [c for c, d in zip(date_cols, parsed_dates) if pd.notna(d) and d > start_date]
    elif time_filter == "Single Day (Latest)" and latest_date:
        active_date_cols = [c for c, d in zip(date_cols, parsed_dates) if pd.notna(d) and d == latest_date]
    else:
        active_date_cols = date_cols
    if not active_date_cols:
        active_date_cols = date_cols
    plot_df = df[df[facility_col].isin(all_facilities)][[facility_col] + active_date_cols].copy()
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

def categorize_reason(note):
    if pd.isna(note): return "No Data Entered"
    note = str(note).lower()
    if 'strike' in note: return "Doctor/Staff Strike"
    if 'lt' in note and any(k in note for k in ['leave', 'not available', 'nhi', 'no lt', 'absent', 'chutti']): return "No Lab Technician"
    if 'opd' in note or 'closed' in note or 'holiday' in note: return "OPD Closed/Holiday"
    if 'doctor' in note and 'prescribe' in note: return "Doctor Did Not Prescribe"
    if 'footfall' in note or 'patient not' in note: return "Low Footfall"
    if 'operational' in note or 'merged' in note: return "Not Operational"
    if 'runner' in note: return "Runner Issue"
    if 'machine' in note or 'equipment' in note: return "Machine Issue"
    if 'flood' in note or 'rain' in note or 'river' in note: return "Weather/Flood"
    if 'recorded' in note or 'no data' in note or 'sample n/a' in note: return "No Data Entered"
    return "Other Issue"

def generate_news_items(plot_df, facility_col, active_date_cols, threshold=20):
    news = []
    if len(active_date_cols) < 14: return news
    recent_cols = active_date_cols[-7:]
    previous_cols = active_date_cols[-14:-7]
    for _, row in plot_df.iterrows():
        ra = pd.to_numeric(row[recent_cols], errors='coerce').fillna(0).mean()
        pa = pd.to_numeric(row[previous_cols], errors='coerce').fillna(0).mean()
        if pa >= 3:
            ch = ((ra - pa) / pa) * 100
            if abs(ch) >= threshold:
                news.append({'facility': row[facility_col], 'change': round(ch, 1), 'recent': round(ra, 1), 'previous': round(pa, 1)})
    news.sort(key=lambda x: abs(x['change']), reverse=True)
    return news

@st.cache_data(show_spinner=False)
def calculate_all_districts(sheet_names_tuple, uploaded_file_bytes, time_filter):
    import io
    xls = pd.ExcelFile(io.BytesIO(uploaded_file_bytes))
    data = []
    for sheet in sheet_names_tuple:
        try:
            sdf = pd.read_excel(xls, sheet_name=sheet)
            _, _, s = process_district_df(sdf, time_filter)
            if s:
                data.append({'District': sheet, 'Total Patients': s['total'], 'Weighted Avg': s['weighted_avg'], 'Uptime %': calc_uptime(s), 'Facilities': s['num_facilities']})
        except Exception: pass
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
            selected_zm = st.selectbox("Select ZM Name", list(ZM_DATA.keys()))
            selected_district_zm = st.selectbox("Select District", list(ZM_DATA[selected_zm].keys()))
            selected_hub_zm = st.selectbox("Select Hub", ZM_DATA[selected_zm][selected_district_zm])
            st.divider()
            time_filter = st.selectbox("Select Time Range:", ["All Available Data", "Last 30 Days", "Last 7 Days", "Single Day (Latest)"])
            st.divider()
            target_district = DISTRICT_MAP.get(selected_district_zm, selected_district_zm)
            if selected_hub_zm in HUB_TO_SHEET_MAP:
                target_district = HUB_TO_SHEET_MAP[selected_hub_zm]
            sheet_found = False
            for s in available_sheets:
                if s == target_district or target_district.lower() in s.lower() or s.lower() in target_district.lower():
                    sheet_to_load = s; sheet_found = True; break
            if sheet_found: st.success(f"✅ Data Available: {selected_district_zm}")
            else: st.warning(f"⏳ Data Pending: {selected_district_zm}")
        except Exception as e:
            st.error(f"Error: {e}")

# --- MAIN AREA ---
st.title("🏥 Bihar District Hub & Spoke Dashboard")
if uploaded_data_file is None:
    st.info("👈 Please upload the Main Data File from the sidebar to begin."); st.stop()
if not sheet_found:
    st.warning(f"⏳ **Data Not Yet Available for {selected_district_zm}**"); st.stop()

df = pd.read_excel(xls, sheet_name=sheet_to_load)
plot_df, raw_text_df, stats = process_district_df(df, time_filter)
if plot_df is None:
    st.error("This sheet does not have the expected columns."); st.stop()
facility_col = stats['facility_col']

news_items = generate_news_items(plot_df, facility_col, stats['active_date_cols'], threshold=20)
if news_items:
    ticker_html = '<div class="news-ticker-container"><div class="news-ticker-label">🔴 LIVE</div><div class="news-ticker-scroll">'
    for item in news_items:
        if item['change'] > 0: ticker_html += f'<span class="news-item-up">📈 {item["facility"]} | +{item["change"]}% | ({item["previous"]} → {item["recent"]}) &nbsp;&nbsp;◆&nbsp;&nbsp;</span>'
        else: ticker_html += f'<span class="news-item-down">📉 {item["facility"]} | {item["change"]}% | ({item["previous"]} → {item["recent"]}) &nbsp;&nbsp;◆&nbsp;&nbsp;</span>'
    ticker_html += '</div></div>'
    st.markdown(ticker_html, unsafe_allow_html=True)

# --- TABS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 District Dashboard", "🏆 State Leaderboard", "📈 Trends & Analytics", "🚨 Diagnostics", "🗺️ Bihar Map", "⚖️ Compare Districts"])

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
        fig = px.bar(sorted_df, y=facility_col, x=metric_col, orientation='h', color='Highlight', color_discrete_map={'Top 5': '#2ecc71', 'Bottom 5': '#e74c3c', 'Others': '#95a5a6'}, title=f"{metric_option} per Facility")
        fig.update_layout(height=max(500, len(sorted_df) * 25), yaxis=dict(autorange="reversed"), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', legend_title="", xaxis_title=metric_option, yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    st.divider()
    st.caption(f"💡 Data: **{sheet_to_load}** | Range: **{time_filter}** | Refreshed: {pd.Timestamp.now().strftime('%d-%b-%Y %H:%M')}")

# ===== TAB 2: LEADERBOARD =====
with tab2:
    st.markdown("### 🏆 All Districts Ranked")
    with st.expander("ℹ️ What do 'Uptime %' and 'Weighted Avg' mean? Click to expand", expanded=False):
        st.markdown("""
        **📊 Uptime %** — *The reliability score.*  
        The percentage of days each facility reported more than 0 patients. Higher is better.  
        *Example: 80% Uptime means facilities were active 4 out of every 5 days.*

        **⚖️ Weighted Avg** — *The efficiency score.*  
        Total patients divided by (facilities × days). Big hospitals count more than small ones.  
        *Example: 14.3 means the average facility saw 14.3 patients per day.*

        **👥 Total Patients** — *The volume score.*  
        Raw sum of all patients across every facility in the district.

        **🏥 Facilities** — Number of reporting hospitals (SDH, CHC, PHC, UPHC) in the district.
        """)
    if st.button("🔄 Calculate Leaderboard", key="lb"):
        with st.spinner("Processing..."):
            lb_df = calculate_all_districts(tuple(available_sheets), file_bytes, time_filter)
        if not lb_df.empty:
            lb_df = lb_df.sort_values('Total Patients', ascending=False).reset_index(drop=True)
            lb_df.index = lb_df.index + 1; lb_df.index.name = 'Rank'
            def medal(r): return "🥇" if r == 1 else "🥈" if r == 2 else "🥉" if r == 3 else ""
            lb_df['District'] = lb_df.apply(lambda row: f"{medal(row.name)} {row['District']}".strip(), axis=1)
            st.dataframe(lb_df, use_container_width=True, column_config={"Uptime %": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100)})
            top15 = lb_df.head(15)
            fig_lb = px.bar(top15, x='Total Patients', y='District', orientation='h', color='Uptime %', color_continuous_scale='RdYlGn')
            fig_lb.update_layout(yaxis=dict(autorange="reversed"), height=500, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_lb, use_container_width=True)
    else: st.info("Click the button above to generate the statewide leaderboard.")

# ===== TAB 3: TRENDS =====
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
    st.divider()
    st.markdown("#### Spoke Heatmap (Facility vs. Date)")
    st.caption("Red = 0 patients. Green = High volume. Look for horizontal (facility down) or vertical (district down) red streaks.")
    heatmap_df = plot_df.set_index(facility_col)[stats['active_date_cols']].copy()
    heatmap_df.columns = [extract_date(c).strftime('%d-%b') if pd.notna(extract_date(c)) else c for c in heatmap_df.columns]
    fig_h = px.imshow(heatmap_df, aspect='auto', color_continuous_scale='RdYlGn')
    fig_h.update_layout(height=max(600, len(heatmap_df) * 20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_colorbar=dict(title="Patients"))
    st.plotly_chart(fig_h, use_container_width=True)
    st.divider()
    st.markdown("#### ⚠️ Anomaly Detector")
    if len(stats['active_date_cols']) >= 8:
        rc = stats['active_date_cols'][-8:-1]; lc = stats['active_date_cols'][-1]
        anomalies = []
        for _, row in plot_df.iterrows():
            pa = pd.to_numeric(row[rc], errors='coerce').fillna(0).mean()
            lv = 0 if pd.isna(row[lc]) else pd.to_numeric(row[lc], errors='coerce')
            lv = 0 if pd.isna(lv) else lv
            if pa > 5 and lv < (pa * 0.2):
                anomalies.append({'Facility': row[facility_col], 'Prev 7-day Avg': round(pa, 1), 'Latest Day': int(lv), 'Drop %': f"-{round((1 - lv/pa) * 100)}%"})
        if anomalies: st.error(f"⚠️ {len(anomalies)} anomalies detected!"); st.dataframe(pd.DataFrame(anomalies), use_container_width=True, hide_index=True)
        else: st.success("✅ No anomalies detected.")

# ===== TAB 4: DIAGNOSTICS =====
with tab4:
    st.markdown(f"### 🚨 Operational Diagnostics for {selected_district_zm}")
    st.markdown("#### Why Are Facilities Reporting Zero?")
    st.caption("This chart reveals the primary blockers to patient care. Focus on the biggest slice.")
    all_reasons = []
    for col in stats['active_date_cols']:
        for val in raw_text_df[col]:
            if pd.notna(val) and not isinstance(val, (int, float)): all_reasons.append(categorize_reason(val))
            elif pd.notna(val) and isinstance(val, (int, float)) and val == 0: all_reasons.append("Reported Zero (No Note)")
    if all_reasons:
        reason_counts = pd.DataFrame(all_reasons, columns=['Reason'])['Reason'].value_counts().reset_index()
        reason_counts.columns = ['Reason', 'Count']
        cp, cb = st.columns(2)
        with cp:
            fig_p = px.pie(reason_counts, values='Count', names='Reason', hole=0.4, title='Share of Issues')
            fig_p.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_p, use_container_width=True)
        with cb:
            fig_r = px.bar(reason_counts, x='Count', y='Reason', orientation='h', color='Count', color_continuous_scale='Reds', title='Count of Days Affected')
            fig_r.update_layout(yaxis=dict(autorange="reversed"), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
            st.plotly_chart(fig_r, use_container_width=True)
    else:
        st.success("✅ No operational issues reported.")

# ===== TAB 5: BIHAR MAP (Coordinate Plot) =====
with tab5:
    st.markdown("### 🗺️ Bihar District Performance Map")
    st.caption("Each circle is a district placed by its real latitude/longitude. Larger circle = more patients. Color = performance.")
    map_metric = st.radio("Color Map By:", ("Weighted Avg", "Uptime %", "Total Patients"), horizontal=True, key="map_metric")
    if st.button("🗺️ Generate Map", key="gen_map"):
        with st.spinner("Calculating..."):
            map_df = calculate_all_districts(tuple(available_sheets), file_bytes, time_filter)
        if map_df.empty:
            st.warning("No data available to map.")
        else:
            map_df['GeoDistrict'] = map_df['District'].map(SHEET_TO_GEO)
            merged = map_df.dropna(subset=['GeoDistrict']).groupby('GeoDistrict').agg({'Total Patients': 'sum', 'Facilities': 'sum', 'Weighted Avg': 'mean', 'Uptime %': 'mean'}).round(1).reset_index()
            merged['Lat'] = merged['GeoDistrict'].map(lambda x: BIHAR_COORDS.get(x, (None, None))[0])
            merged['Lon'] = merged['GeoDistrict'].map(lambda x: BIHAR_COORDS.get(x, (None, None))[1])
            merged = merged.dropna(subset=['Lat', 'Lon'])
            
            if merged.empty:
                st.warning("No mappable data.")
            else:
                fig_map = px.scatter(
                    merged,
                    x='Lon', y='Lat',
                    size='Total Patients',
                    color=map_metric,
                    color_continuous_scale='RdYlGn' if map_metric == 'Uptime %' else 'Viridis',
                    hover_name='GeoDistrict',
                    hover_data={'Total Patients': True, 'Weighted Avg': True, 'Uptime %': True, 'Facilities': True, 'Lat': False, 'Lon': False},
                    size_max=70,
                    title=f'Bihar District Performance — {map_metric}'
                )
                fig_map.update_traces(marker=dict(line=dict(width=1, color='white')))
                fig_map.update_layout(
                    height=700,
                    xaxis=dict(title="Longitude", showgrid=True, gridcolor='#222', zeroline=False, showticklabels=False),
                    yaxis=dict(title="Latitude", showgrid=True, gridcolor='#222', zeroline=False, showticklabels=False, scaleanchor="x", scaleratio=1),
                    plot_bgcolor='#0E1117',
                    paper_bgcolor='rgba(0,0,0,0)',
                    coloraxis_colorbar=dict(title=map_metric)
                )
                st.plotly_chart(fig_map, use_container_width=True)
                
                st.divider()
                st.markdown("#### 📊 District Data Table")
                st.dataframe(merged.sort_values(map_metric, ascending=False).drop(columns=['Lat', 'Lon']), use_container_width=True, hide_index=True)
    else:
        st.info("Click 'Generate Map' to visualize district performance.")

# ===== TAB 6: COMPARE DISTRICTS =====
with tab6:
    st.markdown("### ⚖️ Compare Two Districts Head-to-Head")
    ca, cb = st.columns(2)
    with ca: district_a = st.selectbox("🔵 District A", available_sheets, index=0, key='cmp_a')
    with cb: district_b = st.selectbox("🔴 District B", available_sheets, index=min(1, len(available_sheets) - 1), key='cmp_b')
    if district_a and district_b:
        df_a = pd.read_excel(xls, sheet_name=district_a)
        df_b = pd.read_excel(xls, sheet_name=district_b)
        pa, ra, sa = process_district_df(df_a, time_filter)
        pb, rb, sb = process_district_df(df_b, time_filter)
        if pa is None or pb is None:
            st.error("One of the sheets does not have the expected columns.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"#### 🔵 {district_a}")
                m1, m2, m3 = st.columns(3)
                m1.metric("Total", f"{sa['total']:,}")
                m2.metric("Avg/Day", sa['weighted_avg'])
                m3.metric("Uptime", f"{calc_uptime(sa)}%")
            with col2:
                st.markdown(f"#### 🔴 {district_b}")
                m1, m2, m3 = st.columns(3)
                m1.metric("Total", f"{sb['total']:,}")
                m2.metric("Avg/Day", sb['weighted_avg'])
                m3.metric("Uptime", f"{calc_uptime(sb)}%")
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
            fig_c = px.line(combined, x='Date', y='Patients', color='District', markers=True, color_discrete_map={district_a: '#3498db', district_b: '#e74c3c'})
            fig_c.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=450)
            st.plotly_chart(fig_c, use_container_width=True)
            st.divider()
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
