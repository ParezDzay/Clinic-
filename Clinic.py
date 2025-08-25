# Clinic.py
import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path

# ---------- Safe CSV setup ----------
CSV_FILE = Path("kawa clinic.csv")           # file will live in the app folder
CSV_FILE.parent.mkdir(parents=True, exist_ok=True)  # ensure parent exists

# ---------- Data functions ----------
def load_bookings() -> pd.DataFrame:
    """Load appointments from CSV; create a clean file if missing or malformed."""
    expected = ["Appt_Date", "Patient_Name", "Appt_Time", "Payment"]

    # create file if missing
    if not CSV_FILE.exists():
        pd.DataFrame(columns=expected).to_csv(CSV_FILE, index=False)

    # read file
    df = pd.read_csv(CSV_FILE)

    # ensure expected columns exist
    for c in expected:
        if c not in df.columns:
            df[c] = ""

    # keep only expected columns (protect against corrupted files)
    df = df[expected]

    # parse Appt_Date as datetime
    if not df.empty:
        df["Appt_Date"] = pd.to_datetime(df["Appt_Date"], errors="coerce")
    else:
        df["Appt_Date"] = pd.to_datetime(df["Appt_Date"], errors="coerce")

    return df

def append_booking(record: dict):
    """Append one appointment record to CSV (record keys must match expected cols)."""
    df = load_bookings()
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)

def check_overlap(df: pd.DataFrame, appt_date: date, appt_time: str) -> bool:
    """Return True if there is already a row with the same date and time."""
    if df.empty:
        return False
    mask = (df["Appt_Date"].dt.date == appt_date) & (df["Appt_Time"] == appt_time)
    return mask.any()

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Kawa Clinic Appointments", layout="wide")
st.title("📅 Kawa Clinic — Appointment Records")

# Sidebar form
st.sidebar.header("➕ Add Appointment")
with st.sidebar.form("add_appointment", clear_on_submit=True):
    patient_name = st.text_input("Patient Name")
    appt_date = st.date_input("Appointment Date", value=date.today())
    appt_time = st.text_input("Appointment Time (manual)", placeholder="e.g., 14:30")
    payment = st.text_input("Payment")
    submitted = st.form_submit_button("💾 Save Appointment")

    if submitted:
        df_current = load_bookings()
        if not patient_name.strip() or not appt_time.strip():
            st.sidebar.error("Patient Name and Appointment Time are required.")
        elif check_overlap(df_current, appt_date, appt_time.strip()):
            st.sidebar.error("⚠️ An appointment already exists at this date/time.")
        else:
            record = {
                "Appt_Date": appt_date.isoformat(),    # store ISO string for reliability
                "Patient_Name": patient_name.strip(),
                "Appt_Time": appt_time.strip(),
                "Payment": payment.strip()
            }
            append_booking(record)
            st.sidebar.success("✅ Appointment saved successfully!")

# Load bookings for display
bookings = load_bookings()

# If there are no valid dates yet, create empty upcoming/archived frames
if bookings.empty or bookings["Appt_Date"].isna().all():
    upcoming = pd.DataFrame(columns=["Appt_Date","Patient_Name","Appt_Time","Payment"])
    archived = upcoming.copy()
else:
    upcoming = bookings[bookings["Appt_Date"].dt.date >= date.today()].copy()
    archived = bookings[bookings["Appt_Date"].dt.date < date.today()].copy()

# Tabs
upcoming_tab, archived_tab = st.tabs(["📌 Upcoming Appointments", "📂 Archived Appointments"])

with upcoming_tab:
    if upcoming.empty:
        st.info("No upcoming appointments booked.")
    else:
        st.subheader("📌 Upcoming Appointments")
        upcoming = upcoming.sort_values("Appt_Date", ascending=False)
        for day in upcoming["Appt_Date"].dt.date.drop_duplicates():
            day_df = upcoming[upcoming["Appt_Date"].dt.date == day]
            with st.expander(day.strftime("📅 %A, %d %B %Y")):
                show_df = day_df[["Patient_Name","Appt_Time","Payment"]].reset_index(drop=True)
                show_df.index = range(1, len(show_df) + 1)
                st.dataframe(show_df, use_container_width=True)

with archived_tab:
    if archived.empty:
        st.info("No archived appointments found.")
    else:
        st.subheader("📂 Archived Appointments")
        archived = archived.sort_values("Appt_Date", ascending=False)
        for day in archived["Appt_Date"].dt.date.drop_duplicates():
            day_df = archived[archived["Appt_Date"].dt.date == day]
            with st.expander(day.strftime("📅 %A, %d %B %Y")):
                show_df = day_df[["Patient_Name","Appt_Time","Payment"]].reset_index(drop=True)
                show_df.index = range(1, len(show_df) + 1)
                st.dataframe(show_df, use_container_width=True)
