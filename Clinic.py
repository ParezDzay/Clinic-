import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
from pathlib import Path

# ---------------- Streamlit config ----------------
st.set_page_config(page_title="Kawa Clinic Appointments", layout="wide")
st.title("📅 Kawa Clinic - Appointment Records")

# ---------------- Google Sheets setup ----------------
# Replace with the sheet id you shared
SHEET_ID = "1keLx7iBH92_uKxj-Z70iTmAVus7X9jxaFXl_SQ-mZvU"

@st.cache_resource
def get_sheet():
    # st.secrets["gcp_service_account"] must contain the service-account JSON as a dict
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1

    # Ensure headers exist (only if the sheet is empty)
    headers = ["Appt_Date", "Patient_Name", "Appt_Time", "Payment"]
    # If sheet is empty or has fewer columns, set headers
    rows = sheet.get_all_values()
    if len(rows) == 0 or rows[0] != headers:
        # Clear sheet and write headers (works even if sheet empty)
        sheet.resize(rows=1)
        sheet.update([headers])
    return sheet

sheet = get_sheet()

# ---------------- Data functions ----------------
def load_bookings() -> pd.DataFrame:
    """Load appointments from Google Sheet into a DataFrame"""
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    expected_cols = ["Appt_Date", "Patient_Name", "Appt_Time", "Payment"]
    for c in expected_cols:
        if c not in df.columns:
            df[c] = ""
    df = df[expected_cols]
    if not df.empty:
        df["Appt_Date"] = pd.to_datetime(df["Appt_Date"], errors="coerce")
    return df

def append_booking(rec: dict):
    """Append a new appointment row to Google Sheet"""
    # Use USER_ENTERED so dates and formats are interpreted
    sheet.append_row([
        rec["Appt_Date"],
        rec["Patient_Name"],
        rec["Appt_Time"],
        rec["Payment"]
    ], value_input_option="USER_ENTERED")

def check_overlap(df: pd.DataFrame, appt_date: date, appt_time: str) -> bool:
    """Check overlap by exact date and time"""
    if df.empty:
        return False
    mask = (df["Appt_Date"].dt.date == appt_date) & (df["Appt_Time"] == appt_time)
    return mask.any()

# ---------------- Sidebar: Add Appointment form ----------------
st.sidebar.header("➕ Add Appointment")
with st.sidebar.form("add_appointment", clear_on_submit=True):
    patient_name = st.text_input("Patient Name")
    appt_date = st.date_input("Appointment Date", value=date.today())
    appt_time = st.text_input("Appointment Time (manual)", placeholder="e.g., 14:30")
    payment = st.text_input("Payment")
    submitted = st.form_submit_button("💾 Save Appointment")

    if submitted:
        df = load_bookings()  # read current sheet
        if not patient_name or not appt_time:
            st.sidebar.error("Patient Name and Appointment Time are required.")
        elif check_overlap(df, appt_date, appt_time):
            st.sidebar.error("An appointment already exists at this time.")
        else:
            # Save appt_date as ISO string so Sheets stores it nicely
            record = {
                "Appt_Date": appt_date.isoformat(),
                "Patient_Name": patient_name.strip(),
                "Appt_Time": appt_time.strip(),
                "Payment": payment.strip()
            }
            append_booking(record)
            st.sidebar.success("✅ Appointment saved successfully!")

# ---------------- Load bookings and show tabs ----------------
bookings = load_bookings()

upcoming_tab, archived_tab = st.tabs(["📌 Upcoming Appointments", "📂 Archived Appointments"])

# Upcoming: date >= today (most recent days first)
with upcoming_tab:
    if bookings.empty or bookings["Appt_Date"].isna().all():
        st.info("No upcoming appointments booked.")
    else:
        upcoming = bookings[bookings["Appt_Date"].dt.date >= date.today()].copy()
        if upcoming.empty:
            st.info("No upcoming appointments booked.")
        else:
            upcoming = upcoming.sort_values("Appt_Date", ascending=False)
            for d in upcoming["Appt_Date"].dt.date.drop_duplicates():
                day_df = upcoming[upcoming["Appt_Date"].dt.date == d]
                with st.expander(d.strftime("📅 %A, %d %B %Y")):
                    disp = day_df[["Patient_Name","Appt_Time","Payment"]].reset_index(drop=True)
                    disp.index = range(1, len(disp)+1)
                    st.dataframe(disp, use_container_width=True)

# Archived: date < today
with archived_tab:
    if bookings.empty or bookings["Appt_Date"].isna().all():
        st.info("No archived appointments found.")
    else:
        archived = bookings[bookings["Appt_Date"].dt.date < date.today()].copy()
        if archived.empty:
            st.info("No archived appointments found.")
        else:
            archived = archived.sort_values("Appt_Date", ascending=False)
            for d in archived["Appt_Date"].dt.date.drop_duplicates():
                day_df = archived[archived["Appt_Date"].dt.date == d]
                with st.expander(d.strftime("📅 %A, %d %B %Y")):
                    disp = day_df[["Patient_Name","Appt_Time","Payment"]].reset_index(drop=True)
                    disp.index = range(1, len(disp)+1)
                    st.dataframe(disp, use_container_width=True)
