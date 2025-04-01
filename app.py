import streamlit as st
from groq import Client
import requests
from bs4 import BeautifulSoup
import pandas as pd
from typing import List, Dict

GROQ_API_KEY = "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"
KATO_URL = "https://katokenya.org/kato-members-directory/"

def scrape_kato_members() -> List[Dict[str, str]]:
    """Scrape KATO members directory for Category A and B companies."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(KATO_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        members = []
        member_elements = soup.select("div.member-item")  # Adjust selector based on actual HTML
        for elem in member_elements:
            name = elem.select_one(".member-name").text.strip() if elem.select_one(".member-name") else "Unknown"
            category = elem.select_one(".member-category").text.strip() if elem.select_one(".member-category") else "Unknown"
            if "Category A" in category or "Category B" in category:
                members.append({"name": name, "category": category})
        return members
    except Exception as e:
        st.error(f"Error scraping KATO directory: {e}")
        return [
            {"name": "Abercrombie & Kent Ltd", "category": "Category A"},
            {"name": "African Horizons Travel & Safari Ltd", "category": "Category A"},
            {"name": "African Quest Safaris Ltd-Msa", "category": "Category A"},
            {"name": "African Safari Destinations Ltd", "category": "Category A"},
            {"name": "Asilia Kenya Ltd", "category": "Category A"},
        ]

def get_sample_packages() -> pd.DataFrame:
    """Simulate package data with hypothetical URLs."""
    return pd.DataFrame([
        {
            "company": "Abercrombie & Kent Ltd",
            "package": "Luxury Maasai Mara Safari",
            "price_usd": 3500,
            "days": 5,
            "locations": "Maasai Mara",
            "contents": "luxury lodge, game drives, balloon ride",
            "url": "https://www.abercrombiekent.co.uk/destinations/africa/kenya/luxury-maasai-mara-safari"
        },
        {
            "company": "African Horizons Travel",
            "package": "Amboseli & Tsavo Adventure",
            "price_usd": 1800,
            "days": 4,
            "locations": "Amboseli, Tsavo West",
            "contents": "mid-range camp, game drives, transfers",
            "url": "https://www.africanhorizonstours.com/amboseli-tsavo-adventure"
        },
        {
            "company": "African Quest Safaris Ltd-Msa",
            "package": "Coastal Safari Combo",
            "price_usd": 2200,
            "days": 6,
            "locations": "Tsavo East, Diani Beach",
            "contents": "beach resort, safari, snorkeling",
            "url": "https://www.africanquestsafaris.com/coastal-safari-combo"
        },
        {
            "company": "African Safari Destinations",
            "package": "Great Migration Experience",
            "price_usd": 2800,
            "days": 5,
            "locations": "Maasai Mara, Nairobi",
            "contents": "tented camp, migration viewing, guide",
            "url": "https://www.africansafaridestinations.com/great-migration-experience"
        },
        {
            "company": "Asilia Kenya Ltd",
            "package": "Ultimate Kenya Explorer",
            "price_usd": 4000,
            "days": 7,
            "locations": "Maasai Mara, Laikipia, Lamu",
            "contents": "luxury camps, safaris, cultural tours",
            "url": "https://www.asiliaafrica.com/kenya/ultimate-kenya-explorer"
        },
    ])

def rank_packages(packages: pd.DataFrame, criteria: str = "cost_per_day") -> pd.DataFrame:
    """Rank packages based on specified criteria."""
    packages["cost_per_day"] = packages["price_usd"] / packages["days"]
    packages["location_count"] = packages["locations"].apply(lambda x: len(x.split(", ")))
    if criteria == "cost_per_day":
        return packages.sort_values("cost_per_day")
    elif criteria == "location_variety":
        return packages.sort_values("location_count", ascending=False)
    return packages

def main():
    st.set_page_config(page_title="KATO Travel Assistant Chatbot", layout="wide")
    st.title("✈️ KATO Travel & Hospitality Chatbot")

    # Load chatbot model
    @st.cache_resource
    def load_model():
        return Client(api_key=GROQ_API_KEY)

    chatbot = load_model()

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{
            "role": "system",
            "content": "You are a professional travel assistant specializing in Kenyan tour packages from KATO Category A and B companies. Use the provided data to recommend the best packages based on price, location, and contents, including links to each package. If a query is unrelated to travel, say: 'I specialize in travel assistance. Let me know how I can help with your trip.'"
        }]

    # Scrape KATO members and load package data
    members = scrape_kato_members()
    packages = get_sample_packages()

    # Display chat history
    for message in st.session_state["messages"]:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # User input
    user_input = st.chat_input("How can I assist you with KATO tour packages?")
    
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Process input and generate response
        if "best package" in user_input.lower() or "recommend" in user_input.lower():
            ranked_packages = rank_packages(packages)
            response = "Here are the top recommended packages from KATO Category A companies:\n\n"
            for i, row in ranked_packages.head(3).iterrows():
                response += (
                    f"**[{row['package']}]({row['url']})** by {row['company']}\n"
                    f"- Price: ${row['price_usd']} for {row['days']} days (${row['cost_per_day']:.2f}/day)\n"
                    f"- Locations: {row['locations']}\n"
                    f"- Includes: {row['contents']}\n\n"
                )
        else:
            response = chatbot.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state["messages"]
            ).choices[0].message.content

        st.session_state["messages"].append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

if __name__ == "__main__":
    main()