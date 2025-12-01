from dotenv import load_dotenv
import google.generativeai as genai
import os
import json
import textwrap

# Load environment variables
load_dotenv()

# Retrieve the API key from the environment variable
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Error: API key not found. Please check your .env file.")

# Configure the Generative AI model with the API key
genai.configure(api_key=api_key)

class Gemini:
    def __init__(self, days, members, preferences):
        self.days = days
        self.members = members
        self.preferences = preferences
        
        self.model = genai.GenerativeModel('gemini-pro')
        
    @staticmethod    
    def to_markdown(text):
        text = text.replace('•', '  *')
        return textwrap.indent(text, '> ', predicate=lambda _: True)

    def parse_trip_plan(self, trip_plan):
        days = trip_plan.split("**Day ")[1:]  
        trip_dict = {}
        for i, day in enumerate(days, start=1):
            day_num = f"Day {i}"
            parts = day.split("*Morning:*")
            morning = parts[1].split("*Afternoon:*")[0].strip() if len(parts) > 1 else ""
            afternoon = parts[1].split("*Afternoon:*")[1].split("*Evening:*")[0].strip() if len(parts[1].split("*Afternoon:*")) > 1 else ""
            evening = parts[1].split("*Evening:*")[1].strip() if len(parts[1].split("*Evening:*")) > 1 else ""
            trip_dict[day_num] = {
                "*Morning*:": f"\n{morning}\n",
                "*Afternoon*:": f"\n{afternoon}\n",
                "*Evening*:": f"\n{evening}\n"
            }
        with open("gemini_answer.json", "w") as json_file:
            json.dump(trip_dict, json_file, indent=4)
        return trip_dict
    
    def get_response(self, markdown=True):
        preferences_text = ", ".join(self.preferences) if self.preferences else "none"
        prompt = f"""Generate a trip plan for Goa spanning {self.days} days for a group of {self.members}.
        We are interested in a mix of historical sightseeing, cultural experiences, and delicious food, with specific focus on: {preferences_text}.
        Provide a detailed itinerary for each day, highlighting the activities corresponding to the performance factors selected.
        Exclude any prices or costs. Make sure it is utf-8 encoded. I want the output in that format:
        **Day 1:**
        *Morning:*
        *Afternoon:*
        *Evening:* 

        **Day 2:**
        *Morning:*
        *Afternoon:*
        *Evening:* 
        """
        
        response = self.model.generate_content(prompt)
        if response.parts:
            response = response.parts[0].text
        
        response = self.parse_trip_plan(response)
        return response
