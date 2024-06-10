import pandas as pd
import re
import tldextract
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Function to extract HttpUrl from the 'misc' column
def extract_http_url(misc):
    match = re.search(r'HttpUrl=([^ ]+)', misc)
    return match.group(1) if match else None

# Function to extract the primary domain name from a full URL
def extract_primary_domain_name(full_url):
    ext = tldextract.extract(full_url)
    return ext.domain

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

    # Extract primary domain name from the HttpUrl column
    filtered_data['PrimaryDomainName'] = filtered_data['HttpUrl'].apply(extract_primary_domain_name)

    # Sort the filtered data by datetime
    filtered_data = filtered_data.sort_values(by='datetime')

    # Calculate the duration between consecutive URL hits (in seconds)
    filtered_data['time_diff_seconds'] = filtered_data['datetime'].diff().dt.total_seconds().fillna(0)

    # Convert time difference to hours
    filtered_data['time_diff_hours'] = filtered_data['time_diff_seconds'] / 3600  # 3600 seconds in an hour

    # Ensure time_diff is positive by resetting the first row's time_diff to 0
    filtered_data.iloc[0, filtered_data.columns.get_loc('time_diff_seconds')] = 0
    filtered_data.iloc[0, filtered_data.columns.get_loc('time_diff_hours')] = 0

    # Extract relevant columns
    result = filtered_data[['datetime', 'HttpUrl', 'PrimaryDomainName', 'time_diff_seconds', 'time_diff_hours']]

    # Calculate total time spent on primary domain names (in seconds and hours)
    domain_time_spent = result.groupby('PrimaryDomainName').agg(
        total_time_spent_seconds=('time_diff_seconds', 'sum'),
        total_time_spent_hours=('time_diff_hours', 'sum')
    ).reset_index()

    # Get the top 5 most used primary domain names
    top_domains = domain_time_spent.nlargest(5, 'total_time_spent_seconds')
    return result, domain_time_spent, top_domains

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
            filtered_urls, domain_time_spent, top_domains = calculate_time_spent_on_urls(data, session_id)

            # Display total time spent on each primary domain name
            st.subheader(f'Total Time Spent on Primary Domain Names in Session {session_id}')
            st.dataframe(domain_time_spent.head().style.format({'total_time_spent_seconds': '{:.2f} seconds', 
                                                         'total_time_spent_hours': '{:.2f} hours'}))

            # Display top 5 most used primary domain names
            st.subheader(f'Top 5 Most Used Primary Domain Names in Session {session_id}')
            st.dataframe(top_domains.style.format({'total_time_spent_seconds': '{:.2f} seconds', 
                                                   'total_time_spent_hours': '{:.2f} hours'}))

            # Plotting total time spent on each primary domain
            st.subheader('Time Spent on Each Primary Domain')
            plt.figure(figsize=(10, 5))
            sns.barplot(data=top_domains, x='PrimaryDomainName', y='total_time_spent_hours', palette='viridis')
            plt.xlabel('Primary Domain Name')
            plt.ylabel('Total Time Spent (hours)')
            plt.title(f'Total Time Spent on Each Primary Domain in Session {session_id}')
            st.pyplot(plt.gcf())

            # Plotting the time differences over time
            st.subheader('Time Spent on Each URL (Chronological)')
            plt.figure(figsize=(10, 5))
            plt.plot(filtered_urls['datetime'], filtered_urls['time_diff_hours'], marker='o')
            plt.xlabel('Time')
            plt.ylabel('Time Spent (hours)')
            plt.title(f'Time Spent on Each URL in Session {session_id}')
            st.pyplot(plt.gcf())
    else:
        st.error('The uploaded file does not contain a "session_id" column.')
else:
    st.info('Please upload a CSV file to proceed.')
