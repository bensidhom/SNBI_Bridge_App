import streamlit as st
import sqlite3
import pandas as pd
import folium
from streamlit_folium import folium_static

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
    SELECT bridge_name, latitude, longitude 
    FROM bridges 
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
''', conn)

if not bridges_df.empty:
    # Create Folium map centered on average location
    avg_lat = bridges_df['latitude'].mean()
    avg_lon = bridges_df['longitude'].mean()
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=10)

    # Add markers for each bridge
    for _, row in bridges_df.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=row['bridge_name'],
            tooltip=row['bridge_name']
        ).add_to(m)

    # Display the map in Streamlit
    folium_static(m, width=700, height=500)
else:
    st.write('No bridge locations available in the database.')

# Close the connection
conn.close()