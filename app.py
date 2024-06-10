import pandas as pd
import streamlit as st
import re

# Function to extract HttpUrl from the 'misc' column
def extract_http_url(misc):
    match = re.search(r'HttpUrl=([^ ]+)', misc)
    return match.group(1) if match else None

# Function to filter URLs by session ID and calculate the time spent on URLs
def calculate_time_spent_on_urls(data, session_id):
    # Strip any leading/trailing spaces from the column names
    data.columns = data.columns.str.strip()

    # Convert date and time columns to a single datetime column
    data['datetime'] = pd.to_datetime(data['date'] + ' ' + data['time'])

    # Filter the DataFrame by session ID
    filtered_data = data[data['session_id'] == session_id]

    # Extract HttpUrl from 'misc' column
    filtered_data['HttpUrl'] = filtered_data['misc'].apply(extract_http_url)

    # Drop rows where HttpUrl is None
    filtered_data = filtered_data.dropna(subset=['HttpUrl'])

    # Sort the filtered data by datetime
    filtered_data = filtered_data.sort_values(by='datetime')

    # Calculate the duration between consecutive URL hits
    filtered_data['time_diff'] = filtered_data['datetime'].diff().dt.total_seconds().fillna(0)

    # Ensure time_diff is positive by resetting the first row's time_diff to 0
    filtered_data.iloc[0, filtered_data.columns.get_loc('time_diff')] = 0

    # Extract relevant columns
    result = filtered_data[['datetime', 'HttpUrl', 'time_diff']]

    # Calculate total time spent on URLs
    url_time_spent = result.groupby('HttpUrl')['time_diff'].sum().reset_index()
    url_time_spent = url_time_spent.rename(columns={'time_diff': 'total_time_spent'})

    # Get the top 4 most used URLs
    top_urls = url_time_spent.nlargest(4, 'total_time_spent')

    return result, url_time_spent, top_urls

# Streamlit app
st.title('URL Hit Duration per Session')

# Upload CSV file
uploaded_file = st.file_uploader('Choose a CSV file', type='csv')

if uploaded_file is not None:
    # Read the CSV data into a DataFrame
    data = pd.read_csv(uploaded_file)

    if 'session_id' in data.columns:
        # Select session ID
        session_id = st.selectbox('Select Session ID', data['session_id'].unique())

        if session_id:
            # Calculate time spent on URLs for the selected session
            filtered_urls, url_time_spent, top_urls = calculate_time_spent_on_urls(data, session_id)

            # Display total time spent on each URL
            st.subheader(f'Total Time Spent on URLs in Session {session_id}')
            st.dataframe(url_time_spent.style.format({'total_time_spent': '{:.2f} seconds'}))

            # Display top 4 most used URLs
            st.subheader(f'Top 4 Most Used URLs in Session {session_id}')
            st.dataframe(top_urls.style.format({'total_time_spent': '{:.2f} seconds'}))

            # Visualize the time differences
            st.subheader('Time Spent on Each URL (Chronological)')
            st.line_chart(filtered_urls.set_index('datetime')['time_diff'])
    else:
        st.error('The uploaded file does not contain a "session_id" column.')
else:
    st.info('Please upload a CSV file to proceed.')
