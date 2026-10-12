import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE SETUP ---
st.set_page_config(page_title="District Hub & Spoke Dashboard", page_icon="🏥", layout="wide")

# --- HARDCODED ZM DATA ---
ZM_DATA = {
    "Keshav Kumar (Patna)": {
        "Bhojpur": ["DH Ara Bhojpur"],
        "Nalanda": ["DH Bihar Sharif Nalanda"],
        "Patna": ["DH (Guru Gobind Singh Hospital, Patna City)", "SDH Barh Patna", "SDH Danapur Patna"]
    },
    "Samir Kumar Singh (Bhagalpur)": {
        "Banka": ["DH Banka"],
        "Bhagalpur": ["DH LNJP Bhagalpur"],
        "Jamui": ["DH Jamui"],
        "Munger": ["DH Munger"]
    },
    "Manish Rai (Champaran)": {
        "East Champaran": ["DH Motihari"],
        "Sitamarhi": ["DH Sitamarhi"],
        "West Champaran": ["SDH Narkatiyaganj"]
    },
    "Mohammad Asif Nasir (Darbhanga)": {
        "Darbhanga": ["DH Darbhanga"],
        "Madhubani": ["DH Madhubani"],
        "Samastipur": ["DH Samastipur"]
    },
    "Narendra Kumar Pal (Gaya)": {
        "Aurangabad": ["DH Aurangabad"],
        "Gaya": ["Prabhawati Hospital Gaya"],
        "Nawada": ["DH Nawada"],
        "Arwal": ["DH Arwal"],
        "Jehanabad": ["DH Jehanabad"]
    },
    "Santosh Kumar (Khagaria)": {
        "Begusarai": ["DH Begusarai"],
        "Khagaria": ["DH Khagaria"],
        "Lakhisarai": ["DH Lakhisarai"],
        "Seikhpura": ["DH Sheikhpura"]
    },
    "Rupesh Kumar (Muzaffarpur)": {
        "Muzaffarpur": ["DH Muzaffarpur"],
        "Sheohar": ["Saroja Sitaram Sadar Hospital Sheohar"],
        "Vaishali": ["DH Hajipur"]
    },
    "Paras kumar Jaiswal (Purnia)": {
        "Araria": ["DH Araria"],
        "Katihar": ["DH Katihar"],
        "Kishanganj": ["DH Kishanganj"],
        "Purnia": ["CHC Krityanand Nagar"]
    },
    "Umesh Tiwari (Rohtas)": {
        "Buxar": ["DH Buxar"],
        "Kaimur": ["DH Kaimur"],
        "Rohtas": ["DH Sasaram"]
    },
    "Anant Kumar Ray (Saharsa)": {
        "Madhepura": ["DH Madhepura"],
        "Saharsa": ["DH Saharsa"],
        "Supaul": ["DH Supaul"]
    },
    "Krishna Prakash (Saran)": {
        "Gopalganj": ["DH Gopalganj"],
        "Saran": ["DH Saran"],
        "Siwan": ["DH Siwan"]
    }
}

DISTRICT_MAP = {
    "Seikhpura": "Sheikhpura",
    "Rohtas": "Sasaram"
}

# --- SIDEBAR ---
with st.sidebar:
    st.title("Control Panel")
    st.markdown("Upload the latest data file and select the filters below.")
    
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
            
            target_district = DISTRICT_MAP.get(selected_district_zm, selected_district_zm)
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
            st.error(f"Error reading file: {e}")

# --- MAIN CONTENT AREA ---
st.title("🏥 District Hub & Spoke Patient Footfall Dashboard")
st.markdown("Monitor daily pathology sample collection and patient footfall across districts.")

if uploaded_data_file is None:
    st.info("👈 Please upload the Main Data File from the sidebar to begin.")
    st.stop()

if not sheet_found:
    st.warning(f"⏳ **Data Not Yet Available for {selected_district_zm}**")
    st.info(
        f"The data for this district will be added as soon as the new Excel sheet is shared. "
        f"In the meantime, you can view data for other districts under **{selected_zm}**."
    )
    st.stop()

# --- LOAD AND PROCESS DATA ---
df = pd.read_excel(xls, sheet_name=sheet_to_load)
df.columns = [str(c).strip() for c in df.columns]

facility_col = [c for c in df.columns if 'Name of the Hospital' in c]
if not facility_col:
    st.error("Could not find the 'Name of the Hospital' column in this sheet.")
    st.stop()

facility_col = facility_col[0]
all_facilities = df[facility_col].dropna().tolist()
all_facilities = [f for f in all_facilities if 'TOTAL' not in str(f).upper()]

date_cols = [c for c in df.columns if 'Total number of patients' in c]
if not date_cols:
    st.warning(f"⏳ **Patient Data Not Yet Available for {selected_district_zm}**")
    st.info("The sheet exists but daily patient data columns have not been added yet.")
    st.stop()

plot_df = df[df[facility_col].isin(all_facilities)][[facility_col] + date_cols].copy()

for col in date_cols:
    plot_df[col] = pd.to_numeric(plot_df[col], errors='coerce').fillna(0)

plot_df['Total Patients'] = plot_df[date_cols].sum(axis=1)
plot_df['Average Patients'] = plot_df[date_cols].mean(axis=1).round(1)
plot_df['Zero Days'] = (plot_df[date_cols] == 0).sum(axis=1)

# --- METRIC CARDS (Fixed for Dark Mode) ---
total_patients = int(plot_df['Total Patients'].sum())
avg_patients = round(plot_df['Average Patients'].mean(), 1)
total_zero_days = int(plot_df['Zero Days'].sum())

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total Patients (District Wide)", value=f"{total_patients:,}")
with col2:
    st.metric(label="Avg Daily Patients (Per Facility)", value=f"{avg_patients}")
with col3:
    st.metric(label="Total Zero-Footfall Days", value=f"{total_zero_days}")

st.divider()

# --- TABS FOR GRAPH AND TABLE ---
tab1, tab2 = st.tabs(["📊 Dashboard Graphs", "📋 Detailed Data Table"])

with tab1:
    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    with col_ctrl1:
        metric_option = st.radio(
            "Select Metric to Display:",
            ("Average Patients (30-Day Avg)", "Total Patients", "Zero Days"),
            horizontal=True
        )
    with col_ctrl2:
        sort_option = st.selectbox("Sort Graph By:", ["Highest to Lowest", "Lowest to Highest"])

    if "Average" in metric_option:
        metric_col = 'Average Patients'
    elif "Total" in metric_option:
        metric_col = 'Total Patients'
    else:
        metric_col = 'Zero Days'

    ascending = True if sort_option == "Lowest to Highest" else False
    plot_df_sorted = plot_df.sort_values(by=metric_col, ascending=ascending)
    
    plot_df_sorted['Highlight_Group'] = 'Others (Average Performers)'
    total_rows = len(plot_df_sorted)
    
    if total_rows > 10:
        top_5_idx = plot_df_sorted.nlargest(5, metric_col).index
        bottom_5_idx = plot_df_sorted.nsmallest(5, metric_col).index
        
        plot_df_sorted.loc[top_5_idx, 'Highlight_Group'] = 'Top 5 Performers'
        plot_df_sorted.loc[bottom_5_idx, 'Highlight_Group'] = 'Bottom 5 Performers'
    
    fig = px.bar(
        plot_df_sorted, 
        x=facility_col, 
        y=metric_col,
        color='Highlight_Group',
        color_discrete_map={
            'Top 5 Performers': '#2ecc71',
            'Bottom 5 Performers': '#e74c3c',
            'Others (Average Performers)': '#95a5a6'
        },
        labels={facility_col: 'Facility (Spoke)', 'Highlight_Group': 'Performance', metric_col: metric_option},
        hover_data={'Highlight_Group': False, 'Total Patients': True, 'Average Patients': ':.1f', 'Zero Days': True},
        title=f"{metric_option} per Facility in {selected_district_zm}"
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        xaxis_title="Spokes (Facilities)",
        yaxis_title=metric_option,
        legend_title="Category",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### Detailed Data Table")
    display_df = plot_df[[facility_col, 'Total Patients', 'Average Patients', 'Zero Days']].copy()
    display_df.columns = ['Facility Name', 'Total Patients', 'Avg Daily Patients', 'Zero-Footfall Days']
    display_df = display_df.sort_values(by='Avg Daily Patients', ascending=False)
    
    st.dataframe(
        display_df,
        column_config={
            "Facility Name": st.column_config.TextColumn("Facility Name", width="medium"),
            "Total Patients": st.column_config.NumberColumn("Total Patients", format="%d"),
            "Avg Daily Patients": st.column_config.ProgressColumn(
                "Avg Daily Patients",
                format="%.1f",
                min_value=0,
                max_value=float(display_df['Avg Daily Patients'].max()) if not display_df.empty else 100,
            ),
            "Zero-Footfall Days": st.column_config.NumberColumn("Zero-Footfall Days", format="%d"),
        },
        hide_index=True,
        use_container_width=True
    )
    
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Data as CSV",
        data=csv,
        file_name=f'{selected_district_zm}_data.csv',
        mime='text/csv',
    )
    
    st.caption(f"Note: Average is calculated over the {len(date_cols)} days present in this sheet's data columns.")