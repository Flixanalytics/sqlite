import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import extract  # Importing functions from extractor.py

# Page configuration
st.set_page_config(page_title='FLIXtube Movies', page_icon='🎬', layout='wide')

# CSS for custom styling
def local_css(file_name):
    with open(file_name, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

# Function to prepare recommendation model
def prepare_recommendation_model(data):
    data['combined_features'] = data['title'] + " " + data['category'] + " " + data['genre'] + " " + data['summary']
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(data['combined_features'])
    model = NearestNeighbors(n_neighbors=3, metric='cosine')
    model.fit(tfidf_matrix)
    return model, tfidf_vectorizer

# Function to get recommendations based on video details
def get_recommendations(video, model, vectorizer, data, n_recommendations=3):
    combined_features = video['title'] + " " + video['category'] + " "  + " " + video['summary']
    tfidf_matrix = vectorizer.transform([combined_features])
    distances, indices = model.kneighbors(tfidf_matrix, n_neighbors=n_recommendations + 1)
    recommended_indices = indices.flatten()[1:]  # Skip the first index since it's the video itself
    return data.iloc[recommended_indices]

# Main Streamlit app
def main():
    st.title("🎬 Welcome to FLIXtube Videos")
    st.subheader("Explore, Watch, and Discover Recommended Videos!")

    # Load all videos from the database
    data = extract.load_data()
    if data.empty:
        st.warning("No videos available in the database.")
        return

    # Sidebar for filters
    st.sidebar.header("Filter Movies")
    selected_category = st.sidebar.radio("Select Category", ["All"] + sorted(data['category'].unique().tolist()))
    
    # Filter based on sidebar selection
    filtered_data = data.copy()
    if selected_category != "All":
        filtered_data = filtered_data[filtered_data['category'] == selected_category]
    
    # Search section using a select box
    video_titles = filtered_data['title'].unique().tolist()
    selected_title = st.selectbox("Select a movie title to search", [""] + video_titles)
    search_button = st.button("Search")

    # Display filtered data
    st.subheader("Available Movies")
    if filtered_data.empty:
        st.warning("No movies available for the selected filters.")
    else:
        for index, row in filtered_data.iterrows():
            st.markdown(f"### {row['title']}")
            st.image(row['thumbnail'], use_column_width=True)
            # Create an expander for video playback
            with st.expander("Watch Video", expanded=False):
                st.markdown(
                    f'<iframe width="100%" height="400" src="https://www.youtube.com/embed/{row["video_id"]}" frameborder="0" allowfullscreen></iframe>',
                    unsafe_allow_html=True
                )
            st.write(f"**Category:** {row['category']}")
            
            st.write(f"**Summary:** {row['summary']}")
            st.write("---")  # Divider for better readability

    # Check if the search button was clicked
    if search_button:
        if selected_title:
            searched_video = filtered_data[filtered_data['title'] == selected_title]
            
            if not searched_video.empty:
                st.subheader("Selected Video")
                display_video_with_recommendations(searched_video.iloc[0], data)
            else:
                st.warning("No results found for the selected title.")
        else:
            st.warning("Please select a movie title before searching.")

# Function to display video and recommendations
def display_video_with_recommendations(video, data):
    # Use an expander to show the selected video
    with st.expander(f"Watch {video['title']}", expanded=True):
        st.image(video['thumbnail'], use_column_width=True)
        # Display the video using an iframe
        st.markdown(
            f'<iframe width="100%" height="400" src="https://www.youtube.com/embed/{video["video_id"]}" frameborder="0" allowfullscreen></iframe>',
            unsafe_allow_html=True
        )
        # Display video details
        st.write(f"**Category:** {video['category']}")
        
        st.write(f"**Summary:** {video['summary']}")

    # Prepare and display recommendations for this video
    st.subheader("Recommended Movies")
    model, vectorizer = prepare_recommendation_model(data)
    recommendations = get_recommendations(video, model, vectorizer, data)

    # Show recommendations only for the searched video
    with st.expander("You Might Also Like", expanded=True):
        for _, rec in recommendations.iterrows():
            st.markdown(f"**{rec['title']}**")
            st.image(rec['thumbnail'], width=150)
            st.markdown(
                f'<iframe width="100%" height="200" src="https://www.youtube.com/embed/{rec["video_id"]}" frameborder="0" allowfullscreen></iframe>',
                unsafe_allow_html=True
            )

# Run the app
if __name__ == "__main__":
    main()
