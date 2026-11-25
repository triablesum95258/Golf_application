import streamlit as st
import pandas as pd
import math
from streamlit_geolocation import streamlit_geolocation
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Golf GPS Shot Tracker", layout="wide")

# Custom CSS for sizing the button
st.markdown("""
<style>
iframe {
    transform: scale(1.5);
    transform-origin: top left;
    margin-bottom: 30px;
    height: 50px !important;
}
</style>
""", unsafe_allow_html=True)

st.title("⛳ Mobile Golf GPS & Shot Tracker")

# Initialize session state
if "shots" not in st.session_state:
    st.session_state.shots = []

# Sidebar settings
st.sidebar.header("Current Hole Settings")
current_hole = st.sidebar.selectbox("Hole Number", list(range(1, 19)))
hole_par = st.sidebar.selectbox("Hole Par", [3, 4, 5], index=1)

st.subheader(f"📍 Tracking Hole {current_hole} (Par {hole_par})")
st.write("Tap the button below to fetch your current GPS position:")

# Get location data
location = streamlit_geolocation()

if location and location.get("latitude") and location.get("longitude"):
    lat = location["latitude"]
    lon = location["longitude"]
    accuracy = location.get("accuracy", "Unknown")
    
    st.success(f"Location acquired! (Accuracy: ~{accuracy} meters)")
    
    if st.button("Record Shot Location", type="primary"):
        shot_num = len([s for s in st.session_state.shots if s["Hole"] == current_hole]) + 1
        st.session_state.shots.append({
            "Hole": current_hole,
            "Shot": shot_num,
            "Latitude": lat,
            "Longitude": lon
        })
        st.success(f"Shot {shot_num} saved successfully!")

# --- DEFINE SHOTS DATAFRAME FIRST ---
current_hole_shots = pd.DataFrame()
if st.session_state.shots:
    df_shots = pd.DataFrame(st.session_state.shots)
    current_hole_shots = df_shots[df_shots["Hole"] == current_hole]

# --- NOW RENDER MAP & TABLES USING THE DATAFRAME ---
if not current_hole_shots.empty:
    st.write("### Recorded Shots on This Hole")
    st.dataframe(current_hole_shots)

    st.write("### Shot Path Map")
    
    # Start map centered on the first shot
    first_shot = current_hole_shots.iloc[0]
    m = folium.Map(location=[first_shot["Latitude"], first_shot["Longitude"]], zoom_start=18)
    
    points = []
    for index, row in current_hole_shots.iterrows():
        lat, lon = row["Latitude"], row["Longitude"]
        shot_num = row["Shot"]
        points.append((lat, lon))
        
        folium.Marker(
            location=[lat, lon],
            popup=f"Shot {shot_num}",
            tooltip=f"Shot {shot_num}"
        ).add_to(m)
        
    # Draw a line connecting the shots in order
    if len(points) > 1:
        folium.PolyLine(points, color="blue", weight=4, opacity=0.8).add_to(m)
        
        # Automatically fit the map boundaries to include all shots nicely
        m.fit_bounds(points, padding=(30, 30))
        
    # Render map full-width so it fits mobile screens properly
    st_folium(m, use_container_width=True, height=400)

    # Calculate distances
    if len(current_hole_shots) > 1:
        st.write("### Calculated Shot Distances")
        
        def haversine(lat1, lon1, lat2, lon2):
            R = 3958.8
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return R * c * 1760

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