import streamlit as st
import pandas as pd
from datetime import date
import os

# ---------- CSV File ----------
CSV_FILE = "/Users/parezdzay/Documents/Kawa Clinic/kawa clinic.csv"

# ---------- Data Functions ----------
def load_bookings() -> pd.DataFrame:
    """Load appointments from CSV"""
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=["Patient_Name","Appt_Date","Appt_Time","Payment"])
        df.to_csv(CSV_FILE, index=False)
    else:
        df = pd.read_csv(CSV_FILE)
        if "Appt_Date" in df.columns:
            df["Appt_Date"] = pd.to_datetime(df["Appt_Date"], errors="coerce")
        else:
            df["Appt_Date"] = pd.NaT
    return df

def append_booking(record: dict):
    """Append a new appointment"""
    df = load_bookings()
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)

def check_overlap(df: pd.DataFrame, appt_date: date, appt_time: str) -> bool:
    """Check if an appointment exists at the same date/time"""
    if df.empty:
        return False
    mask = (df["Appt_Date"].dt.date == appt_date) & (df["Appt_Time"] == appt_time)
    return mask.any()

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Kawa Clinic Appointments", layout="wide")
st.title("📅 Kawa Clinic - Appointment Records")

# ---------- Sidebar: Add Appointment ----------
st.sidebar.header("➕ Add Appointment")
with st.sidebar.form("add_appointment_form", clear_on_submit=True):
    patient_name = st.text_input("Patient Name")
    appt_date = st.date_input("Appointment Date", value=date.today())
    appt_time = st.text_input("Appointment Time (manual)", placeholder="14:30")
    payment = st.text_input("Payment")
    submitted = st.form_submit_button("💾 Save Appointment")

    if submitted:
        bookings = load_bookings()  # Reload before checking
        if not patient_name or not appt_time:
            st.sidebar.error("Patient Name and Appointment Time are required.")
        elif check_overlap(bookings, appt_date, appt_time):
            st.sidebar.error("An appointment already exists at this time.")
        else:
            append_booking({
                "Patient_Name": patient_name.strip(),
                "Appt_Date": appt_date,
                "Appt_Time": appt_time.strip(),
                "Payment": payment.strip()
            })
            st.sidebar.success("✅ Appointment saved successfully!")

# ---------- Load bookings for display ----------
bookings = load_bookings()

# ---------- Main Tabs ----------
upcoming_tab, archived_tab = st.tabs(["📌 Upcoming Appointments", "📂 Archived Appointments"])

# ---------- Upcoming Appointments ----------
with upcoming_tab:
    upcoming = bookings[bookings["Appt_Date"].dt.date >= date.today()].copy()
    if upcoming.empty:
        st.info("No upcoming appointments booked.")
    else:
        st.subheader("📌 Upcoming Appointments")
        upcoming = upcoming.sort_values("Appt_Date", ascending=False)
        for d in upcoming["Appt_Date"].dt.date.drop_duplicates():
            day_df = upcoming[upcoming["Appt_Date"].dt.date == d]
            with st.expander(d.strftime("📅 %A, %d %B %Y")):
                df_disp = day_df[["Patient_Name","Appt_Time","Payment"]].reset_index(drop=True)
                df_disp.index = range(1, len(df_disp)+1)
                st.dataframe(df_disp, use_container_width=True)

# ---------- Archived Appointments ----------
with archived_tab:
    archived = bookings[bookings["Appt_Date"].dt.date < date.today()].copy()
    if archived.empty:
        st.info("No archived appointments found.")
    else:
        st.subheader("📂 Archived Appointments")
        archived = archived.sort_values("Appt_Date", ascending=False)
        for d in archived["Appt_Date"].dt.date.drop_duplicates():
            day_df = archived[archived["Appt_Date"].dt.date == d]
            with st.expander(d.strftime("📅 %A, %d %B %Y")):
                df_disp = day_df[["Patient_Name","Appt_Time","Payment"]].reset_index(drop=True)
                df_disp.index = range(1, len(df_disp)+1)
                st.dataframe(df_disp, use_container_width=True)
