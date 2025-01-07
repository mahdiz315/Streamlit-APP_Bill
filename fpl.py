import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime  # Import datetime for time handling
import matplotlib.pyplot as plt

#st.set_page_config(layout="wide")

st.title("FPL Dashboard Analysis")

# --- Step 1: Number of Accounts ---
st.sidebar.header("Account Information")
num_accounts = st.sidebar.number_input("Number of Accounts", min_value=1, step=1, value=1)

# --- Step 2: File Upload ---
uploaded_files = []
for i in range(num_accounts):
    st.sidebar.subheader(f"Upload Files for Account {i + 1}")
    uploaded_files.append(st.sidebar.file_uploader(f"Upload 12 Monthly Files for Account {i + 1}", accept_multiple_files=True))

# --- Step 3: Working Hours ---
#st.header("Manufacturing Working Hours")

# Operating Days
saturday_op = st.checkbox("Saturday an operating day")
sunday_op = st.checkbox("Sunday an operating day")

# Operating Shifts with dynamic time selection
st.subheader("Define Working Shifts")

shifts = []

# Debug: Ensure shifts are captured
def log_shifts(shifts):
    st.sidebar.write("### Shifts Configured:")
    for idx, shift in enumerate(shifts):
        st.sidebar.write(f"Shift {idx + 1}: {shift[0]} to {shift[1]} ({shift[2]})")

# 1st Shift (Monday - Friday)
col1, col2, col3 = st.columns([1, 2, 2])
with col1:
    shift_1 = st.checkbox("1st Shift - Monday - Friday")
with col2:
    shift_1_start = st.time_input("Start time (1st Shift - Monday - Friday)", value=pd.Timestamp("06:30").time(), key="shift_1_start")
with col3:
    shift_1_end = st.time_input("End time (1st Shift - Monday - Friday)", value=pd.Timestamp("15:00").time(), key="shift_1_end")
if shift_1:
    shifts.append((shift_1_start, shift_1_end, "Weekday"))

# 2nd Shift (Monday - Friday)
col1, col2, col3 = st.columns([1, 2, 2])
with col1:
    shift_2 = st.checkbox("2nd Shift - Monday - Friday")
with col2:
    shift_2_start = st.time_input("Start time (2nd Shift - Monday - Friday)", value=pd.Timestamp("15:00").time(), key="shift_2_start")
with col3:
    shift_2_end = st.time_input("End time (2nd Shift - Monday - Friday)", value=pd.Timestamp("23:00").time(), key="shift_2_end")
if shift_2:
    shifts.append((shift_2_start, shift_2_end, "Weekday"))

# 3rd Shift (Monday - Friday)
col1, col2, col3 = st.columns([1, 2, 2])
with col1:
    shift_3 = st.checkbox("3rd Shift - Monday - Friday")
with col2:
    shift_3_start = st.time_input("Start time (3rd Shift - Monday - Friday)", value=pd.Timestamp("23:00").time(), key="shift_3_start")
with col3:
    shift_3_end = st.time_input("End time (3rd Shift - Monday - Friday)", value=pd.Timestamp("06:30").time(), key="shift_3_end")
if shift_3:
    shifts.append((shift_3_start, shift_3_end, "Weekday"))

# Special weekend shifts
if saturday_op:
    st.subheader("Saturday Shifts")
    col1, col2, col3 = st.columns([1, 2, 2])
    with col1:
        saturday_shift_start = st.time_input("Start time (Saturday Shift)", value=pd.Timestamp("08:00").time(), key="saturday_start")
    with col3:
        saturday_shift_end = st.time_input("End time (Saturday Shift)", value=pd.Timestamp("16:00").time(), key="saturday_end")
    shifts.append((saturday_shift_start, saturday_shift_end, "Saturday"))

if sunday_op:
    st.subheader("Sunday Shifts")
    col1, col2, col3 = st.columns([1, 2, 2])
    with col1:
        sunday_shift_start = st.time_input("Start time (Sunday Shift)", value=pd.Timestamp("08:00").time(), key="sunday_start")
    with col3:
        sunday_shift_end = st.time_input("End time (Sunday Shift)", value=pd.Timestamp("16:00").time(), key="sunday_end")
    shifts.append((sunday_shift_start, sunday_shift_end, "Sunday"))

log_shifts(shifts)  # Log configured shifts

# --- Step 4: Number of Demand Columns ---
num_demand_columns = st.number_input("Number of Demand Columns", min_value=1, step=1, value=1)
demand_columns = [st.text_input(f"Enter name of Demand Column {i + 1}") for i in range(num_demand_columns)]

# --- Step 5: Interval ---
interval = st.radio("Select Data Interval", [1, 0.5, 0.25], index=0)

# --- Step 7: File Preprocessing ---
def preprocess_file(file, demand_column_name):
    # Read the file, skipping the first 3 rows
    df = pd.read_excel(file, skiprows=3)

    # Parse DateTime or Date and Time columns
    if "DateTime" in df.columns:
        df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce")
        df["Time"] = df["DateTime"].dt.time
        df["Hour"] = df["DateTime"].dt.hour
    elif "Date" in df.columns and "Time" in df.columns:
        # Parse time strings into datetime.time objects
        df["Time"] = df["Time"].apply(lambda x: datetime.strptime(x, "%I:%M %p").time() if isinstance(x, str) else x)
        df["DateTime"] = pd.to_datetime(df["Date"] + " " + df["Time"].astype(str), errors="coerce")
        df["Hour"] = df["DateTime"].dt.hour

    # Validate the demand column
    if demand_column_name not in df.columns:
        st.error(f"Demand column '{demand_column_name}' not found!")
        return None

    # Ensure demand values are numeric
    df["Demand"] = pd.to_numeric(df[demand_column_name], errors="coerce")

    # Add additional datetime-related columns
    df["DayName"] = df["DateTime"].dt.day_name()
    df["Month"] = df["DateTime"].dt.strftime("%B")
    df["Year"] = df["DateTime"].dt.year

    return df



def calculate_operating(row, shifts, saturday_op=False, sunday_op=False):
    """
    Determine if the given row is within operating hours.
    """
    if pd.isna(row["Time"]):
        return False

    # Exclude weekends unless marked as operating
    if row["DayName"] == "Saturday" and not saturday_op:
        return False
    if row["DayName"] == "Sunday" and not sunday_op:
        return False

    # Check against shifts
    for start, end, day_type in shifts:
        if day_type == "Weekday" and row["DayName"] in ["Saturday", "Sunday"]:
            continue
        if day_type != "Weekday" and row["DayName"] != day_type:
            continue

        # Handle shifts crossing midnight
        row_time = row["Time"]
        if start < end:
            if start <= row_time <= end:
                return True
        else:
            if row_time >= start or row_time <= end:
                return True
    return False


def calculate_on_peak(row):
    """
    Determine if a row is within on-peak hours.
    """
    if row["DayName"] in ["Saturday", "Sunday"]:
        return False  # Weekends are off-peak

    hour = row["Hour"]
    if 4 <= row["DateTime"].month <= 10:  # April to October
        return 12 <= hour <= 21  # On-peak: 12 PM to 9 PM
    else:  # November to March
        return (6 <= hour <= 10) or (18 <= hour <= 22)  # On-peak: 6-10 AM, 6-10 PM


def generate_monthly_summary(data, shifts, interval, saturday_op=False, sunday_op=False):
    """
    Generate a monthly summary table with operating, non-operating, on-peak, and off-peak demands.
    """
    data = data.reset_index(drop=True)

    # Calculate if the time falls within operating hours
    data["Operating"] = data.apply(lambda row: calculate_operating(row, shifts, saturday_op, sunday_op), axis=1)
    data["OnPeak"] = data.apply(calculate_on_peak, axis=1)

    # Scale demand values by the interval
    data["Demand"] *= interval

    # Monthly aggregation with logical masks
    monthly_summary = data.groupby("Month").agg(
        NotOperating=("Demand", lambda x: x[~data.loc[x.index, "Operating"]].sum()),
        OperatingShift=("Demand", lambda x: x[data.loc[x.index, "Operating"]].sum()),
        TotalDemand=("Demand", "sum"),
        OnPeakOperating=("Demand", lambda x: x[data.loc[x.index, "Operating"] & data.loc[x.index, "OnPeak"]].sum()),
        OffPeakOperating=("Demand", lambda x: x[data.loc[x.index, "Operating"] & ~data.loc[x.index, "OnPeak"]].sum()),
        OnPeakNotOperating=("Demand", lambda x: x[~data.loc[x.index, "Operating"] & data.loc[x.index, "OnPeak"]].sum()),
        OffPeakNotOperating=("Demand", lambda x: x[~data.loc[x.index, "Operating"] & ~data.loc[x.index, "OnPeak"]].sum()),
    ).reset_index()
    
    # Add Ratio column
    monthly_summary["NOratio"] = monthly_summary["NotOperating"] / monthly_summary["TotalDemand"]

    # Add a total row
    total_row = monthly_summary.sum(numeric_only=True).to_frame().T
    total_row["Month"] = "Total"
    total_row["NOratio"] = total_row["NotOperating"] / total_row["TotalDemand"]
    monthly_summary = pd.concat([monthly_summary, total_row], ignore_index=True)
    #st.write("Debug: Operating and OnPeak Flags for January")
    #st.dataframe(combined_data[combined_data["Month"] == "January"])

    # Add a total row
    total_row = monthly_summary.sum(numeric_only=True).to_frame().T
    total_row["Month"] = "Total"
    #monthly_summary = pd.concat([monthly_summary, total_row], ignore_index=True)

    return monthly_summary



# Initialize a list to store data for the consolidated table
consolidated_data = []
month_order = {
                            "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
                            "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
                        }

if st.button("Process Files"):
    all_data_by_account = []
    consolidated_data = []  # Initialize for the consolidated table

    # Process files for each account
    for account_index, files in enumerate(uploaded_files):
        st.write(f"### Processing Account {account_index + 1}")

        account_data = []
        for file in files:
            for demand_column in demand_columns:
                df = preprocess_file(file, demand_column)
                if df is not None:
                    account_data.append(df)

        if account_data:
            combined_account_data = pd.concat(account_data, ignore_index=True)
            combined_account_data["Operating"] = combined_account_data.apply(
                lambda row: calculate_operating(row, shifts, saturday_op, sunday_op), axis=1
            )
            combined_account_data["OnPeak"] = combined_account_data.apply(calculate_on_peak, axis=1)

            # Generate the summary table for the current account
            summary_account = generate_monthly_summary(combined_account_data, shifts, interval, saturday_op, sunday_op)

            # Add "Year" column to summary_account using year mapping from combined_account_data
            year_mapping = combined_account_data.groupby("Month")["Year"].first().reset_index()
            summary_account = pd.merge(summary_account, year_mapping, on="Month", how="left")

            # Add account number to identify the source account
            summary_account["Account"] = f"Account {account_index + 1}"

            # Add a "Month / Year" column
            summary_account["MonthOrder"] = summary_account["Month"].map(month_order)
            summary_account = summary_account.sort_values(by=["Year", "MonthOrder"])
            summary_account["Month / Year"] = summary_account["Month"] + " / " + summary_account["Year"].fillna("").astype(str)

            # Separate Total row
            total_row = summary_account[summary_account["Month"] == "Total"]
            summary_account = summary_account[summary_account["Month"] != "Total"]
            total_row["Month / Year"] = "Total / Total"  # Assign placeholder value
            total_row["Year"] = None  # Set Year to None for the Total row
            summary_account = pd.concat([summary_account, total_row], ignore_index=True)

            # Rearrange columns
            summary_account = summary_account[["Account", "Month / Year", "Year", "MonthOrder"] + 
                                               [col for col in summary_account.columns if col not in ["Account", "Month / Year", "Year", "MonthOrder", "Month"]]]

            # Save account-specific data
            all_data_by_account.append((account_index + 1, summary_account))
            consolidated_data.append(summary_account)

            # Display the summary table for the current account
            st.write(f"### Monthly Summary for Account {account_index + 1}")
            summary_account.index = summary_account.index + 1
            st.dataframe(summary_account)

    if consolidated_data:
        # Concatenate data for all accounts
        consolidated_table = pd.concat(consolidated_data, ignore_index=True)

        # Extract Month and Year from "Month / Year" if not already present
        if "Month" not in consolidated_table.columns:
            consolidated_table["Month"] = consolidated_table["Month / Year"].str.split(" / ").str[0]
        if "Year" not in consolidated_table.columns:
            consolidated_table["Year"] = consolidated_table["Month / Year"].str.split(" / ").str[1]

        # Ensure 'Year' is numeric
        consolidated_table["Year"] = pd.to_numeric(consolidated_table["Year"], errors="coerce")  # Handle NaN for 'Total' rows

        # Filter out 'Total' rows before aggregation
        filtered_consolidated_table = consolidated_table[consolidated_table["Month / Year"] != "Total / Total"]

        # Group by Month and Year and sum the numeric columns
        aggregated_table = filtered_consolidated_table.groupby(["Month", "Year"]).sum(numeric_only=True).reset_index()

        # Add a "Month / Year" column
        aggregated_table["MonthOrder"] = aggregated_table["Month"].map(month_order)
        aggregated_table = aggregated_table.sort_values(by=["Year", "MonthOrder"]).reset_index(drop=True)
        aggregated_table["Month / Year"] = aggregated_table["Month"] + " / " + aggregated_table["Year"].astype(int).astype(str)

        # Rearrange columns
        aggregated_table = aggregated_table[["Month / Year", "Year"] + 
                                            [col for col in aggregated_table.columns if col not in ["Month / Year", "Year", "MonthOrder", "Month"]]]

        # Add a Total row to the aggregated table
        total_row = aggregated_table.sum(numeric_only=True).to_frame().T
        total_row["Month / Year"] = "Total / Total"
        total_row["Year"] = None  # Set Year to None for the Total row
        aggregated_table = pd.concat([aggregated_table, total_row], ignore_index=True)

        # Display the aggregated table
        st.write("### Consolidated Monthly Summary (Summation of All Accounts)")
        st.dataframe(aggregated_table)