import streamlit as st
import requests
from typing import TypedDict, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq


# Define the PlannerState TypedDict
class PlannerState(TypedDict):
    messages: List[HumanMessage | AIMessage]
    city: str
    budget: str
    duration: int
    additional_input: str
    itinerary: str
    num_travelers: int


# Define the LLM
llm = ChatGroq(
    temperature=0,
    groq_api_key="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",  # Replace with your Groq API key
    model_name="llama-3.3-70b-versatile"
)

# Define the itinerary prompt
itinerary_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a helpful travel assistant. Using the provided information, generate:\n"
     "1. Top-rated attractions and activities at the destination.\n"
     "2. Suggestions aligned with user preferences (e.g., 'Hidden Gems').\n"
     "3. A well-structured itinerary with timing and grouping of activities for each day.\n"
     "4. A detailed budget breakdown for the trip, including accommodation, food, transportation, and activities.\n\n"
     "Use the following inputs (some might be missing):\n"
     "City: {city}, Budget: {budget}, Duration: {duration} days, Additional Input: {additional_input}, Number of Travelers: {num_travelers}."
     ),
    ("human", "Create a detailed itinerary for my trip."),
])


# Helper Functions
def process_optional_inputs(state: PlannerState) -> PlannerState:
    """Fill in default values for optional inputs."""
    state["budget"] = state["budget"] if state["budget"] else "moderate"
    state["duration"] = state["duration"] if state["duration"] > 0 else 3  # Default to 3 days
    state["additional_input"] = state["additional_input"] or "none"
    state["num_travelers"] = state["num_travelers"] if state["num_travelers"] > 0 else 1  # Default to 1 traveler
    return state


def get_weather(city: str, api_key: str) -> str:
    """Fetch weather data for the given city using WeatherAPI.com."""
    url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}&aqi=no"
    response = requests.get(url)
    if response.status_code == 200:
        weather_data = response.json()
        current = weather_data.get("current", {})
        condition = current.get("condition", {})
        return f"🌤️ Weather in {city}: {current['temp_c']}°C, {condition['text']}"
    else:
        return f"⚠️ Could not fetch weather data for {city}. Please check the city name and try again."


def create_itinerary(state: PlannerState, weather_api_key: str) -> str:
    """Generate a detailed itinerary with weather information."""
    # Fetch weather data
    weather_info = get_weather(state['city'], weather_api_key)

    # Generate itinerary
    response = llm.invoke(
        itinerary_prompt.format_messages(
            city=state['city'],
            budget=state['budget'],
            duration=state['duration'],
            additional_input=state['additional_input'],
            num_travelers=state['num_travelers']
        )
    )

    # Combine itinerary and weather information
    itinerary_with_weather = f"{weather_info}\n\n{response.content}"

    # Update state
    state["itinerary"] = itinerary_with_weather
    state["messages"] += [AIMessage(content=itinerary_with_weather)]

    return itinerary_with_weather


# Streamlit Application
def main():
    st.title("✈ AI-Powered Travel Planner")
    st.write("Fill in the details below to get a personalized trip itinerary.")

    # Weather API key
    weather_api_key = "ff420f0b5dce48e3b2061549251102"  # Replace with your actual Weather API key

    # Initialize state
    if "state" not in st.session_state:
        st.session_state.state = {
            "messages": [],
            "city": "",
            "budget": "",
            "duration": 0,
            "additional_input": "",
            "itinerary": "",
            "num_travelers": 1,
        }

    # Form for user inputs
    st.subheader("Trip Details")
    city = st.text_input("🏙️ Destination", placeholder="e.g., Paris")
    budget = st.selectbox("💰 Budget", ["Low", "Moderate", "High"], index=1)
    duration = st.number_input("📅 Duration (in days)", min_value=1, step=1, value=3)
    num_travelers = st.number_input("👥 Number of Travelers", min_value=1, step=1, value=1)
    additional_input = st.text_area("📝 Additional Details (optional)",
                                    placeholder="e.g., I want a mix of famous and offbeat places.")

    # Generate itinerary button
    if st.button("Generate Itinerary"):
        # Update state with user inputs
        st.session_state.state.update({
            "city": city,
            "budget": budget,
            "duration": duration,
            "additional_input": additional_input,
            "num_travelers": num_travelers,
        })

        # Process optional inputs
        st.session_state.state = process_optional_inputs(st.session_state.state)

        # Generate itinerary with weather information
        itinerary = create_itinerary(st.session_state.state, weather_api_key)

    # Display the itinerary
    st.subheader("Your Personalized Itinerary")
    if st.session_state.state["itinerary"]:
        st.markdown(st.session_state.state["itinerary"], unsafe_allow_html=True)
    else:
        st.write("Fill in the details and click 'Generate Itinerary' to see your personalized trip plan.")


if __name__ == "__main__":
    main()