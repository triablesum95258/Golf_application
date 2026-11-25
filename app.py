import streamlit as st
import pandas as pd
import math
from streamlit_geolocation import streamlit_geolocation

st.set_page_config(page_title="Golf GPS Shot Tracker", layout="wide")

st.markdown("""
<style>
/* Use a controlled scale and allocate layout height to prevent overlap */
iframe {
    transform: scale(1.8);
    transform-origin: top left;
    margin-bottom: 50px;
    height: 50px !important;
}
</style>
""", unsafe_allow_html=True)

# Custom CSS to make the geolocation button much larger and easier to tap on mobile
st.markdown("""
<style>
/* Targets the streamlit-geolocation custom component wrapper/button */
iframe {
    width: 100% !important;
}
div[data-testid="stHorizontalBlock"] button, .stButton button {
    height: 60px;
    font-size: 20px;
}
</style>
""", unsafe_allow_html=True)

st.title("⛳ Mobile Golf GPS & Shot Tracker")

# Initialize session state for tracking shots
if "shots" not in st.session_state:
    st.session_state.shots = []

# Sidebar settings
st.sidebar.header("Current Hole Settings")
current_hole = st.sidebar.selectbox("Hole Number", list(range(1, 19)))
hole_par = st.sidebar.selectbox("Hole Par", [3, 4, 5], index=1)

st.subheader(f"📍 Tracking Hole {current_hole} (Par {hole_par})")
st.write("Tap the button below to fetch your current GPS position:")

# Get location data from component
location = streamlit_geolocation()

# Check if location data was successfully returned
if location and location.get("latitude") and location.get("longitude"):
    lat = location["latitude"]
    lon = location["longitude"]
    accuracy = location.get("accuracy", "Unknown")
    
    st.success(f"Location acquired! (Accuracy: ~{accuracy} meters)")
    
    # Button to save the fetched GPS location into your shot log
    if st.button("Record Shot Location", type="primary", use_container_width=True):
        shot_num = len([s for s in st.session_state.shots if s["Hole"] == current_hole]) + 1
        st.session_state.shots.append({
            "Hole": current_hole,
            "Shot": shot_num,
            "Latitude": lat,
            "Longitude": lon
        })
        st.success(f"Shot {shot_num} saved at Lat: {lat:.5f}, Lon: {lon:.5f}!")

# Display recorded shots for this hole
if st.session_state.shots:
    df_shots = pd.DataFrame(st.session_state.shots)
    current_hole_shots = df_shots[df_shots["Hole"] == current_hole]
    
    if not current_hole_shots.empty:
        st.write("### Recorded Shots on This Hole")
        st.dataframe(current_hole_shots, use_container_width=True)

        # Calculate distances between consecutive shots using Haversine formula
        if len(current_hole_shots) > 1:
            st.write("### Calculated Shot Distances")
            
            def haversine(lat1, lon1, lat2, lon2):
                R = 3958.8  # Earth radius in miles
                dlat = math.radians(lat2 - lat1)
                dlon = math.radians(lon2 - lon1)
                a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                return R * c * 1760  # Convert to yards

            distances = []
            for i in range(len(current_hole_shots) - 1):
                p1 = current_hole_shots.iloc[i]
                p2 = current_hole_shots.iloc[i+1]
                dist_yards = haversine(p1["Latitude"], p1["Longitude"], p2["Latitude"], p2["Longitude"])
                distances.append({
                    "From Shot": p1["Shot"],
                    "To Shot": p2["Shot"],
                    "Distance (yards)": round(dist_yards, 1)
                })
            
            st.table(pd.DataFrame(distances))

import folium
from streamlit_folium import st_folium

# Inside your current hole shots section:
if not current_hole_shots.empty:
    st.write("### Shot Path Map")
    
    # Center map on the first shot of the hole
    first_shot = current_hole_shots.iloc[0]
    m = folium.Map(location=[first_shot["Latitude"], first_shot["Longitude"]], zoom_start=18)
    
    # Collect coordinates for line connection
    points = []
    for index, row in current_hole_shots.iterrows():
        lat, lon = row["Latitude"], row["Longitude"]
        shot_num = row["Shot"]
        points.append((lat, lon))
        
        # Add a marker for each shot
        folium.Marker(
            location=[lat, lon],
            popup=f"Shot {shot_num}",
            tooltip=f"Shot {shot_num}"
        ).add_to(m)
        
    # Draw a line connecting the shots in order
    if len(points) > 1:
        folium.PolyLine(points, color="blue", weight=4, opacity=0.8).add_to(m)
        
    # Display the map in Streamlit
    st_folium(m, width=700, height=450)

# Manual Putting & Hole-Out Section
st.subheader("🏁 Green & Hole-Out Log")
putts = st.number_input("Number of Putts on Green", min_value=0, max_value=6, value=2)
if st.button("Finish Hole & Save Round", use_container_width=True):
    st.info(f"Hole {current_hole} completed with {putts} putts logged!")