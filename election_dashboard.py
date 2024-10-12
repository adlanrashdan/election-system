import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Function to load data from the first Google Sheet with caching to avoid frequent access
@st.cache_data(ttl=1800)
def load_data_from_sheet1(sheet_url):
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url).sheet1
    all_values = sheet.get_all_values()

    title1 = extract_title(all_values[1:2])
    title2 = extract_title(all_values[5:6])
    title3 = extract_title(all_values[9:10])
    title4 = extract_title(all_values[14:15])
    title5 = extract_title(all_values[19:20])

    table1 = clean_and_filter_data(all_values[2:4])
    table2 = clean_and_filter_data(all_values[6:8])
    table3 = clean_and_filter_data(all_values[10:13])
    table4 = clean_and_filter_data(all_values[15:18])
    table5 = clean_and_filter_data(all_values[20:43])

    return (title1, title2, title3, title4, title5), (table1, table2, table3, table4, table5)

# Function to extract title from a specific range
def extract_title(raw_values):
    return " ".join([cell.strip() for cell in raw_values[0] if isinstance(cell, str) and cell.strip()])

# Function to clean and filter data to include only text cells and set headers properly
def clean_and_filter_data(raw_values):
    filtered_rows = [row for row in raw_values if any(isinstance(cell, str) and cell.strip() for cell in row)]
    if len(filtered_rows) < 2:
        return pd.DataFrame()

    header = [cell.strip() if isinstance(cell, str) and cell.strip() else f"Unnamed_{index}" for index, cell in enumerate(filtered_rows[0])]
    filtered_data = []
    for row in filtered_rows[1:]:
        cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]
        if any(cell for cell in cleaned_row):
            filtered_data.append(cleaned_row)

    data = pd.DataFrame(filtered_data, columns=header)
    data = data.loc[:, ~data.columns.str.contains('^Unnamed')]
    data = data.dropna(axis=1, how='all')
    return data

# Function to sort and limit rows based on 'JUMLAH UNDI' column and add 'KEDUDUKAN' column
def sort_and_limit_rows(data, num_rows=15):
    if not data.empty and len(data) > 1:
        try:
            data['JUMLAH_UNDI_NUMERIC'] = pd.to_numeric(data[data.columns[-1]], errors='coerce')
            sorted_data = data.sort_values(by='JUMLAH_UNDI_NUMERIC', ascending=False, na_position='last').reset_index(drop=True)
            sorted_data['KEDUDUKAN'] = sorted_data['JUMLAH_UNDI_NUMERIC'].rank(method='min', ascending=False).astype('Int64')
        except Exception as e:
            print(f"Error in sorting by numeric values: {e}")
        sorted_data = sorted_data.drop(columns=['JUMLAH_UNDI_NUMERIC'])
    else:
        sorted_data = data

    return sorted_data, sorted_data if len(sorted_data) <= num_rows else sorted_data.iloc[:num_rows]

# Function to highlight rows below the first 8 (for second section)
def highlight_rows_below_8(data, show_all):
    styles = pd.DataFrame('', index=data.index, columns=data.columns)
    if len(data) > 8:
        styles.iloc[8:] = 'background-color: #FFCCCB; color: black; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); font-weight: bold;'  
    return styles

# Function to highlight rows below the first 15 (for first section)
def highlight_rows_below_15(data, show_all):
    styles = pd.DataFrame('', index=data.index, columns=data.columns)
    if len(data) > 15:
        styles.iloc[15:] = 'background-color: #FFCCCB; color: black; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); font-weight: bold;'  
    return styles

# Google Sheet URL
sheet_url1 = 'https://docs.google.com/spreadsheets/d/1okLq9jinvR8O_P8I2eqTkaI73adQnbH9zOxpu2u4h48/edit?usp=sharing'
sheet_url_tabs = 'https://docs.google.com/spreadsheets/d/1VdMWSI-c4zv0o8uuKkhDPLrVHtw6c3kg8RjnORbKRJo/edit?usp=sharing'

bahagian_tabs = ['PUCHONG', 'KOTA RAJA', 'SUNGAI BESAR', 'RASAH', 'SEREMBAN']

if 'data_loaded_sheet1' not in st.session_state:
    st.session_state.data_loaded_sheet1 = False

if not st.session_state.data_loaded_sheet1:
    st.session_state.titles_sheet1, st.session_state.tables_sheet1 = load_data_from_sheet1(sheet_url1)
    st.session_state.data_loaded_sheet1 = True

# Define the main page structure and styling with improved table visibility
st.markdown("""
    <style>
        .main-header {
            font-size: 40px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 20px;
            color: #000000;
        }
        .sub-header {
            font-size: 30px;
            text-align: center;
            margin-bottom: 30px;
            color: #8B0000;
        }
        .table-title {
            font-size: 26px;
            font-weight: bold;
            color: #8B0000;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .stDataFrame table {
            border-collapse: collapse;
            width: 100%;
            border: 3px solid #b0bec5;
        }
        .stDataFrame th {
            background-color: #1e88e5;
            color: #ffffff;
            font-size: 22px;
            padding: 12px;
            font-weight: bold;
        }
        .stDataFrame td {
            border: 2px solid #90a4ae;
            padding: 15px;
            font-size: 20px;
            font-weight: normal;
        }
        .stDataFrame tbody tr:nth-child(even) {
            background-color: #e3f2fd;
        }
        .stDataFrame tbody tr:hover {
            background-color: #bbdefb;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-header'>KEPUTUSAN PENUH PEMILIHAN SAYAP BERSEKUTU</div>", unsafe_allow_html=True)

# Show the last updated time with larger font size
last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f"""
    <div style='font-size: 24px; font-weight: bold; text-align: center;'>
        Last Updated: {last_updated}
    </div>
""", unsafe_allow_html=True)

def create_static_table(data, title):
    if not data.empty:
        st.markdown(f'<div class="table-title">{title}</div>', unsafe_allow_html=True)
        full_data, limited_data = sort_and_limit_rows(data)
        display_data = limited_data

        show_all = False
        if len(full_data) > 8:
            show_all = st.checkbox("Show All", key=f"checkbox_{title}_sheet1")
            if show_all:
                display_data = full_data

        # Center all columns except 'NAMA CALON', including headers
        styled_data = display_data.style.set_properties(subset=[col for col in display_data.columns if col != 'NAMA CALON'], **{'text-align': 'center'}) \
                                        .set_properties(subset=['NAMA CALON'], **{'text-align': 'left'})  # Left align 'NAMA CALON'
        
        styled_data = styled_data.set_table_styles([
            {'selector': 'th', 'props': [('text-align', 'center')]}
        ])

        # Highlight rows below row 15
        styled_data = styled_data.apply(highlight_rows_below_15, show_all=show_all, axis=None)

        st.write(styled_data.hide(axis='index').to_html(), unsafe_allow_html=True)
    else:
        st.warning(f"{title} is empty or does not contain valid data.")

for i, (title, table) in enumerate(zip(st.session_state.titles_sheet1, st.session_state.tables_sheet1), start=1):
    create_static_table(table, title)

# Load data from multiple tabs
def load_data_from_tabs(sheet_url, sheet_name):
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url).worksheet(sheet_name)
    all_values = sheet.get_all_values()

    title1 = extract_title(all_values[1:2])
    title2 = extract_title(all_values[6:7])
    title3 = extract_title(all_values[11:12])
    title4 = extract_title(all_values[17:18])
    title5 = extract_title(all_values[22:23])

    table1 = clean_and_filter_data(all_values[2:6])
    table2 = clean_and_filter_data(all_values[7:11])
    table3 = clean_and_filter_data(all_values[12:16])
    table4 = clean_and_filter_data(all_values[18:22])
    table5 = clean_and_filter_data(all_values[23:])

    return (title1, title2, title3, title4, title5), (table1, table2, table3, table4, table5)

# Display the header above the tab selection
st.markdown("<div class='main-header'>KEPUTUSAN PENUH PEMILIHAN SAYAP BERSEKUTU BAHAGIAN</div>", unsafe_allow_html=True)

# Automatically display data for the selected Bahagian
selected_tab = st.selectbox("Select Bahagian", bahagian_tabs)

def bahagian_tab_layout(sheet_url, sheet_name):
    titles, tables = load_data_from_tabs(sheet_url, sheet_name)
    for idx, (title, table) in enumerate(zip(titles, tables)):
        sorted_table, _ = sort_and_limit_rows(table)

        st.markdown(f'<div class="table-title">{title}</div>', unsafe_allow_html=True)

        # Center all columns, including headers
        styled_data = sorted_table.style.set_properties(**{'text-align': 'center'})

        styled_data = styled_data.set_table_styles([
            {'selector': 'th', 'props': [('text-align', 'center')]}
        ])

        if idx == 4:  # For the last table, apply highlight_rows_below_8 and show all rows
            styled_data = styled_data.apply(highlight_rows_below_8, show_all=False, axis=None)
            st.write(styled_data.hide(axis='index').to_html(), unsafe_allow_html=True)
        else:
            st.write(styled_data.hide(axis='index').to_html(), unsafe_allow_html=True)

bahagian_tab_layout(sheet_url_tabs, selected_tab)
