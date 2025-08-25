import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date, datetime
from pathlib import Path

# ---------- Streamlit Config ----------
st.set_page_config(page_title="Kawa Clinic Appointments", layout="wide")
st.title("📅 Kawa Clinic - Appointment Records")

# ---------- Google Sheets Setup ----------
SHEET_ID = "1keLx7iBH92_uKxj-Z70iTmAVus7X9jxaFXl_SQ-mZvU"

@st.cache_resource
def get_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1
    # If sheet is empty, initialize headers
    if sheet.row_count == 0:
        sheet.append_row(["Appt_Date", "Patient_Name", "Appt_Time", "Payment"])
    return sheet

sheet = get_sheet()

# ---------- Data Functions ----------
def load_bookings() -> pd.DataFrame:
    """
    Load appointments from Google Sheet into DataFrame
    """
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    expected_cols = ["Appt_Date", "Patient_Name", "Appt_Time", "Payment"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""
    df = df[expected_cols]
    if not df.empty:
        df["Appt_Date"] = pd.to_datetime(df["Appt_Date"], errors="coerce")
    return df

def append_booking(rec: dict):
    """
    Append one new appointment to Google Sheet
    """
    sheet.append_row([rec["Appt_Date"], rec["Patient_Name"], rec["Appt_Time"], rec["Payment"]],
                     value_input_option="USER_ENTERED")

# ---------- Check overlap ----------
def check_overlap(df: pd.DataFrame, appt_date: date, appt_time: str) -> bool:
    if df.empty:
        return False
    mask = (df["Appt_Date"].dt.date == appt_date) & (df["Appt_Time"] == appt_time)
    return mask.any()

# ---------- Safe rerun ----------
def safe_rerun():
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    elif hasattr(st, "rerun"):
        st.rerun()
    else:
        st.stop()

# ---------- Sidebar: Add Appointment ----------
st.sidebar.header("Add Appointment")
picked_date  = st.sidebar.date_input("Appointment Date", value=date.today())
appt_time    = st.sidebar.text_input("Appointment Time (manual)")
patient_name = st.sidebar.text_input("Patient Name")
payment      = st.sidebar.text_input("Payment")

if st.sidebar.button("💾 Save Appointment"):
    df = load_bookings()
    if not patient_name or not appt_time:
        st.sidebar.error("Patient Name and Appointment Time are required.")
    elif check_overlap(df, picked_date, appt_time):
        st.sidebar.error("Appointment already exists at this time.")
    else:
        record = {
            "Appt_Date":    picked_date.isoformat(),
            "Patient_Name": patient_name.strip(),
            "Appt_Time":    appt_time.strip(),
            "Payment":      payment.strip()
        }
        append_booking(record)
        st.sidebar.success("✅ Appointment saved successfully!")
        safe_rerun()

# ---------- Load Bookings ----------
bookings = load_bookings()

# ---------- Main Tabs ----------
upcoming_tab, archived_tab = st.tabs(["📌 Upcoming Appointments", "📂 Archived Appointments"])

# Upcoming
with upcoming_tab:
    upcoming = bookings[bookings["Appt_Date"].dt.date >= date.today()].copy()
    if upcoming.empty:
        st.info("No upcoming appointments booked.")
    else:
        upcoming = upcoming.sort_values("Appt_Date")
        for d in upcoming["Appt_Date"].dt.date.drop_duplicates():
            day_df = upcoming[upcoming["Appt_Date"].dt.date == d]
            with st.expander(d.strftime("📅 %A, %d %B %Y")):
                df_disp = day_df[["Patient_Name","Appt_Time","Payment"]].reset_index(drop=True)
                df_disp.index = range(1, len(df_disp)+1)
                st.dataframe(df_disp, use_container_width=True)

# Archived
with archived_tab:
    archived = bookings[bookings["Appt_Date"].dt.date < date.today()].copy()
    if archived.empty:
        st.info("No archived appointments found.")
    else:
        archived = archived.sort_values("Appt_Date", ascending=False)
        for d in archived["Appt_Date"].dt.date.drop_duplicates():
            day_df = archived[archived["Appt_Date"].dt.date == d]
            with st.expander(d.strftime("📅 %A, %d %B %Y")):
                df_disp = day_df[["Patient_Name","Appt_Time","Payment"]].reset_index(drop=True)
                df_disp.index = range(1, len(df_disp)+1)
                st.dataframe(df_disp, use_container_width=True)
