import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
import re

# --- PAGE SETUP ---
st.set_page_config(page_title="Bihar Health Dashboard", page_icon="🏥", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        border: 1px solid #333333;
        padding: 15px;
        border-radius: 10px;
    }
    div[data-testid="stMetric"] label {color: #AAAAAA !important;}
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {color: #FFFFFF !important;}
    .news-ticker-container {
        background-color: #1a1a1a; border: 1px solid #333; border-left: 5px solid #00D4FF;
        border-radius: 8px; padding: 12px 0; margin-bottom: 15px;
        overflow: hidden; position: relative;
    }
    .news-ticker-label {
        position: absolute; left: 0; top: 0; bottom: 0;
        background-color: #00D4FF; color: #000; font-weight: bold;
        padding: 12px 15px; z-index: 10; font-size: 14px;
    }
    .news-ticker-scroll {
        display: inline-block; white-space: nowrap;
        padding-left: 100%; animation: scroll 60s linear infinite; font-size: 14px;
    }
    .news-ticker-scroll:hover { animation-play-state: paused; }
    @keyframes scroll {
        0% { transform: translateX(0); }
        100% { transform: translateX(-100%); }
    }
    .news-item-up { color: #2ecc71; font-weight: 600; padding: 0 30px; }
    .news-item-down { color: #e74c3c; font-weight: 600; padding: 0 30px; }
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
    
    return plot_df, raw_text_df, {
        'total': district_total, 'weighted_avg': weighted_avg, 'zero_days': total_zero,
        'num_facilities': num_facilities, 'num_days': num_days,
        'facility_col': facility_col, 'active_date_cols': active_date_cols
    }

def categorize_reason(note):
    if pd.isna(note): return "No Data Entered"
    note = str(note).lower()
    if 'strike' in note: return "Doctor/Staff Strike"
    if 'lt' in note and ('leave' in note or 'not available' in note or 'nhi' in note or 'no lt' in note or 'absent' in note or 'chutti' in note): return "No Lab Technician"
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
    if len(active_date_cols) < 14:
        return news
    recent_cols = active_date_cols[-7:]
    previous_cols = active_date_cols[-14:-7]
    
    for _, row in plot_df.iterrows():
        facility = row[facility_col]
        recent_avg = pd.to_numeric(row[recent_cols], errors='coerce').fillna(0).mean()
        previous_avg = pd.to_numeric(row[previous_cols], errors='coerce').fillna(0).mean()
        
        if previous_avg >= 3:
            change_pct = ((recent_avg - previous_avg) / previous_avg) * 100
            if abs(change_pct) >= threshold:
                news.append({
                    'facility': facility, 'change': round(change_pct, 1),
                    'recent': round(recent_avg, 1), 'previous': round(previous_avg, 1)
                })
    news.sort(key=lambda x: abs(x['change']), reverse=True)
    return news

def build_change_table(plot_df, facility_col, active_date_cols):
    """Builds a detailed Week-over-Week comparison table for all facilities."""
    if len(active_date_cols) < 14:
        return None
    
    recent_cols = active_date_cols[-7:]
    previous_cols = active_date_cols[-14:-7]
    
    rows = []
    for _, row in plot_df.iterrows():
        facility = row[facility_col]
        recent_avg = pd.to_numeric(row[recent_cols], errors='coerce').fillna(0).mean()
        previous_avg = pd.to_numeric(row[previous_cols], errors='coerce').fillna(0).mean()
        recent_total = pd.to_numeric(row[recent_cols], errors='coerce').fillna(0).sum()
        previous_total = pd.to_numeric(row[previous_cols], errors='coerce').fillna(0).sum()
        
        if previous_avg > 0:
            change_pct = round(((recent_avg - previous_avg) / previous_avg) * 100, 1)
        elif recent_avg > 0:
            change_pct = 100.0  # New activity
        else:
            change_pct = 0.0
        
        # Determine status
        if change_pct >= 20:
            status = "🟢 Major Gain"
        elif change_pct >= 5:
            status = "🟢 Growth"
        elif change_pct <= -20:
            status = "🔴 Major Drop"
        elif change_pct <= -5:
            status = "🟠 Decline"
        else:
            status = "⚪ Stable"
        
        rows.append({
            'Facility Name': facility,
            'Previous Week Total': int(previous_total),
            'Previous Week Avg/Day': round(previous_avg, 1),
            'Current Week Total': int(recent_total),
            'Current Week Avg/Day': round(recent_avg, 1),
            'Change (%)': change_pct,
            'Status': status
        })
    
    change_df = pd.DataFrame(rows)
    change_df = change_df.sort_values('Change (%)', ascending=False).reset_index(drop=True)
    return change_df

def build_monthly_scorecard(plot_df, raw_text_df, facility_col, active_date_cols):
    """Builds a comprehensive monthly summary per facility."""
    rows = []
    for _, row in plot_df.iterrows():
        facility = row[facility_col]
        values = pd.to_numeric(row[active_date_cols], errors='coerce').fillna(0)
        
        # Find best and worst days
        best_val = values.max()
        worst_val = values.min()
        
        # Count operational issues from raw text
        raw_row = raw_text_df[raw_text_df[facility_col] == facility]
        issue_count = 0
        if not raw_row.empty:
            for col in active_date_cols:
                val = raw_row.iloc[0][col]
                if pd.notna(val) and not isinstance(val, (int, float)):
                    issue_count += 1
        
        rows.append({
            'Facility Name': facility,
            'Total Patients': int(values.sum()),
            'Avg Daily Patients': round(values.mean(), 1),
            'Zero-Footfall Days': int((values == 0).sum()),
            'Best Day': int(best_val),
            'Worst Day': int(worst_val),
            'Days with Operational Issues': issue_count,
            'Total Days Reported': len(active_date_cols)
        })
    
    scorecard = pd.DataFrame(rows).sort_values('Avg Daily Patients', ascending=False).reset_index(drop=True)
    return scorecard

# --- SIDEBAR ---
with st.sidebar:
    st.title("Control Panel")
    uploaded_data_file = st.file_uploader("Upload Main Data File", type=["xlsx", "csv"])
    
    if uploaded_data_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_data_file)
            available_sheets = xls.sheet_names
            st.divider()
            
            zm_list = list(ZM_DATA.keys())
            selected_zm = st.selectbox("Select ZM Name", zm_list)
            
            district_list = list(ZM_DATA[selected_zm].keys())
            selected_district_zm = st.selectbox("Select District", district_list)
            
            hub_list = ZM_DATA[selected_zm][selected_district_zm]
            selected_hub_zm = st.selectbox("Select Hub", hub_list)
            
            st.divider()
            
            time_filter = st.selectbox(
                "Select Time Range:",
                ["All Available Data", "Last 30 Days", "Last 7 Days", "Single Day (Latest)"]
            )
            
            st.divider()
            
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

df = pd.read_excel(xls, sheet_name=sheet_to_load)
plot_df, raw_text_df, stats = process_district_df(df, time_filter)

if plot_df is None:
    st.error("This sheet does not have the expected columns.")
    st.stop()

facility_col = stats['facility_col']

# ============================================================
# NEWS TICKER
# ============================================================
news_items = generate_news_items(plot_df, facility_col, stats['active_date_cols'], threshold=20)

if news_items:
    ticker_html = '<div class="news-ticker-container"><div class="news-ticker-label">🔴 LIVE</div><div class="news-ticker-scroll">'
    for item in news_items:
        if item['change'] > 0:
            ticker_html += f'<span class="news-item-up">📈 {item["facility"]} | +{item["change"]}% | ({item["previous"]} → {item["recent"]} patients/day) &nbsp;&nbsp;◆&nbsp;&nbsp;</span>'
        else:
            ticker_html += f'<span class="news-item-down">📉 {item["facility"]} | {item["change"]}% | ({item["previous"]} → {item["recent"]} patients/day) &nbsp;&nbsp;◆&nbsp;&nbsp;</span>'
    ticker_html += '</div></div>'
    st.markdown(ticker_html, unsafe_allow_html=True)

# --- CREATE TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 District Dashboard",
    "🏆 State Leaderboard",
    "📈 Trends & Analytics",
    "🚨 Diagnostics",
    "📥 Reports & Downloads"
])

# ============================================================
# TAB 1: DISTRICT DASHBOARD
# ============================================================
with tab1:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label=f"Total Patients ({time_filter})", value=f"{stats['total']:,}")
    with col2:
        st.metric(label="Weighted Avg Daily Patients", value=f"{stats['weighted_avg']}")
    with col3:
        st.metric(label=f"Zero-Footfall Days", value=f"{stats['zero_days']}")
    
    st.divider()
    
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 1, 1])
    with col_ctrl1:
        metric_option = st.radio("Metric:", ("Average Patients", "Total Patients", "Zero Days"), horizontal=True, key="dash_metric")
    with col_ctrl2:
        sort_option = st.selectbox("Sort:", ["Highest to Lowest", "Lowest to Highest"], key="dash_sort")
    with col_ctrl3:
        active_only = st.checkbox("Exclude Inactive", value=False, key="dash_active")
    
    metric_col = {'Average Patients': 'Average Patients', 'Total Patients': 'Total Patients', 'Zero Days': 'Zero Days'}[metric_option]
    
    filtered = plot_df.copy()
    if active_only:
        filtered = filtered[filtered['Total Patients'] > 0]
    
    if filtered.empty:
        st.warning("No data matches the filters.")
    else:
        ascending = sort_option == "Lowest to Highest"
        sorted_df = filtered.sort_values(by=metric_col, ascending=not ascending)
        sorted_df['Highlight'] = 'Others'
        if len(sorted_df) > 10:
            sorted_df.loc[sorted_df.nlargest(5, metric_col).index, 'Highlight'] = 'Top 5'
            sorted_df.loc[sorted_df.nsmallest(5, metric_col).index, 'Highlight'] = 'Bottom 5'
        
        fig = px.bar(sorted_df, y=facility_col, x=metric_col, orientation='h',
                     color='Highlight',
                     color_discrete_map={'Top 5': '#2ecc71', 'Bottom 5': '#e74c3c', 'Others': '#95a5a6'},
                     title=f"{metric_option} per Facility")
        fig.update_layout(height=max(500, len(sorted_df) * 25), yaxis=dict(autorange="reversed"),
                         plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                         legend_title="", xaxis_title=metric_option, yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 2: STATE LEADERBOARD
# ============================================================
with tab2:
    st.markdown("### 🏆 All Districts Ranked (Statewide Leaderboard)")
    st.caption("Ranking calculated across all districts in the uploaded master file.")
    
    if st.button("🔄 Calculate Leaderboard", key="calc_leaderboard"):
        progress = st.progress(0, text="Processing districts...")
        leaderboard_data = []
        
        for i, sheet in enumerate(available_sheets):
            try:
                sdf = pd.read_excel(xls, sheet_name=sheet)
                _, _, s_stats = process_district_df(sdf, time_filter)
                if s_stats and s_stats['total'] > 0:
                    leaderboard_data.append({
                        'District': sheet, 'Total Patients': s_stats['total'],
                        'Weighted Avg': s_stats['weighted_avg'], 'Zero Days': s_stats['zero_days'],
                        'Facilities': s_stats['num_facilities']
                    })
                elif s_stats:
                    leaderboard_data.append({
                        'District': sheet, 'Total Patients': 0,
                        'Weighted Avg': 0, 'Zero Days': s_stats['zero_days'],
                        'Facilities': s_stats['num_facilities']
                    })
            except Exception:
                pass
            progress.progress((i + 1) / len(available_sheets), text=f"Processing {sheet}...")
        
        progress.empty()
        
        if leaderboard_data:
            lb_df = pd.DataFrame(leaderboard_data)
            lb_df = lb_df.sort_values('Total Patients', ascending=False).reset_index(drop=True)
            lb_df.index = lb_df.index + 1
            lb_df.index.name = 'Rank'
            
            def add_medal(rank):
                if rank == 1: return "🥇"
                elif rank == 2: return "🥈"
                elif rank == 3: return "🥉"
                return ""
            
            lb_df['District'] = lb_df.apply(lambda row: f"{add_medal(row.name)} {row['District']}".strip(), axis=1)
            st.dataframe(lb_df, use_container_width=True)
            
            st.divider()
            st.markdown("#### 📊 Top 15 Districts Chart")
            top15 = lb_df.head(15)
            fig_lb = px.bar(top15, x='Total Patients', y='District', orientation='h',
                            color='Total Patients', color_continuous_scale='Viridis',
                            title='Top 15 Districts by Total Patients')
            fig_lb.update_layout(yaxis=dict(autorange="reversed"), height=500,
                                 plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                 coloraxis_showscale=False)
            st.plotly_chart(fig_lb, use_container_width=True)
        else:
            st.warning("No districts with data found.")
    else:
        st.info("Click the button above to generate the statewide leaderboard. This may take 30-60 seconds.")

# ============================================================
# TAB 3: TRENDS & ANALYTICS
# ============================================================
with tab3:
    st.markdown(f"### 📈 Trends for {selected_district_zm}")
    
    st.markdown("#### Daily Patient Trend")
    if 'active_date_cols' in stats and stats['active_date_cols']:
        trend_data = []
        for col in stats['active_date_cols']:
            date_val = extract_date(col)
            daily_total = pd.to_numeric(plot_df[col], errors='coerce').fillna(0).sum()
            if pd.notna(date_val):
                trend_data.append({'Date': date_val, 'Patients': daily_total})
        
        if trend_data:
            trend_df = pd.DataFrame(trend_data).sort_values('Date')
            fig_trend = px.line(trend_df, x='Date', y='Patients', markers=True,
                                title='Daily Patient Footfall Trend')
            fig_trend.update_traces(line_color='#00D4FF', line_width=3)
            fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                    xaxis_title="Date", yaxis_title="Total Patients")
            st.plotly_chart(fig_trend, use_container_width=True)
    
    st.divider()
    
    st.markdown("#### Day-of-Week Analysis")
    if 'active_date_cols' in stats:
        dow_data = []
        for col in stats['active_date_cols']:
            date_val = extract_date(col)
            daily_total = pd.to_numeric(plot_df[col], errors='coerce').fillna(0).sum()
            if pd.notna(date_val):
                dow_data.append({'Day': date_val.strftime('%A'), 'Patients': daily_total})
        if dow_data:
            dow_df = pd.DataFrame(dow_data)
            dow_summary = dow_df.groupby('Day')['Patients'].mean().round(1).reset_index()
            weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dow_summary['Day'] = pd.Categorical(dow_summary['Day'], categories=weekday_order, ordered=True)
            dow_summary = dow_summary.sort_values('Day')
            
            fig_dow = px.bar(dow_summary, x='Day', y='Patients', color='Patients',
                             color_continuous_scale='Blues', title='Average Patients by Day of Week')
            fig_dow.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                  coloraxis_showscale=False, xaxis_title="", yaxis_title="Avg Patients")
            st.plotly_chart(fig_dow, use_container_width=True)
    
    st.divider()
    
    st.markdown("#### ⚠️ Anomaly Detector")
    st.caption("Flags facilities where the latest day's footfall dropped by more than 80% vs. the previous 7-day average.")
    
    if 'active_date_cols' in stats and len(stats['active_date_cols']) >= 8:
        recent_cols = stats['active_date_cols'][-8:-1]
        latest_col = stats['active_date_cols'][-1]
        
        anomalies = []
        for _, row in plot_df.iterrows():
            prev_avg = pd.to_numeric(row[recent_cols], errors='coerce').fillna(0).mean()
            latest_val = row[latest_col]
            latest = 0 if pd.isna(latest_val) else pd.to_numeric(latest_val, errors='coerce')
            latest = 0 if pd.isna(latest) else latest
            
            if prev_avg > 5 and latest < (prev_avg * 0.2):
                anomalies.append({
                    'Facility': row[facility_col],
                    'Prev 7-day Avg': round(prev_avg, 1),
                    'Latest Day': int(latest),
                    'Drop %': f"-{round((1 - latest/prev_avg) * 100)}%"
                })
        
        if anomalies:
            st.error(f"⚠️ {len(anomalies)} anomalies detected!")
            st.dataframe(pd.DataFrame(anomalies), use_container_width=True, hide_index=True)
        else:
            st.success("✅ No anomalies detected in the latest day.")

# ============================================================
# TAB 4: DIAGNOSTICS
# ============================================================
with tab4:
    st.markdown(f"### 🚨 Operational Diagnostics for {selected_district_zm}")
    
    st.markdown("#### Why Are Facilities Reporting Zero?")
    if raw_text_df is not None:
        all_reasons = []
        for col in stats['active_date_cols']:
            for val in raw_text_df[col]:
                if pd.notna(val) and not isinstance(val, (int, float)):
                    all_reasons.append(categorize_reason(val))
                elif pd.notna(val) and isinstance(val, (int, float)) and val == 0:
                    all_reasons.append("Reported Zero (No Note)")
        
        if all_reasons:
            reason_df = pd.DataFrame(all_reasons, columns=['Reason'])
            reason_counts = reason_df['Reason'].value_counts().reset_index()
            reason_counts.columns = ['Reason', 'Count']
            
            col_pie, col_bar = st.columns(2)
            with col_pie:
                fig_pie = px.pie(reason_counts, values='Count', names='Reason', hole=0.4,
                                 title='Reasons for Zero Footfall (Share)')
                fig_pie.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_pie, use_container_width=True)
            with col_bar:
                fig_rbar = px.bar(reason_counts, x='Count', y='Reason', orientation='h',
                                  color='Count', color_continuous_scale='Reds',
                                  title='Reasons for Zero Footfall (Count)')
                fig_rbar.update_layout(yaxis=dict(autorange="reversed"), plot_bgcolor='rgba(0,0,0,0)',
                                       paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False,
                                       xaxis_title="Days Affected", yaxis_title="")
                st.plotly_chart(fig_rbar, use_container_width=True)
    
    st.divider()
    
    st.markdown("#### Distance from Hub vs. Performance")
    st.caption("Are remote facilities being neglected?")
    
    distance_col = None
    for c in df.columns:
        if 'Spokes Distance' in str(c) or 'Distance From Hub' in str(c):
            distance_col = c
            break
    
    if distance_col:
        scatter_df = plot_df.copy()
        scatter_df['Distance'] = pd.to_numeric(df.loc[scatter_df.index, distance_col], errors='coerce')
        scatter_df = scatter_df.dropna(subset=['Distance'])
        
        if not scatter_df.empty:
            fig_scatter = px.scatter(scatter_df, x='Distance', y='Average Patients',
                                     size='Total Patients', hover_name=facility_col,
                                     color='Average Patients', color_continuous_scale='RdYlGn',
                                     title='Facility Distance vs. Average Daily Patients')
            fig_scatter.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                      xaxis_title="Distance from Hub (km)", yaxis_title="Avg Daily Patients",
                                      coloraxis_showscale=False)
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("No distance data available for this district.")
    else:
        st.info("No 'Distance From Hub' column found in this sheet.")

# ============================================================
# TAB 5: REPORTS & DOWNLOADS
# ============================================================
with tab5:
    st.markdown(f"### 📥 Reports & Downloads — {selected_district_zm}")
    st.caption(f"All downloads are filtered to: **{time_filter}**. Use the sidebar to change the time range.")
    
    # --- REPORT 1: WEEK-OVER-WEEK CHANGE REPORT ---
    st.markdown("---")
    st.markdown("### 📊 Report 1: Week-over-Week Change Report")
    st.caption("Compares the last 7 days against the previous 7 days for every facility.")
    
    change_table = build_change_table(plot_df, facility_col, stats['active_date_cols'])
    
    if change_table is not None:
        # Summary metrics
        total_gains = len(change_table[change_table['Change (%)'] >= 20])
        total_drops = len(change_table[change_table['Change (%)'] <= -20])
        
        col_g, col_d = st.columns(2)
        with col_g:
            st.metric("🟢 Facilities with Major Gains (>20%)", total_gains)
        with col_d:
            st.metric("🔴 Facilities with Major Drops (>20%)", total_drops)
        
        # Display the table
        st.dataframe(
            change_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Change (%)": st.column_config.NumberColumn("Change (%)", format="%.1f%%"),
                "Previous Week Avg/Day": st.column_config.NumberColumn("Previous Week Avg/Day", format="%.1f"),
                "Current Week Avg/Day": st.column_config.NumberColumn("Current Week Avg/Day", format="%.1f"),
            }
        )
        
        # Download button
        csv_change = change_table.to_csv(index=False).encode('utf-8')
        month_str = pd.Timestamp.now().strftime('%b_%Y')
        st.download_button(
            label=f"📥 Download WoW Change Report ({selected_district_zm})",
            data=csv_change,
            file_name=f'{selected_district_zm}_WoW_Change_{month_str}.csv',
            mime='text/csv',
            key='download_change'
        )
    else:
        st.info("⚠️ Not enough data for week-over-week comparison. Requires at least 14 days of data in the selected range.")
    
    # --- REPORT 2: MONTHLY SCORECARD ---
    st.markdown("---")
    st.markdown("### 📋 Report 2: Monthly Facility Scorecard")
    st.caption("A comprehensive summary of every facility's performance for the selected period.")
    
    scorecard = build_monthly_scorecard(plot_df, raw_text_df, facility_col, stats['active_date_cols'])
    
    st.dataframe(
        scorecard,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Avg Daily Patients": st.column_config.ProgressColumn(
                "Avg Daily Patients",
                format="%.1f",
                min_value=0,
                max_value=float(scorecard['Avg Daily Patients'].max()) if not scorecard.empty else 100,
            ),
        }
    )
    
    csv_scorecard = scorecard.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"📥 Download Monthly Scorecard ({selected_district_zm})",
        data=csv_scorecard,
        file_name=f'{selected_district_zm}_Monthly_Scorecard_{month_str}.csv',
        mime='text/csv',
        key='download_scorecard'
    )
    
    # --- REPORT 3: FULL RAW DATA EXPORT ---
    st.markdown("---")
    st.markdown("### 📁 Report 3: Full Data Export")
    st.caption("Download the complete cleaned dataset with all dates and facilities.")
    
    # Build the full export dataframe
    full_export = raw_text_df.copy()
    full_export['Total Patients'] = plot_df['Total Patients'].values
    full_export['Average Patients'] = plot_df['Average Patients'].values
    full_export['Zero Days'] = plot_df['Zero Days'].values
    
    st.dataframe(full_export.head(5), use_container_width=True, hide_index=True)
    st.caption(f"Showing first 5 rows. Full export has {len(full_export)} rows.")
    
    csv_full = full_export.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"📥 Download Full Data Export ({selected_district_zm})",
        data=csv_full,
        file_name=f'{selected_district_zm}_Full_Export_{month_str}.csv',
        mime='text/csv',
        key='download_full'
    )

# --- Footer ---
st.divider()
st.caption(f"💡 Data loaded from: **{sheet_to_load}** sheet | Time Range: **{time_filter}** | Last refreshed: {pd.Timestamp.now().strftime('%d-%b-%Y %H:%M')}")