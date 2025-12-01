import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
import os
import json
import spacy
import folium
import requests
import base64  # For handling local images
from streamlit_folium import folium_static
from gemini import Gemini

# Load environment variables
load_dotenv()
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Load NLP model
nlp = spacy.load("en_core_web_sm")
def set_background_online(image_url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: url({image_url});
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Call the function with the image URL
set_background_online("https://blog.erasmusgeneration.org/sites/default/files/articles/2022-03/travelling_alone_all_across_the_globe.jpg")
import streamlit as st

# CSS for text styles
st.markdown(
    """
    <style>
    /* Text styling with shadow */
    .content h1, .content h2, .content h3, .content p {
        color: white; /* Text color */
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8); /* Black text shadow */
        text-align: center; /* Center text */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Function to extract locations
def extract_locations(text):
    if isinstance(text, dict):
        text = " ".join(str(value) for value in text.values())
    
    locations = {}
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "GPE" or ent.label_ == "LOC":  # Geographic locations
            geocoded = geocode_location(ent.text)
            if geocoded:
                locations[ent.text] = geocoded
    return locations

# Remove Google Maps API dependency
def geocode_location(location):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        data = response.json()

        if data:
            # Extract the latitude and longitude of the first result
            latitude = float(data[0]["lat"])
            longitude = float(data[0]["lon"])
            return (latitude, longitude)
        else:
            return None  # No results found
    except Exception as e:
        st.write(f"Error geocoding {location}: {e}")
        return None

# Session state management
if 'counter' not in st.session_state:
    st.session_state['counter'] = 0
if 'generate_button_clicked' not in st.session_state:
    st.session_state["generate_button_clicked"] = False
if 'model' not in st.session_state:
    st.session_state["model"] = None
if 'response' not in st.session_state:
    st.session_state["response"] = {}
if 'current_day' not in st.session_state:
    st.session_state['current_day'] = 1  # Track the current day displayed

def main():
    session_state = st.session_state
        
    st.title("Goa Travel Planner")
    model = session_state["model"]

    col1, col2, col3 = st.columns([1, 4, 2])
    
    # Sidebar for trip details
    st.sidebar.header("Trip Details")
    days = st.sidebar.number_input("For how many days?", min_value=1, value=3)
    members = st.sidebar.number_input("How big is your group?", min_value=1, value=1)

    # Performance factor options
    st.sidebar.header("Performance Factors")
    sun_tan = st.sidebar.checkbox("Focus on Sun Tan", value=True)
    fitness = st.sidebar.checkbox("Include Fitness Activities", value=True)
    nightlife = st.sidebar.checkbox("Enjoy Nightlife", value=True)
    sightseeing = st.sidebar.checkbox("Sightseeing", value=True)
    photography = st.sidebar.checkbox("Photography", value=True)
    avoid_hangovers = st.sidebar.checkbox("Avoid Hangovers", value=True)

    preferences = []
    if sun_tan: preferences.append("sun tan")
    if fitness: preferences.append("fitness")
    if nightlife: preferences.append("nightlife")
    if sightseeing: preferences.append("sightseeing")
    if photography: preferences.append("photography")
    if avoid_hangovers: preferences.append("avoiding hangovers")
    
    if st.sidebar.button("Generate Trip Plan"):
        model = Gemini(days, members, preferences)
        response = model.get_response(markdown=False)
        st.session_state["model"] = model
        st.session_state["response"] = response
        st.session_state["generate_button_clicked"] = True
        st.session_state['counter'] = 0  # Reset counter on new plan generation
        st.session_state['current_day'] = 1  # Reset current day to 1

    with col2:
        st.title("Trip Plan")
        response = st.session_state["response"]
        
        if session_state["generate_button_clicked"]:
            current_day = st.session_state['current_day']
            if current_day <= days:
                current_day_key = f"Day {current_day}"
                current_day_info = response.get(current_day_key, None)
                if current_day_info:
                    st.write(f"## {current_day_key}")

                    # Include preferred options as side headings
                    st.subheader("Preferences:")
                    for pref in preferences:
                        st.write(f"- {pref.capitalize()}")
                    
                    # Displaying the trip plan with sections
                    for key, value in current_day_info.items():
                        st.markdown(f"### {key}")
                        st.markdown(value.strip())

                else:
                    st.write(f"No information available for {current_day_key}.")
                
                if current_day < days:
                    if st.button("Next Day"):
                        st.session_state['current_day'] += 1
                else:
                    st.button("Next Day", disabled=True)  # Disable if it's the last day

    with col3:
        if session_state["generate_button_clicked"]:
            current_day = st.session_state['current_day']
            current_day_key = f"Day {current_day}"
            current_day_info = response.get(current_day_key, None)

            if current_day_info:
                # Extract locations for the current day
                current_day_text = " ".join(current_day_info.values())
                locations = extract_locations(current_day_text)

                # Generate map for current day locations
                coordinates = [loc for loc in locations.values() if loc is not None]
                map_center = (
                    [sum(coord) / len(coord) for coord in zip(*coordinates)]
                    if coordinates
                    else [15.2993, 74.1240]  # Default to Goa center
                )
                mymap = folium.Map(location=map_center, zoom_start=12)

                for place_name, loc in locations.items():
                    if loc:
                        folium.Marker(loc, popup=place_name).add_to(mymap)

                # Display map
                st.markdown("<div style='text-align: right; font-size: 30px; font-weight: bold;'>Map Viewer</div>", unsafe_allow_html=True)
                folium_static(mymap, width=600, height=400)
            else:
                st.write("No locations available for the current day.")




if __name__ == '__main__':
    main()
