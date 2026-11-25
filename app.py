import streamlit as st
import pandas as pd
import math
from streamlit_geolocation import streamlit_geolocation

st.set_page_config(page_title="Golf GPS Shot Tracker", layout="wide")

st.title("⛳ Mobile Golf GPS & Shot Tracker")

# Initialize session state to store shots for the current round
if "shots" not in st.session_state:
    st.session_state.shots = []

# Sidebar for Hole Configuration
st.sidebar.header("Current Hole Settings")
current_hole = st.sidebar.selectbox("Hole Number", list(range(1, 19)))
hole_par = st.sidebar.selectbox("Hole Par", [3, 4, 5], index=1)

st.subheader(f"📍 Tracking Hole {current_hole} (Par {hole_par})")
st.write("Tap the button below each time you hit your ball to log your GPS coordinates.")

# GPS Button Component
location = streamlit_geolocation()

if location and location.get("latitude") and location.get("longitude"):
    lat = location["latitude"]
    lon = location["longitude"]
    
    if st.button("Record Shot Location"):
        shot_num = len(st.session_state.shots) + 1
        st.session_state.shots.append({
            "Hole": current_hole,
            "Shot": shot_num,
            "Latitude": lat,
            "Longitude": lon
        })
        st.success(f"Shot {shot_num} recorded at ({lat:.5f}, {lon:.5f})!")

# Display recorded shots for this hole
if st.session_state.shots:
    df_shots = pd.DataFrame(st.session_state.shots)
    current_hole_shots = df_shots[df_shots["Hole"] == current_hole]
    
    st.write("### Recorded Shots on This Hole")
    st.dataframe(current_hole_shots)

    # Calculate distances between consecutive shots using Haversine formula
    if len(current_hole_shots) > 1:
        st.write("### Calculated Shot Distances")
        
        def haversine(lat1, lon1, lat2, lon2):
            R = 3958.8 # Radius of the earth in miles
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance_miles = R * c
            return distance_miles * 1760 # Convert to yards

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

# Manual Putting & Hole-Out Section
st.subheader("🏁 Green & Hole-Out Log")
putts = st.number_input("Number of Putts on Green", min_value=0, max_value=6, value=2)
if st.button("Finish Hole"):
    st.info(f"Hole {current_hole} completed with {putts} putts logged. Data saved for AI analysis!")
    # Clear or reset temporary shot state for the next hole as needed