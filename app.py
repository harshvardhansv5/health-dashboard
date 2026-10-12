import streamlit as st
import pandas as pd
import plotly.express as px

# --- HARDCODED ZM DATA (Extracted from "Location and zm list.xlsx") ---
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

# --- NAME DISCREPANCIES (ZM File vs Main Data File) ---
DISTRICT_MAP = {
    "Seikhpura": "Sheikhpura",
    "Rohtas": "Sasaram"
}

# --- PAGE SETUP ---
st.set_page_config(page_title="District Hub & Spoke Dashboard", layout="wide")
st.title("🏥 District Hub & Spoke Patient Footfall Dashboard")
st.markdown("Upload the Main Data file. The app will automatically detect which districts have data.")

# --- FILE UPLOADER ---
uploaded_data_file = st.file_uploader("Upload the Main Data File (Hub Wise Collection)", type=["xlsx", "csv"])

if uploaded_data_file is not None:
    try:
        # Load the Excel file and get sheet names
        xls = pd.ExcelFile(uploaded_data_file)
        available_sheets = xls.sheet_names
        
        # --- DROPDOWN 1: ZM NAME ---
        zm_list = list(ZM_DATA.keys())
        selected_zm = st.selectbox("Select ZM Name", zm_list)
        
        # --- DATA AVAILABILITY SUMMARY FOR THIS ZM ---
        st.markdown(f"#### 📊 Data Availability for {selected_zm}")
        
        # Check each district managed by this ZM
        availability_data = []
        for district, hubs in ZM_DATA[selected_zm].items():
            sheet_name = DISTRICT_MAP.get(district, district)
            
            # Check if the sheet exists
            sheet_found = False
            for s in available_sheets:
                if s == sheet_name or sheet_name.lower() in s.lower() or s.lower() in sheet_name.lower():
                    sheet_found = True
                    break
            
            if sheet_found:
                status = "✅ Data Available"
            else:
                status = "⏳ Data Pending"
            
            availability_data.append({
                "District": district,
                "Status": status,
                "Hubs": ", ".join(hubs)
            })
        
        availability_df = pd.DataFrame(availability_data)
        st.dataframe(availability_df, hide_index=True, use_container_width=True)
        
        # --- DROPDOWN 2: DISTRICT ---
        district_list = list(ZM_DATA[selected_zm].keys())
        selected_district_zm = st.selectbox("Select District", district_list)
        
        # --- DROPDOWN 3: HUB ---
        hub_list = ZM_DATA[selected_zm][selected_district_zm]
        selected_hub_zm = st.selectbox("Select Hub", hub_list)
        
        # --- RESOLVE SHEET NAME ---
        target_district = DISTRICT_MAP.get(selected_district_zm, selected_district_zm)
        
        sheet_to_load = None
        for s in available_sheets:
            if s == target_district or target_district.lower() in s.lower() or s.lower() in target_district.lower():
                sheet_to_load = s
                break
        
        # --- SCENARIO 1: SHEET NOT FOUND ---
        if not sheet_to_load:
            st.warning(f"⏳ **Data Not Yet Available for {selected_district_zm}**")
            st.info(
                f"The data for this district will be added as soon as the new Excel sheet is shared. "
                f"In the meantime, you can view data for other districts under **{selected_zm}**."
            )
            st.stop()
        
        # --- SCENARIO 2: SHEET FOUND, LOAD DATA ---
        df = pd.read_excel(xls, sheet_name=sheet_to_load)
        df.columns = [str(c).strip() for c in df.columns]
        
        facility_col = [c for c in df.columns if 'Name of the Hospital' in c]
        
        if not facility_col:
            st.warning(f"⏳ **Data Structure Not Yet Ready for {selected_district_zm}**")
            st.info("The sheet exists but does not yet contain the expected 'Name of the Hospital' column.")
            st.stop()
        
        facility_col = facility_col[0]
        all_facilities = df[facility_col].dropna().tolist()
        all_facilities = [f for f in all_facilities if 'TOTAL' not in str(f).upper()]
        
        # --- SCENARIO 3: SHEET FOUND, NO DATE COLUMNS YET ---
        date_cols = [c for c in df.columns if 'Total number of patients' in c]
        
        if not date_cols:
            st.warning(f"⏳ **Patient Data Not Yet Available for {selected_district_zm}**")
            st.info(
                f"The sheet for **{selected_district_zm}** exists with facility names, "
                f"but daily patient data columns have not been added yet. "
                f"This will be automatically detected when the updated Excel file is shared."
            )
            st.stop()
        
        # --- SCENARIO 4: FULL DATA AVAILABLE ---
        plot_df = df[df[facility_col].isin(all_facilities)][[facility_col] + date_cols].copy()
        
        for col in date_cols:
            plot_df[col] = pd.to_numeric(plot_df[col], errors='coerce').fillna(0)
        
        plot_df['Total Patients'] = plot_df[date_cols].sum(axis=1)
        plot_df['Average Patients'] = plot_df[date_cols].mean(axis=1).round(1)
        plot_df['Zero Days'] = (plot_df[date_cols] == 0).sum(axis=1)
        
        # --- CONTROLS ---
        st.markdown("### Dashboard Controls")
        col1, col2 = st.columns(2)
        
        with col1:
            metric_option = st.radio(
                "Select Metric to Display:",
                ("Average Patients (30-Day Avg)", "Total Patients", "Zero Days"),
                horizontal=True
            )
            
        with col2:
            sort_option = st.selectbox(
                "Sort Graph By:",
                ["Highest to Lowest", "Lowest to Highest"]
            )
        
        if "Average" in metric_option:
            metric_col = 'Average Patients'
        elif "Total" in metric_option:
            metric_col = 'Total Patients'
        else:
            metric_col = 'Zero Days'

        ascending = True if sort_option == "Lowest to Highest" else False
        plot_df = plot_df.sort_values(by=metric_col, ascending=ascending)
        
        # --- TOP 5 & BOTTOM 5 HIGHLIGHT LOGIC ---
        plot_df['Highlight_Group'] = 'Others (Average Performers)'
        total_rows = len(plot_df)
        
        if total_rows > 10:
            top_5_idx = plot_df.nlargest(5, metric_col).index
            bottom_5_idx = plot_df.nsmallest(5, metric_col).index
            
            plot_df.loc[top_5_idx, 'Highlight_Group'] = 'Top 5 Performers'
            plot_df.loc[bottom_5_idx, 'Highlight_Group'] = 'Bottom 5 Performers'
        
        # --- GRAPH GENERATION ---
        st.markdown(f"### {metric_option}: {selected_district_zm} District (Hub: {selected_hub_zm})")
        
        fig = px.bar(
            plot_df, 
            x=facility_col, 
            y=metric_col,
            color='Highlight_Group',
            color_discrete_map={
                'Top 5 Performers': '#2ecc71',
                'Bottom 5 Performers': '#e74c3c',
                'Others (Average Performers)': '#95a5a6'
            },
            labels={
                facility_col: 'Facility (Spoke)', 
                'Highlight_Group': 'Performance',
                metric_col: metric_option
            },
            hover_data={
                'Highlight_Group': False,
                'Total Patients': True,
                'Average Patients': ':.1f',
                'Zero Days': True
            },
            title=f"{metric_option} per Facility"
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            xaxis_title="Spokes (Facilities)",
            yaxis_title=metric_option,
            legend_title="Category",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # --- IMPROVED DATA TABLE ---
        st.markdown("### Detailed Data Table")
        
        display_df = plot_df[[facility_col, 'Total Patients', 'Average Patients', 'Zero Days']].copy()
        display_df.columns = ['Facility Name', 'Total Patients', 'Avg Daily Patients', 'Zero-Footfall Days']
        
        st.dataframe(
            display_df,
            column_config={
                "Facility Name": st.column_config.TextColumn("Facility Name", width="medium"),
                "Total Patients": st.column_config.NumberColumn(
                    "Total Patients", 
                    format="%d",
                    help="Total patients over the entire period"
                ),
                "Avg Daily Patients": st.column_config.ProgressColumn(
                    "Avg Daily Patients",
                    help="Average patients per day",
                    format="%.1f",
                    min_value=0,
                    max_value=float(display_df['Avg Daily Patients'].max()) if not display_df.empty else 100,
                ),
                "Zero-Footfall Days": st.column_config.NumberColumn(
                    "Zero-Footfall Days", 
                    format="%d",
                    help="Number of days with 0 patients"
                ),
            },
            hide_index=True,
            use_container_width=True
        )
        
        st.caption(f"Note: Average is calculated over the {len(date_cols)} days present in this sheet's data columns.")
                    
    except Exception as e:
        st.error(f"An error occurred: {e}")