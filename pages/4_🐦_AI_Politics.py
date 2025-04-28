import streamlit as st
import requests
import pandas as pd
import datetime
import os
import base64
import json
from utils.lottie_utils import load_lottieurl, display_lottie_animation
from utils.local_storage import save_key, get_key

# Page configuration
st.set_page_config(
    page_title="Verborum - AI & Politics Tweets",
    page_icon="🐦",
    layout="wide"
)

# Added Coming Soon placeholder
st.title("🐦 AI & Politics – Coming Soon")
st.info("This page is under construction. Please check back soon!")
st.stop()

def get_bearer_token():
    """
    Generate a Bearer Token from API Key and Secret
    
    Returns:
        str: Bearer Token or None if keys are missing
    """
    # Check if we already have a bearer token directly saved
    bearer_token = get_key("twitter_bearer_token")
    if bearer_token:
        return bearer_token
    
    # Otherwise try to generate from API key and secret
    api_key = get_key("twitter_api_key")
    api_secret = get_key("twitter_api_secret")
    
    if not api_key or not api_secret:
        return None
    
    try:
        # Encode API Key and Secret for Bearer Token authentication
        credentials = f"{api_key}:{api_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        # Request Bearer Token from Twitter
        url = "https://api.twitter.com/oauth2/token"
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        }
        data = "grant_type=client_credentials"
        
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        
        token = response.json()["access_token"]
        # Save the bearer token for future use
        save_key("twitter_bearer_token", token)
        return token
    except Exception as e:
        st.error(f"Error getting Bearer Token: {str(e)}")
        return None

# Cache Twitter API results for 15 minutes (900 seconds)
@st.cache_data(ttl=900)
def fetch_tweets():
    """
    Fetch the latest 30 tweets about AI and politics in Italian or English,
    excluding retweets and replies.
    
    Returns:
        pandas.DataFrame: DataFrame with tweet data or None if API call fails
    """
    # Get bearer token from API Key and Secret
    bearer_token = get_bearer_token()
    
    if not bearer_token:
        st.error("Unable to generate Bearer Token. Please check your API Key and Secret in the sidebar.")
        return None
        
    headers = {"Authorization": f"Bearer {bearer_token}"}
    
    # Fixed search query - simplified and using proper Twitter API syntax
    # Use parentheses to properly group terms and operators
    query = '(AI OR "artificial intelligence" OR IA) (politics OR politica) -is:retweet -is:reply (lang:en OR lang:it)'
    
    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": query,
        "max_results": 30,
        "tweet.fields": "created_at,author_id",
        "user.fields": "username,verified",
        "expansions": "author_id",
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        # More detailed error handling for debugging
        if response.status_code != 200:
            error_detail = "Unknown error"
            try:
                error_json = response.json()
                error_detail = json.dumps(error_json, indent=2)
            except:
                error_detail = response.text
                
            st.error(f"Twitter API Error {response.status_code}:\n{error_detail}")
            return None
        
        data = response.json()
        
        # Handle case where no tweets match the search criteria
        if "data" not in data:
            st.info("No tweets found matching the search criteria.")
            return pd.DataFrame()
        return pd.DataFrame(tweets)
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching tweets: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error processing tweets: {str(e)}")
        return None

# Page title
st.title("🐦 AI & Politics – Latest Tweets")

# Sidebar with API key input and animation
with st.sidebar:
    # Twitter Lottie animation
    twitter_animation = load_lottieurl("https://lottie.host/7714e6eb-4696-49e1-9a9b-bc557d991b7c/99PVBMRdTY.json")
    display_lottie_animation(twitter_animation, height=120, key="twitter_anim")
    
    # Creator info (following app pattern)
    st.markdown("### Created by [Paulo Giavoni](https://www.linkedin.com/in/paulogiavoni/)")
    
    # Twitter API Key input form (matching style from Home.py)
    with st.expander("API Keys", expanded=True):
        with st.form("twitter_api_key_form"):
            st.caption("Enter your Twitter API credentials")
            
            api_key = st.text_input("API Key", type="password", 
                                   value=get_key("twitter_api_key") or "")
            
            api_secret = st.text_input("API Key Secret", type="password", 
                                     value=get_key("twitter_api_secret") or "")
            
            submitted = st.form_submit_button("Save Keys")
            
            if submitted:
                if api_key and api_secret:
                    save_key("twitter_api_key", api_key)
                    save_key("twitter_api_secret", api_secret)
                    st.success("Twitter API credentials saved!")
                    # Clear cache to force new token generation
                    st.cache_data.clear()
                    st.rerun()
    
    # Information about the Twitter API
    with st.expander("About Twitter API Usage"):
        st.markdown("""
        This page uses the Twitter API v2 Recent Search endpoint to fetch tweets about:
        
        - AI/Artificial Intelligence
        - Politics
        
        Results are limited to Italian or English and exclude retweets and replies.
        
        Data is cached for 15 minutes to respect the Twitter API rate limits.
        """)

# Get tweets
last_refresh = datetime.datetime.now()
tweets_df = fetch_tweets()

# Display timestamp of when data was last refreshed
st.caption(f"Data last refreshed: {last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

# Display tweets
if tweets_df is not None and not tweets_df.empty:
    # Show tweets in a responsive table
    st.dataframe(tweets_df, use_container_width=True, hide_index=True)
else:
    st.warning("No tweets found or API error occurred. Check the sidebar to make sure your API credentials are correct.")

# Refresh button
if st.button("Refresh now"):
    st.cache_data.clear()
    st.rerun()

# Page footer
st.divider()
st.caption("Verborum AI & Politics Twitter Feed • Powered by Twitter API v2")