import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import extract  # Importing functions from extractor.py

# Page configuration
st.set_page_config(page_title='FlixTubee', page_icon='🎬', layout='wide')

# Custom CSS for styling
def local_css(file_name):
    with open(file_name, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

# Function to prepare recommendation model
def prepare_recommendation_model(data):
    data['combined_features'] = data['title'] + " " + data['category'] + " " + data['summary']
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(data['combined_features'])
    model = NearestNeighbors(n_neighbors=3, metric='cosine')
    model.fit(tfidf_matrix)
    return model, tfidf_vectorizer

# Updated get_recommendations function
def get_recommendations(title, model, tfidf_vectorizer, data, n_recommendations=3):
    try:
        tfidf_matrix = tfidf_vectorizer.transform([title])
        distances, indices = model.kneighbors(tfidf_matrix, n_neighbors=n_recommendations + 1)
        recommended_indices = indices.flatten()[1:]  # Skip the first index as it is the video itself
        recommended_videos = data.iloc[recommended_indices]
        return recommended_videos
    except Exception as e:
        st.error(f"Error in recommendations: {str(e)}")
        return pd.DataFrame()

# Main Streamlit app
def main():
    st.title("FlixAnalytics Video Explorer")

    # Sidebar with navigation and filters
    st.sidebar.header("FlixAnalytics")
    st.sidebar.write("Your go-to analytics platform for exploring and discovering videos.")
    
    # Sidebar filters
    filter_options = ["Python", "Animation", "Football", "Machine Learning", "Fantasy", "Musical", "Other", "Tutorial"]
    selected_filter = st.sidebar.selectbox("Filter by Category", ["All"] + filter_options)

    # Sidebar navigation for sections
    if st.sidebar.button("Overview"):
        st.session_state['section'] = 'overview'
    if st.sidebar.button("Search Videos"):
        st.session_state['section'] = 'search'

    # About FlixAnalytics
    st.sidebar.subheader("About FlixAnalytics")
    st.sidebar.info("FlixAnalytics is a data-driven company specializing in providing analytics and recommendations for various content platforms.")

    # Contact information
    st.sidebar.subheader("Contact Us")
    st.sidebar.write("📧 flixanalytics@yahoo.com")

    
    # Load data
    data = extract.load_data()
    if data.empty:
        st.warning("No videos available in the database.")
        return

    # Apply selected filter to the data
    if selected_filter != "All":
        filtered_data = data[data['category'] == selected_filter]
    else:
        filtered_data = data

    # Default overview page showing all videos with filter applied
    if st.session_state.get('section', 'overview') == 'overview':
        st.subheader("Overview: All Videos")

        if filtered_data.empty:
            st.warning("No videos available for the selected category.")
        else:
            for index, row in filtered_data.iterrows():
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(row['thumbnail'], use_column_width=True)
                with col2:
                    st.subheader(row['title'])
                    st.write(f"**Category:** {row['category']}")
                    st.write(f"**Summary:** {row['summary']}")
                    with st.expander("Watch Video"):
                        st.markdown(
                            f'<iframe width="100%" height="400" src="https://www.youtube.com/embed/{row["video_id"]}" frameborder="0" allowfullscreen></iframe>',
                            unsafe_allow_html=True
                        )
                st.markdown("---")  # Divider between videos

    # Search section
    elif st.session_state.get('section') == 'search':
        st.subheader("Search for Videos")
        video_titles = filtered_data['title'].unique().tolist()
        video_title_input = st.selectbox("Select a video title", [""] + video_titles)
        search_button = st.button("Search")

        if search_button and video_title_input:
            selected_video = filtered_data[filtered_data['title'] == video_title_input].iloc[0]
            st.subheader(f"{selected_video['title']}")
            st.image(selected_video['thumbnail'], use_column_width=True)
            with st.expander("Watch Video"):
                st.markdown(
                    f'<iframe width="100%" height="400" src="https://www.youtube.com/embed/{selected_video["video_id"]}" frameborder="0" allowfullscreen></iframe>',
                    unsafe_allow_html=True
                )
            
            # Display recommendations below the selected video
            st.subheader("You Might Also Like This..")
            model, tfidf_vectorizer = prepare_recommendation_model(data)
            recommended_videos = get_recommendations(video_title_input, model, tfidf_vectorizer, data)
            
            if not recommended_videos.empty:
                for index, row in recommended_videos.iterrows():
                    with st.expander(f"{row['title']}"):
                        st.image(row['thumbnail'], width=200)
                        st.markdown(
                            f'<iframe width="100%" height="400" src="https://www.youtube.com/embed/{row["video_id"]}" frameborder="0" allowfullscreen></iframe>',
                            unsafe_allow_html=True
                        )
            else:
                st.warning("No recommendations found.")

    # # Refresh button to reload data
    # if st.button("Refresh Data"):
    #     st.cache_data.clear()
    #     data = extract.load_data()
    #     st.rerun()

if __name__ == "__main__":
    if 'section' not in st.session_state:
        st.session_state['section'] = 'overview'  # Default to overview section
    main()
