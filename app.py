import streamlit as st
import pandas as pd
import re
from io import BytesIO
import yfinance as yf
from datetime import datetime, timedelta

# Function to parse the sentiment file
def parse_sentiment_file(file):
    lines = file.readlines()
    data = []
    current_date = None
    
    for line in lines:
        line = line.decode('utf-8').strip()
        
        if re.match(r'\d+/\d+/\d+', line):  # Match dates
            current_date = line
        elif "Bullish:" in line:
            bullish_data = re.search(r'Bullish: (\d+) \((\d+)%\)', line)
            if bullish_data:
                bullish = int(bullish_data.group(1))
                bullish_percent = int(bullish_data.group(2))
        elif "Bearish:" in line:
            bearish_data = re.search(r'Bearish: (\d+) \((\d+)%\)', line)
            if bearish_data:
                bearish = int(bearish_data.group(1))
                bearish_percent = int(bearish_data.group(2))
                
                data.append({
                    "Date": current_date,
                    "Bullish": bullish,
                    "Bearish": bearish,
                    "Bullish (%)": bullish_percent,
                    "Bearish (%)": bearish_percent
                })
    
    df = pd.DataFrame(data)
    return df

# Function to parse text area input
def parse_text_input(text):
    lines = text.strip().split("\n")
    data = []
    current_date = None
    
    for line in lines:
        line = line.strip()
        
        if re.match(r'\d+/\d+/\d+', line):  # Match dates
            current_date = line
        elif "Bullish:" in line:
            bullish_data = re.search(r'Bullish: (\d+) \((\d+)%\)', line)
            if bullish_data:
                bullish = int(bullish_data.group(1))
                bullish_percent = int(bullish_data.group(2))
        elif "Bearish:" in line:
            bearish_data = re.search(r'Bearish: (\d+) \((\d+)%\)', line)
            if bearish_data:
                bearish = int(bearish_data.group(1))
                bearish_percent = int(bearish_data.group(2))
                
                data.append({
                    "Date": current_date,
                    "Bullish": bullish,
                    "Bearish": bearish,
                    "Bullish (%)": bullish_percent,
                    "Bearish (%)": bearish_percent
                })
    
    df = pd.DataFrame(data)
    return df

# Function to fetch VIX closing value for a given date
def get_vix_value(date):
    vix = yf.Ticker("^VIX")
    start_date = datetime.strptime(date, '%m/%d/%y').strftime('%Y-%m-%d')
    end_date = (datetime.strptime(date, '%m/%d/%y') + timedelta(days=1)).strftime('%Y-%m-%d')
    vix_data = vix.history(start=start_date, end=end_date)
    if not vix_data.empty:
        return vix_data['Close'][0]
    else:
        return None

# Function to fetch SPY next day returns
def get_spy_next_day_return(date):
    spy = yf.Ticker("SPY")
    current_date = datetime.strptime(date, '%m/%d/%y')
    start_date = current_date.strftime('%Y-%m-%d')
    end_date = (current_date + timedelta(days=2)).strftime('%Y-%m-%d')  # Include an extra day to ensure we get the next day's closing price
    spy_data = spy.history(start=start_date, end=end_date)
    if len(spy_data) >= 2:
        current_close = spy_data['Close'][0]
        next_close = spy_data['Close'][1]
        next_day_return = ((next_close - current_close) / current_close) * 100
        return next_day_return
    else:
        return None

# Streamlit App
st.title("Sentiment Data Parser")

# File upload section
uploaded_file = st.file_uploader("Upload your sentiment file", type="txt")

# Sidebar for manual input
st.sidebar.subheader("Enter the sentiment data manually")
date = st.sidebar.text_input("Date (MM/DD/YY)", "")
bullish = st.sidebar.number_input("Bullish Count", min_value=0, step=1)
bullish_percent = st.sidebar.number_input("Bullish (%)", min_value=0, max_value=100, step=1)
bearish = st.sidebar.number_input("Bearish Count", min_value=0, step=1)
bearish_percent = st.sidebar.number_input("Bearish (%)", min_value=0, max_value=100, step=1)

# Button to add manually entered data to the DataFrame
if st.sidebar.button("Add Data"):
    if date and bullish and bearish:
        new_data = {
            "Date": date,
            "Bullish": bullish,
            "Bearish": bearish,
            "Bullish (%)": bullish_percent,
            "Bearish (%)": bearish_percent
        }
        if 'manual_data' not in st.session_state:
            st.session_state.manual_data = []
        st.session_state.manual_data.append(new_data)
        st.sidebar.success("Data added successfully")
    else:
        st.sidebar.error("Please fill in all the fields")

# Text area for entering data in a specific format
st.subheader("Or enter the sentiment data in text format")
text_input = st.text_area("Enter data:", height=200)

if st.button("Parse Text Input"):
    if text_input:
        text_df = parse_text_input(text_input)
        if 'text_data' not in st.session_state:
            st.session_state.text_data = text_df
        else:
            st.session_state.text_data = pd.concat([st.session_state.text_data, text_df], ignore_index=True)
        st.success("Text data parsed successfully")
    else:
        st.error("Please enter some data in the text area")

# Create DataFrame from manual input
if 'manual_data' in st.session_state:
    manual_df = pd.DataFrame(st.session_state.manual_data)
else:
    manual_df = pd.DataFrame(columns=["Date", "Bullish", "Bearish", "Bullish (%)", "Bearish (%)"])

# Combine data from file, manual input, and text input
if uploaded_file is not None:
    file_df = parse_sentiment_file(uploaded_file)
    combined_df = pd.concat([file_df, manual_df], ignore_index=True)
else:
    combined_df = manual_df

if 'text_data' in st.session_state:
    combined_df = pd.concat([combined_df, st.session_state.text_data], ignore_index=True)

# Fetch VIX data for each date and add it to the DataFrame
if not combined_df.empty:
    combined_df['VIX'] = combined_df['Date'].apply(lambda x: get_vix_value(x))
    combined_df['SPY Next Day Return (%)'] = combined_df['Date'].apply(lambda x: get_spy_next_day_return(x))
    st.write("Combined Data with VIX and SPY Next Day Returns:")
    st.dataframe(combined_df)
else:
    st.write("No data available.")

# Allow the user to download the combined data as an Excel file
if not combined_df.empty:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        combined_df.to_excel(writer, index=False, sheet_name='Sentiment Data')
        writer.close()
    
    st.download_button(
        label="Download Excel file",
        data=output.getvalue(),
        file_name="sentiment_data_with_vix_spy.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
