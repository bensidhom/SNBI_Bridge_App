import streamlit as st
import sqlite3
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium import plugins
import plotly.express as px
from datetime import datetime


# Complete US state/territory FIPS code mapping (used in National Bridge Inventory - NBI)
# Codes are 2-digit (stored as int 1-78). Includes all 50 states + DC + territories
STATE_MAP = {
    1: 'Alabama (AL)',
    2: 'Alaska (AK)',
    4: 'Arizona (AZ)',
    5: 'Arkansas (AR)',
    6: 'California (CA)',
    8: 'Colorado (CO)',
    9: 'Connecticut (CT)',
    10: 'Delaware (DE)',
    11: 'District of Columbia (DC)',
    12: 'Florida (FL)',
    13: 'Georgia (GA)',
    15: 'Hawaii (HI)',
    16: 'Idaho (ID)',
    17: 'Illinois (IL)',
    18: 'Indiana (IN)',
    19: 'Iowa (IA)',
    20: 'Kansas (KS)',
    21: 'Kentucky (KY)',
    22: 'Louisiana (LA)',
    23: 'Maine (ME)',
    24: 'Maryland (MD)',
    25: 'Massachusetts (MA)',
    26: 'Michigan (MI)',
    27: 'Minnesota (MN)',
    28: 'Mississippi (MS)',
    29: 'Missouri (MO)',
    30: 'Montana (MT)',
    31: 'Nebraska (NE)',
    32: 'Nevada (NV)',
    33: 'New Hampshire (NH)',
    34: 'New Jersey (NJ)',
    35: 'New Mexico (NM)',
    36: 'New York (NY)',
    37: 'North Carolina (NC)',
    38: 'North Dakota (ND)',
    39: 'Ohio (OH)',
    40: 'Oklahoma (OK)',
    41: 'Oregon (OR)',
    42: 'Pennsylvania (PA)',
    44: 'Rhode Island (RI)',
    45: 'South Carolina (SC)',
    46: 'South Dakota (SD)',
    47: 'Tennessee (TN)',
    48: 'Texas (TX)',
    49: 'Utah (UT)',
    50: 'Vermont (VT)',
    51: 'Virginia (VA)',
    53: 'Washington (WA)',
    54: 'West Virginia (WV)',
    55: 'Wisconsin (WI)',
    56: 'Wyoming (WY)',
    # Territories (included for completeness - NBI uses these)
    60: 'American Samoa (AS)',
    66: 'Guam (GU)',
    69: 'Northern Mariana Islands (MP)',
    72: 'Puerto Rico (PR)',
    78: 'Virgin Islands (VI)',
}
# Connect to the SQLite database
conn = sqlite3.connect('bridges5.db')

# Get list of tables dynamically
tables_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
tables = tables_df['name'].tolist()

# Sidebar for table selection
st.sidebar.title('Database Tables')
selected_table = st.sidebar.selectbox('Select a table to visualize:', tables)

# Display the selected table
if selected_table:
    st.header(f'Data from {selected_table} table')
    df = pd.read_sql_query(f'SELECT * FROM {selected_table}', conn)
    st.dataframe(df, use_container_width=True)

# Map section at the bottom
st.header('Bridge Locations Map')

# Query bridges table for locations
bridges_df = pd.read_sql_query('''
    SELECT bridge_name, bridge_number, latitude, longitude, state_code
    FROM bridges 
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
''', conn)

if not bridges_df.empty:
    # ... your existing code ...

    # Create Folium map centered on average location
    avg_lat = bridges_df['latitude'].mean()
    avg_lon = bridges_df['longitude'].mean()
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=10,
                tiles="cartodbpositron")   # ← nicer background for borders

    # ------------------ Add US state borders ------------------
    STATE_BORDERS = "https://raw.githubusercontent.com/python-visualization/folium-example-data/main/us_states.json"

    folium.GeoJson(
        STATE_BORDERS,
        name="US States",
        style_function=lambda x: {
            'fillColor': 'transparent',     # ← no fill = only borders
            'color': '#333333',             # dark gray
            'weight': 2,                    # border thickness
            'opacity': 0.7
        }
    ).add_to(m)

    # Optional: make states slightly visible (very light fill)
    # 'fillColor': '#f0f0f0', 'fillOpacity': 0.1,
    # Create cluster group
    marker_cluster = plugins.MarkerCluster(
            name="Bridges",
            overlay=True,
            control=True,
            options={"maxClusterRadius": 80, "disableClusteringAtZoom": 15}  # adjust as needed
        ).add_to(m)
    # Add markers for each bridge
    for _, row in bridges_df.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"{row['bridge_name']}<br>{row['bridge_number']}",
            tooltip=row['bridge_name']
        ).add_to(marker_cluster)

    # Optional but useful: layer control
    folium.LayerControl().add_to(m)

    # Display the map in Streamlit
    folium_static(m, width=700, height=500)
else:
    st.write('No bridge locations available in the database.')


st.header("Bridge KPIs by State")

@st.cache_data
def get_state_kpis():
    current_year = datetime.now().year  # 2026 in your case

    # Query main bridges + join features for traffic (take max AADT per bridge)
    query = """
    SELECT 
        b.state_code,
        b.bridge_number,
        b.year_built,
        b.deck_condition_rating,
        b.superstructure_condition_rating,
        b.substructure_condition_rating,
        b.culvert_condition_rating,
        b.calculated_deck_area,
        b.total_bridge_length,
        b.bridge_width_out_to_out,
        MAX(f.annual_average_daily_traffic) as aadt
    FROM bridges b
    LEFT JOIN features f 
        ON b.state_code = f.state_code AND b.bridge_number = f.bridge_number
    GROUP BY b.state_code, b.bridge_number
    """
    df = pd.read_sql_query(query, conn)

    # Convert ratings to numeric (handle 'N', NULL, etc. → NaN)
    for col in ['deck_condition_rating', 'superstructure_condition_rating', 
                'substructure_condition_rating', 'culvert_condition_rating']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Overall lowest condition (ignore NaN for culvert if not applicable)
    condition_cols = ['deck_condition_rating', 'superstructure_condition_rating', 
                      'substructure_condition_rating']
    df['lowest_condition'] = df[condition_cols].min(axis=1, skipna=True)
    
    # For culvert bridges (if lowest from main is NaN but culvert exists)
    df['lowest_condition'] = df.apply(
        lambda row: row['culvert_condition_rating'] 
        if pd.isna(row['lowest_condition']) and not pd.isna(row['culvert_condition_rating'])
        else row['lowest_condition'], axis=1
    )

    # Classify Good/Fair/Poor
    def classify_condition(rating):
        if pd.isna(rating):
            return 'Unknown'
        if rating >= 7:
            return 'Good'
        elif rating >= 5:
            return 'Fair'
        else:
            return 'Poor'

    df['condition_class'] = df['lowest_condition'].apply(classify_condition)

    # Deck area fallback
    df['deck_area'] = df['calculated_deck_area'].fillna(
        df['total_bridge_length'] * df['bridge_width_out_to_out']
    ).fillna(0)

    # Map state codes
    df['state_name'] = df['state_code'].map(STATE_MAP).fillna('Unknown')

    # Aggregate per state
    kpi_df = df.groupby(['state_code', 'state_name']).agg(
        total_bridges=('bridge_number', 'count'),
        good_bridges=('condition_class', lambda x: (x == 'Good').sum()),
        fair_bridges=('condition_class', lambda x: (x == 'Fair').sum()),
        poor_bridges=('condition_class', lambda x: (x == 'Poor').sum()),
        avg_age=('year_built', lambda x: current_year - x.mean() if x.notna().any() else None),
        total_deck_area=('deck_area', 'sum'),
        high_traffic_bridges=('aadt', lambda x: (x > 10000).sum()),
        old_bridges=('year_built', lambda x: (x < 1980).sum())
    ).reset_index()

    kpi_df['pct_good'] = (kpi_df['good_bridges'] / kpi_df['total_bridges'] * 100).round(1)
    kpi_df['pct_fair'] = (kpi_df['fair_bridges'] / kpi_df['total_bridges'] * 100).round(1)
    kpi_df['pct_poor'] = (kpi_df['poor_bridges'] / kpi_df['total_bridges'] * 100).round(1)
    kpi_df['pct_old'] = (kpi_df['old_bridges'] / kpi_df['total_bridges'] * 100).round(1)

    return kpi_df

kpi_df = get_state_kpis()

if not kpi_df.empty:
    # Sidebar filter
    states_list = sorted(kpi_df['state_name'].dropna().unique())
    selected_state = st.sidebar.selectbox("Filter KPIs by State", ["All"] + states_list)

    display_df = kpi_df if selected_state == "All" else kpi_df[kpi_df['state_name'] == selected_state]

    # KPI cards
    st.subheader("Key Metrics Overview")
    cols = st.columns(5)
    total_bridges_all = kpi_df['total_bridges'].sum()
    poor_pct_all = kpi_df['pct_poor'].mean().round(1)

    if selected_state == "All":
        cols[0].metric("Total Bridges (Nationwide)", f"{total_bridges_all:,}")
        cols[1].metric("Avg % Poor Condition", f"{poor_pct_all}%", delta_color="inverse")
    else:
        row = display_df.iloc[0]
        cols[0].metric("Total Bridges", f"{int(row['total_bridges']):,}")
        cols[1].metric("% Poor Condition", f"{row['pct_poor']}%", delta_color="inverse")
        cols[2].metric("Poor Bridges", int(row['poor_bridges']))
        cols[3].metric("Avg Age (years)", f"{row['avg_age']:.1f}" if pd.notna(row['avg_age']) else "N/A")
        cols[4].metric("% Built Before 1980", f"{row['pct_old']}%")

    # Detailed table with progress bars
    st.subheader("Detailed KPI Table by State")
    st.dataframe(
        display_df[['state_name', 'total_bridges', 'pct_good', 'pct_fair', 'pct_poor', 
                    'poor_bridges', 'avg_age', 'high_traffic_bridges', 'pct_old', 'total_deck_area']],
        column_config={
            "state_name": "State",
            "total_bridges": st.column_config.NumberColumn("Total Bridges"),
            "pct_good": st.column_config.ProgressColumn("% Good", format="%.1f%%", min_value=0, max_value=100),
            "pct_fair": st.column_config.ProgressColumn("% Fair", format="%.1f%%", min_value=0, max_value=100),
            "pct_poor": st.column_config.ProgressColumn("% Poor", format="%.1f%%", min_value=0, max_value=100),
            "poor_bridges": "Poor Bridges",
            "avg_age": st.column_config.NumberColumn("Avg Age (years)", format="%.1f"),
            "high_traffic_bridges": "High Traffic (>10k AADT)",
            "pct_old": st.column_config.ProgressColumn("% Pre-1980", format="%.1f%%", min_value=0, max_value=100),
            "total_deck_area": st.column_config.NumberColumn("Total Deck Area (sq units)", format="%.0f")
        },
        hide_index=True,
        use_container_width=True
    )

    # Visualizations
    st.subheader("Visualizations")

    # Stacked bar for condition %
    fig_cond = px.bar(
        kpi_df.sort_values('state_name'),
        x='state_name',
        y=['pct_good', 'pct_fair', 'pct_poor'],
        title="Bridge Condition Distribution by State (%)",
        labels={'value': '% of Bridges', 'variable': 'Condition'},
        color_discrete_map={'pct_good': '#00CC96', 'pct_fair': '#FFA500', 'pct_poor': '#EF553B'},
        barmode='stack'
    )
    fig_cond.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_cond, use_container_width=True)

    # Choropleth for % poor
    kpi_df['state_abbr'] = kpi_df['state_name'].apply(
        lambda x: x.split('(')[-1].rstrip(')') if '(' in str(x) else ''
    )
    fig_map = px.choropleth(
        kpi_df,
        locations='state_abbr',
        locationmode="USA-states",
        color='pct_poor',
        scope="usa",
        color_continuous_scale="Reds",
        title="% of Bridges in Poor Condition by State",
        labels={'pct_poor': '% Poor'}
    )
    fig_map.update_layout(geo_visible=False)
    st.plotly_chart(fig_map, use_container_width=True)

    # Avg age bar
    fig_age = px.bar(
        kpi_df.sort_values('avg_age', ascending=False),
        x='state_name',
        y='avg_age',
        title="Average Bridge Age by State (years)",
        color='avg_age',
        color_continuous_scale="Blues_r"
    )
    fig_age.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_age, use_container_width=True)

else:
    st.info("No bridge data available for KPI calculations.")
# Close the connection
conn.close()

