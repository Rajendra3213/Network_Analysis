import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# Set up the Streamlit app with a title and a description
st.set_page_config(page_title="Network Traffic Analysis", layout="wide")
st.title("Network Traffic Analysis Dashboard")
st.markdown("""
This dashboard provides insights into network traffic by analyzing various parameters such as protocols, IP addresses, packet sizes, connection durations, HTTP methods, and URLs.
""")

# File uploader for log.csv
st.sidebar.header("Upload log.csv")
uploaded_file = st.sidebar.file_uploader("Choose a file", type=['csv'])

if uploaded_file is not None:
    # Load the data
    df = pd.read_csv(uploaded_file, 
                     names=["date", "time", "session_id", "session_id_2", "connection_id_1", "connection_id_2", 
                            "protocol_hex", "packet_size", "protocol", "tcp_flags", "src_ip", "src_port", "dst_ip", 
                            "dst_port", "sequence_number", "ack_number", "window_size", "http_method", "http_url", 
                            "http_protocol", "unknown_1", "unknown_2", "unknown_3", "unknown_4"], 
                     skiprows=1)

    # Clean column names to remove any leading/trailing whitespace
    df.columns = df.columns.str.strip()

    # Display the data to ensure it's loaded correctly
    st.write("Data Preview:", df.head())

    # Convert 'date' and 'time' columns to datetime
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='%Y-%m-%d %H:%M:%S.%f')

    # Ensure that 'session_id' is treated as a string to avoid any numeric parsing issues
    df['session_id'] = df['session_id'].astype(str)

    # Calculate connection duration in seconds
    df['duration'] = df.groupby('session_id')['datetime'].transform(lambda x: (x.max() - x.min()).total_seconds())

    # Sidebar filters
    st.sidebar.header("Filters")
    protocols = st.sidebar.multiselect("Select Protocols", options=df['protocol'].unique(), default=df['protocol'].unique())
    start_date = st.sidebar.date_input("Start Date", df['datetime'].min().date())
    end_date = st.sidebar.date_input("End Date", df['datetime'].max().date())

    # Filter data based on sidebar inputs
    filtered_df = df[(df['protocol'].isin(protocols)) & (df['datetime'].dt.date >= start_date) & (df['datetime'].dt.date <= end_date)]

    # Check if the filtered DataFrame is empty
    if filtered_df.empty:
        st.warning("No data available for the selected date range. Please adjust the filters.")
    else:
        # 1. Protocol Distribution
        st.header("Protocol Distribution")
        protocol_counts = filtered_df['protocol'].value_counts(normalize=True)
        st.dataframe(protocol_counts)

        # Protocol Insights
        most_common_protocol = protocol_counts.idxmax()
        least_common_protocol = protocol_counts.idxmin()
        st.write(f"The most common protocol is {most_common_protocol} with a frequency of {protocol_counts.max():.2%}.")
        st.write(f"The least common protocol is {least_common_protocol} with a frequency of {protocol_counts.min():.2%}.")

        # 2. Top Source and Destination IPs
        col1, col2 = st.columns(2)

        with col1:
            st.header("Top Source IPs")
            top_source_ips = filtered_df['src_ip'].value_counts().head(5)
            st.dataframe(top_source_ips)
            most_common_src_ip = top_source_ips.idxmax()
            st.write(f"The most frequent source IP is {most_common_src_ip} with {top_source_ips.max()} occurrences.")

        with col2:
            st.header("Top Destination IPs")
            top_dest_ips = filtered_df['dst_ip'].value_counts().head(5)
            st.dataframe(top_dest_ips)
            most_common_dst_ip = top_dest_ips.idxmax()
            st.write(f"The most frequent destination IP is {most_common_dst_ip} with {top_dest_ips.max()} occurrences.")

        # 3. Packet Size Distribution
        st.header("Packet Size Distribution by Protocol")
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.boxplot(x='protocol', y='packet_size', data=filtered_df, ax=ax, palette="Set2")
        ax.set_title('Packet Size Distribution by Protocol', fontsize=16)
        ax.set_xlabel('Protocol', fontsize=14)
        ax.set_ylabel('Packet Size', fontsize=14)
        st.pyplot(fig)

        # Packet Size Insights
        packet_size_stats = filtered_df['packet_size'].describe()
        st.write("Packet Size Statistics:")
        st.write(packet_size_stats)

        # 4. Connection Duration
        st.header("Connection Duration Distribution")
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.histplot(filtered_df['duration'], bins=50, kde=True, ax=ax, color="skyblue")
        ax.set_title('Connection Duration Distribution', fontsize=16)
        ax.set_xlabel('Duration (seconds)', fontsize=14)
        ax.set_ylabel('Frequency', fontsize=14)
        st.pyplot(fig)

        # Connection Duration Insights
        duration_stats = filtered_df['duration'].describe()
        st.write("Connection Duration Statistics:")
        st.write(duration_stats)

        # 5. Traffic Patterns Over Time
        st.header("Traffic Patterns Over Time")
        fig, ax = plt.subplots(figsize=(12, 6))
        filtered_df.set_index('datetime').resample('1Min').size().plot(ax=ax, color="purple")
        ax.set_title('Traffic Patterns Over Time', fontsize=16)
        ax.set_xlabel('Time', fontsize=14)
        ax.set_ylabel('Number of Connections', fontsize=14)
        ax.grid(True)
        st.pyplot(fig)

        # 6. HTTP Methods and URLs
        st.header("HTTP Methods and URLs")
        col3, col4 = st.columns(2)

        with col3:
            st.subheader("Top HTTP Methods")
            top_http_methods = filtered_df['http_method'].value_counts().head(5)
            st.dataframe(top_http_methods)
            most_common_http_method = top_http_methods.idxmax()
            st.write(f"The most common HTTP method is {most_common_http_method} with {top_http_methods.max()} occurrences.")

        with col4:
            st.subheader("Top HTTP URLs")
            top_http_urls = filtered_df['http_url'].value_counts().head(5)
            st.dataframe(top_http_urls)
            most_common_http_url = top_http_urls.idxmax()
            st.write(f"The most common HTTP URL is {most_common_http_url} with {top_http_urls.max()} occurrences.")

# Footer
st.markdown("""
---
**Developed by:** Rajendra Acharya
""")
