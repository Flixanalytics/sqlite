
# extractor.py
import sqlite3
import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st

# Initialize the SQLite database and create the videos table if it doesn't exist
def init_db():
    conn = sqlite3.connect('flixtube.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id TEXT NOT NULL UNIQUE,
        title TEXT,
        thumbnail TEXT,
        category TEXT,
        genre TEXT,
        summary TEXT
    )''')
    conn.commit()
    conn.close()

# Function to connect to the SQLite database
def get_db():
    conn = sqlite3.connect('flixtube.db')
    conn.row_factory = sqlite3.Row
    return conn

# Function to retrieve video title and thumbnail from YouTube
def get_video_data(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    response = requests.get(url)
    if response.status_code != 200:
        return "Title not found", ""
    
    soup = BeautifulSoup(response.text, 'html.parser')
    title_tag = soup.find('meta', {'name': 'title'})
    title = title_tag['content'] if title_tag else "Title not found"
    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/0.jpg"
    return title, thumbnail_url

# Function to add new video data to the SQLite database
def update_dataset(video_id, category, genre, summary):
    conn = get_db()
    # Check if the video ID already exists
    existing_ids = set(row['video_id'] for row in conn.execute('SELECT video_id FROM videos').fetchall())
    
    if video_id not in existing_ids:
        title, thumbnail_url = get_video_data(video_id)
        conn.execute('''
            INSERT INTO videos (video_id, title, thumbnail, category, genre, summary) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (video_id, title, thumbnail_url, category, genre, summary))
        conn.commit()
        conn.close()
        return f"Video '{title}' added successfully!"
    else:
        conn.close()
        return f"Video ID '{video_id}' already exists in the dataset."

# Function to load data from the SQLite database
def load_data():
    conn = get_db()
    data = pd.read_sql_query("SELECT * FROM videos", conn)
    conn.close()
    return data

# Run database initialization on import
init_db()

# Streamlit UI for adding video data
def main():
    st.title("YouTube Video Data Entry")

    # Video ID input
    video_id = st.text_input("Enter YouTube Video ID or URL")
    
    # Category select box
    category = st.selectbox(
        "Select Category",
        options=["Action", "Comedy", "Drama", "Horror", "Documentary", "Sci-Fi", "Other"]
    )
    
    # Genre select box
    genre = st.selectbox(
        "Select Genre",
        options=["Adventure", "Animation", "Biography", "Crime", "Fantasy", "Musical", "Mystery", "Romance", "Thriller", "Other"]
    )
    
    # Summary input
    summary = st.text_area("Enter a brief summary of the video")

    # Button to add video data
    if st.button("Add Video Data"):
        if video_id and category and genre and summary:
            # Extract video ID from full YouTube URL or direct ID input
            video_id = video_id.split('v=')[-1].split('&')[0] if 'v=' in video_id else video_id.split('youtu.be/')[-1].split('?')[0]
            
            # Add video to the database
            result = update_dataset(video_id, category, genre, summary)
            st.success(result)
        else:
            st.warning("Please fill out all fields.")

    # Display current dataset
    st.subheader("Current Dataset")
    data = load_data()
    if not data.empty:
        st.dataframe(data)
    else:
        st.info("No data available in the database.")

# Run Streamlit app if the script is executed directly
if __name__ == "__main__":
    main()
