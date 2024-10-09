import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Function to clean and filter data to include only text cells and set headers properly
def clean_and_filter_data(raw_values):
    filtered_rows = [row for row in raw_values if any(isinstance(cell, str) and cell.strip() for cell in row)]

    if len(filtered_rows) < 2:
        return pd.DataFrame()  # Return an empty DataFrame if there's not enough data

    header = [cell.strip() if isinstance(cell, str) and cell.strip() else f"Unnamed_{index}" for index, cell in enumerate(filtered_rows[0])]
    filtered_data = []
    for row in filtered_rows[1:]:
        cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]  # Convert all cells to string to avoid NaNs
        if any(cell for cell in cleaned_row):
            filtered_data.append(cleaned_row)

    data = pd.DataFrame(filtered_data, columns=header)
    data = data.loc[:, ~data.columns.str.contains('^Unnamed')]
    data = data.dropna(axis=1, how='all')

    return data

# Function to extract title from a specific range
def extract_title(raw_values):
    return " ".join([cell.strip() for cell in raw_values[0] if isinstance(cell, str) and cell.strip()])

# Function to load data and titles from Google Sheets
def load_data_and_titles_from_sheets(sheet_url):
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

    table1 = clean_and_filter_data(all_values[2:4])   # A3:G4 (data starts from row 3)
    table2 = clean_and_filter_data(all_values[6:8])   # A7:G8
    table3 = clean_and_filter_data(all_values[10:13]) # A11:G13
    table4 = clean_and_filter_data(all_values[15:18]) # A16:G18
    table5 = clean_and_filter_data(all_values[20:43]) # A21:G43

    return (title1, title2, title3, title4, title5), (table1, table2, table3, table4, table5)

# Function to sort and limit rows of the table based on the last column
def sort_and_limit_rows(data, num_rows=8):
    if not data.empty and len(data) > 1:  # Only sort if there is more than 1 row of data (excluding header)
        # Attempt to convert the last column to numeric values for sorting; if not possible, sort as strings
        try:
            data[data.columns[-1]] = pd.to_numeric(data[data.columns[-1]], errors='coerce')
        except Exception as e:
            print(f"Error in converting to numeric: {e}")

        # Sort by last column in descending order
        sorted_data = data.sort_values(by=data.columns[-1], ascending=False).reset_index(drop=True)
    else:
        sorted_data = data

    # Limit rows if it exceeds the defined number of rows
    return sorted_data, sorted_data if len(sorted_data) <= num_rows else sorted_data.iloc[:num_rows]

# Load data and titles from the Google Sheets link
sheet_url = 'https://docs.google.com/spreadsheets/d/1-dV891Thy0HbL54N2xGHHqeT6TIOEmbrDNlayHLhwDU/edit?usp=sharing'
titles, tables = load_data_and_titles_from_sheets(sheet_url)

# Define the dashboard title and subtitle
st.markdown("<h1 style='text-align: center; color: #333333;'>Election Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: #666666;'>Real-Time Election Results</h2>", unsafe_allow_html=True)

# Styling the UI to be cleaner and more professional
st.markdown("""
<style>
    .table-title {
        font-size: 22px;
        font-weight: bold;
        color: #800000;  /* Dark red color for table titles */
        margin-bottom: 15px;
    }
    .stDataFrame table {
        border-collapse: collapse; /* Ensure borders are collapsed for a straight line */
        width: 100%;
        border: 2px solid #b0bec5; /* Thicker outer border for a solid appearance */
    }
    .stDataFrame th, .stDataFrame td {
        border: 1px solid #90a4ae; /* Consistent border for cells */
        padding: 12px;
        font-size: 14px;
    }
    .stDataFrame th {
        background-color: #e3f2fd;  /* Light blue header background */
        font-weight: bold;
        color: #0d47a1;  /* Dark blue header text */
    }
    .stDataFrame tbody tr:nth-child(even) {
        background-color: #f5f5f5;  /* Light gray background for even rows */
    }
    .stDataFrame tbody tr:hover {
        background-color: #e1f5fe;  /* Light blue highlight on hover */
    }
</style>
""", unsafe_allow_html=True)

# Function to create a styled DataFrame with display limit and toggle option
def create_static_table(data, title):
    if not data.empty:
        st.markdown(f'<div class="table-title">{title}</div>', unsafe_allow_html=True)

        # Sort the data and limit the initial display to 8 rows
        full_data, limited_data = sort_and_limit_rows(data)

        # Only show the checkbox if the data has more than 8 rows
        display_data = limited_data
        if len(full_data) > 8:
            # Checkbox to toggle between full and limited view
            show_all = st.checkbox("Show All", key=f"checkbox_{title}")

            # Toggle between showing limited rows and full rows
            if show_all:
                display_data = full_data

        # Display the data without index
        st.write(display_data.style.hide(axis='index').to_html(), unsafe_allow_html=True)
    else:
        st.warning(f"{title} is empty or does not contain valid data.")

# Display each table with separate titles and content
for i, (title, table) in enumerate(zip(titles, tables), start=1):
    create_static_table(table, title)
