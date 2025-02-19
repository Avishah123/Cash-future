import pandas as pd
from SmartApi import SmartConnect
import pyotp
import streamlit as st
import time

# Initialize API credentials
api_key = 'taADOnb8'
clientId = 'SERT1017'
pwd = '2589'
token = "JAZJT3WVP4JXREBJARRWXQSMRE"

# Generate TOTP
totp = pyotp.TOTP(token).now()

# Connect to the API
obj = SmartConnect(api_key)
data = obj.generateSession(clientId, pwd, totp)
authToken = data['data']['jwtToken']
refreshToken = data['data']['refreshToken']
feed_token = obj.getfeedToken()

# Sample get_ltp_open function
def get_ltp_open(exchange, stocks, tokens):
    try:
        print(f"Fetching LTP for Exchange: {exchange}, Stocks: {stocks}, Tokens: {tokens}")
        response = obj.ltpData(exchange, stocks, tokens)
        print(f"Response: {response}")
        if response and "data" in response and "ltp" in response["data"]:
            return response["data"]["ltp"]
        else:
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


# Function to fetch and update the DataFrame
# @st.cache_data(ttl=10)  
def fetch_data():
    # Load the token data
    df = pd.read_csv('token_data_new.csv', low_memory=False)

    # Filter data
    filtered_df = df[(df['exch_seg'] == 'NFO') & (df['instrumenttype'] == 'FUTSTK')]
    filtered_df2 = df[(df['exch_seg'] == 'NSE')]
    filtered_df3 = filtered_df2[filtered_df2['symbol'].str.endswith('-EQ')]

    merged_df = pd.merge(filtered_df, filtered_df3, on='name', how='inner')
    df = merged_df.head(30)
    print(df)

    print('inside the ltp_x and y')
    # Add LTP columns
    df.loc[:, 'ltp_x'] = df.apply(lambda row: get_ltp_open(row['exch_seg_x'], row['symbol_x'], row['token_x']), axis=1)
    df.loc[:, 'ltp_y'] = df.apply(lambda row: get_ltp_open(row['exch_seg_y'], row['symbol_y'], row['token_y']), axis=1)
    print(df['ltp_x'])
    print('outside the ltp_x and y')
    # Calculate the difference
    df.loc[:, 'ltp_difference'] = df['ltp_x'] - df['ltp_y']

    # Filtered DataFrame
    return df[['symbol_x', 'symbol_y', 'ltp_x', 'ltp_y', 'expiry_x', 'ltp_difference']]

# Streamlit Dashboard
st.title("LTP Dashboard")
st.write("This dashboard displays live LTP data and differences. It refreshes every 10 seconds.")

# Auto-refresh
placeholder = st.empty()

while True:
    with placeholder.container():
        # Fetch the data
        filtered_df = fetch_data()

        # Display the table
        st.subheader("Filtered Data")
        st.dataframe(filtered_df)

        # Add filters for user interaction with unique keys
        symbol_x_filter = st.selectbox(
            "Filter by Symbol X", 
            options=filtered_df['symbol_x'].unique(), 
            key=f"symbol_x_filter_{int(time.time())}"  # Unique key
        )
        filtered_data = filtered_df[filtered_df['symbol_x'] == symbol_x_filter]

        # Display filtered data
        st.subheader(f"Data for {symbol_x_filter}")
        st.dataframe(filtered_data)

    # Wait for 10 seconds before refreshing
    time.sleep(10)
