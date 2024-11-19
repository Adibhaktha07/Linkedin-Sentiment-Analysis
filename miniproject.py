import requests
import json
import os
import time
import pandas as pd
import numpy as np
import streamlit as st
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="LinkedIn Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

def scrapeposts(purl):
    """
    Scrape and analyze LinkedIn posts for the given profile URL
    """
    api_url = "https://fresh-linkedin-profile-data.p.rapidapi.com/get-profile-posts"
    querystring = {"linkedin_url": purl, "type": "posts"}
    headers = {
        "X-RapidAPI-Key": os.getenv("RAPID_API_KEY"),
        "X-RapidAPI-Host": "fresh-linkedin-profile-data.p.rapidapi.com"
    }
    
    try:
        api_res = requests.get(api_url, headers=headers, params=querystring, timeout=30)
        api_res.raise_for_status()
        
        json_data = api_res.json()
        if not json_data.get('data'):
            st.error("No post data found for this profile")
            return
            
        data = json_data['data'][:10]  # Limit to first 10 post URLs

        # Extract data
        post_urls = [item.get('post_url', '') for item in data]
        num_likes = [item.get('num_likes', 0) for item in data]
        num_comments = [item.get('num_comments', 0) for item in data]
        num_reposts = [item.get('num_reposts', 0) for item in data]

        # Display metrics
        st.divider()
        p1, p2, p3 = st.columns(3)
        with p1:
            st.write("Total Likes")
            st.title(f"{sum(num_likes):,}")
            st.divider()
        with p2:
            st.write("Total Impressions")
            total_impressions = sum(num_likes) + sum(num_reposts)
            st.title(f"{total_impressions:,}")
            st.divider()
        with p3:
            st.write("Total Engagements")
            total_engagements = sum(num_likes) + sum(num_comments) + sum(num_reposts)
            st.title(f"{total_engagements:,}")
            st.divider()

        # Create DataFrames
        df = pd.DataFrame({
            'Post URL': post_urls,
            'Number of Likes': num_likes,
            'Number of Comments': num_comments,
            'Number of Reposts': num_reposts,
        })

        # Display visualizations
        st.subheader("Engagement Metrics Over Time")
        
        # Bar charts
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Likes per Post")
            st.bar_chart(data=df, y="Number of Likes")
        with col2:
            st.caption("Comments per Post")
            st.bar_chart(data=df, y="Number of Comments")
        
        # Area chart for overall engagement
        st.subheader("Overall Engagement Trends")
        chart_data = pd.DataFrame({
            "Likes": num_likes,
            "Comments": num_comments,
            "Reposts": num_reposts,
        })
        st.area_chart(chart_data)

        # Display tables and insights
        st.title("Recent Posts Analysis")
        st.dataframe(df, use_container_width=True)
        
        # Most engaging posts
        st.divider()
        st.subheader("Top Performing Posts")
        df_sorted = df.sort_values('Number of Likes', ascending=False)
        st.dataframe(df_sorted, use_container_width=True)
        
        # AI Insights
        st.divider()
        st.title("AI Insights")
        top_post = df_sorted.iloc[0]
        insights = [
            f"📈 Most Engaging Post: {top_post['Post URL']}",
            f"👍 Received {top_post['Number of Likes']:,} likes",
            f"💬 Generated {top_post['Number of Comments']:,} comments",
            f"🔄 Earned {top_post['Number of Reposts']:,} reposts",
            f"📊 Average likes per post: {df['Number of Likes'].mean():.1f}",
            f"💡 Engagement rate: {(total_engagements / len(data)):.1f} interactions per post"
        ]
        
        for insight in insights:
            st.markdown(insight)
            
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch post data: {str(e)}")
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse API response: {str(e)}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")

def analyze_post(post_url):
    """
    Analyze a single LinkedIn post using Cohere API
    """
    # Extract API key from environment variables
    cohere_api_key = os.getenv("COHERE_API_KEY")
    if not cohere_api_key:
        st.error("Cohere API key not found in environment variables")
        return
        
    # Define the Cohere API endpoint
    url = "https://api.cohere.ai/v1/generate"
    
    headers = {
        "Authorization": f"Bearer {cohere_api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # Extract post content (you can replace this step with actual post content scraping or processing)
        payload = {
            "input": post_url,
            "input_type": "article",
            "output_type": "json",
            "steps": [{"skill": "html-extract-article"}],  # Example of extracting article content
        }

        # Making the request to the extraction API (you can replace this step with actual post content extraction logic)
        response = requests.post("https://api.oneai.com/api/v0/pipeline", json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        article_data = response.json()
        
        if not article_data.get('output'):
            st.error("Could not extract post content")
            return
        
        article_text = article_data['output'][0]['contents'][0]['utterance']
        st.success("Successfully extracted post content!")
        
        # Now, analyze this content using Cohere's API
        st.info("Analyzing post content with Cohere...")
        
        cohere_payload = {
            "model": "xlarge",  # You can choose the model based on your needs, for example, 'xlarge' or 'large'
            "prompt": f"Analyze this LinkedIn post and provide insights: {article_text}",
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        # Send the request to Cohere's API for analysis
        cohere_response = requests.post(url, headers=headers, json=cohere_payload, timeout=30)
        cohere_response.raise_for_status()
        
        cohere_data = cohere_response.json()
        
        if "text" in cohere_data:
            analysis = cohere_data["text"]
            st.subheader("AI Analysis")
            st.markdown(analysis)
        else:
            st.error("Invalid response format from Cohere API")
            
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {str(e)}")
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse API response: {str(e)}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")

def competitor_analysis(username, password, comp_un):
    """
    Analyze a competitor's LinkedIn profile
    """
    try:
        options = Options()
        options.headless = True
        furl = f'https://www.linkedin.com/in/{comp_un}?original_referer=https://google.com'
        
        driver = webdriver.Firefox(options=options)
        wait = WebDriverWait(driver, 10)
        
        # Login process
        driver.get('https://www.linkedin.com/login')
        
        username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
        username_input.send_keys(username)
        
        password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
        password_input.send_keys(password)
        
        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        login_button.click()
        
        # Wait and navigate
        time.sleep(3)
        driver.get(furl)
        
        # Extract profile data
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "main")))
        
        profile_data = []
        sections = {
            "About": "section.artdeco-card div.display-flex span",
            "Experience": "section#experience-section li.artdeco-list__item",
            "Education": "section#education-section li.artdeco-list__item",
            "Skills": "section.artdeco-card section.skill-categories-section span"
        }
        
        for section_name, selector in sections.items():
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                section_data = [element.text.strip() for element in elements if element.text.strip()]
                if section_data:
                    profile_data.append(f"\n{section_name}:")
                    profile_data.extend(section_data)
            except Exception as e:
                st.warning(f"Could not extract {section_name} section: {str(e)}")
        
        if not profile_data:
            raise ValueError("No profile data could be extracted")
        
        profile_text = '\n'.join(profile_data)
        st.success("Successfully extracted profile information!")
        
        # AI Analysis
        st.info("Analyzing profile data...")
        
        anyscale_token = os.getenv("ANYSCALE_API_KEY")
        if not anyscale_token:
            st.error("Anyscale API key not found in environment variables")
            return
            
        api_base = "https://api.endpoints.anyscale.com/v1/chat/completions"
        body = {
            "model": "meta-llama/Llama-2-70b-chat-hf",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an AI assistant analyzing LinkedIn profiles. Provide insights about career progression, skills, and professional background. Compare with industry standards and suggest potential opportunities or gaps."
                },
                {
                    "role": "user",
                    "content": f"Analyze this LinkedIn profile data and provide strategic insights:\n\n{profile_text}"
                }
            ],
            "temperature": 0.7,
            "max_tokens": 750
        }
        
        response = requests.post(
            api_base,
            headers={
                "Authorization": f"Bearer {anyscale_token}",
                "Content-Type": "application/json"
            },
            json=body,
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        if "choices" in data and data["choices"] and \
           "message" in data["choices"][0] and \
           "content" in data["choices"][0]["message"]:
            analysis = data["choices"][0]["message"]["content"]
            st.subheader("AI Analysis")
            st.markdown(analysis)
        else:
            st.error("Invalid response format from AI service")
            
    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    finally:
        if 'driver' in locals():
            driver.quit()

# Sidebar navigation
with st.sidebar:
    choose = option_menu(
        "DASHBOARD",
        ["My Profile", "Post Analyzer", "Competitor Analysis"],
        icons=['linkedin', 'file-post', 'kanban'],
        menu_icon="list",
        default_index=0,
        styles={
            "container": {"padding": "5!important"},
            "icon": {"color": "#000", "font-size": "25px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "0px",
                "--hover-color": "#0087FF"
            },
            "nav-link-selected": {"background-color": "#0087FF"},
        }
    )

# Main content area
if choose == "My Profile":
    st.title("LinkedIn Analytics Dashboard")
    st.write("Analyze your LinkedIn profile performance and engagement metrics")
    
    purl = st.text_input("Enter Your LinkedIn Profile URL:", 
                        placeholder="https://www.linkedin.com/in/yourprofile")
    
    if st.button("Analyze Profile"):
        if not purl:
            st.error("Please enter a LinkedIn profile URL")
        else:
            scrapeposts(purl)

elif choose == "Post Analyzer":
    st.title("LinkedIn Post Analyzer")
    st.write("Get detailed insights about any LinkedIn post")
    
    post_url = st.text_input("Enter LinkedIn Post URL:", 
                            placeholder="https://www.linkedin.com/posts/...")
    
    if st.button("Analyze Post"):
        if not post_url:
            st.error("Please enter a LinkedIn post URL")
        else:
            analyze_post(post_url)

elif choose == "Competitor Analysis":
    st.title("Competitor Profile Analysis")
    st.write("Analyze any LinkedIn profile for competitive insights")
    
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("LinkedIn Username:")
        password = st.text_input("LinkedIn Password:", type="password")
    with col2:
        comp_un = st.text_input("Competitor's Profile Username:",
                               placeholder="john-doe")
    
    if st.button("Analyze Competitor"):
        if not all([username, password, comp_un]):
            st.error("Please fill in all required fields")
        else:
            competitor_analysis(username, password, comp_un)

# Footer
st.markdown("""
    <style>
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
    </style>
""", unsafe_allow_html=True)
