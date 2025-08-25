import streamlit as st
import pandas as pd
from datetime import date, datetime, time, timedelta
from pathlib import Path

# ---------- CSV Setup ----------
BASE_DIR = Path(__file__).parent if "__file__" in globals() else Path.cwd()
CSV_FILE = BASE_DIR / "kawa clinic.csv"

# Create CSV if it doesn't exist
if not CSV_FILE.exists():
    df = pd.DataFrame(columns=[
        "Patient Name", "Appointment Date", "Appointment Time (manual)", "Payment"
    ])
    df.to_csv(CSV_FILE, index=False)

# ---------- Data Functions ----------
def load_bookings() -> pd.DataFrame:
    df = pd.read_csv(CSV_FILE)
    df["Appointment Date"] = pd.to_datetime(df["Appointment Date"], errors="coerce")
    return df

def append_booking(rec: dict):
    df = load_bookings()
    df = pd.concat([df, pd.DataFrame([rec])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)

def check_overlap(df: pd.DataFrame, d: date, patient_name: str, hr: str) -> bool:
    if df.empty:
        return False
    mask = (
        (df["Appointment Date"] == pd.Timestamp(d)) &
        (df["Patient Name"].str.lower() == patient_name.lower()) &
        (df["Appointment Time (manual)"] == hr)
    )
    return mask.any()

def safe_rerun():
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    elif hasattr(st, "rerun"):
        st.rerun()
    else:
        st.stop()

# ---------- Main Tabs ----------
tabs = st.tabs(["📌 Upcoming Appointments", "📂 Appointment Archive"])

# Tab: Upcoming Appointments
with tabs[0]:
    bookings = load_bookings()
    yesterday = pd.Timestamp(date.today() - timedelta(days=1))
    upcoming = bookings[bookings["Appointment Date"] > yesterday]

    st.subheader("📌 Upcoming Appointments")
    if upcoming.empty:
        st.info("No upcoming appointments.")
    else:
        disp = (
            upcoming
            .drop_duplicates(subset=["Appointment Date", "Appointment Time (manual)"])
            .sort_values(["Appointment Date", "Appointment Time (manual)"])
        )
        for d in disp["Appointment Date"].dt.date.unique():
            day_df = disp[disp["Appointment Date"].dt.date == d]
            with st.expander(d.strftime("📅 %A, %d %B %Y")):
                dd = day_df[["Patient Name", "Appointment Time (manual)", "Payment"]].reset_index(drop=True)
                dd.index = range(1, len(dd)+1)
                st.dataframe(dd, use_container_width=True)

# Tab: Archived Appointments
with tabs[1]:
    bookings = load_bookings()
    yesterday = pd.Timestamp(date.today() - timedelta(days=1))
    archive = bookings[bookings["Appointment Date"] <= yesterday]

    st.subheader("📂 Appointment Archive")
    if archive.empty:
        st.info("No archived appointments.")
    else:
        disp = (
            archive
            .drop_duplicates(subset=["Appointment Date", "Appointment Time (manual)"])
            .sort_values(["Appointment Date", "Appointment Time (manual)"], ascending=False)
            .copy()
        )
        disp["Appointment Date"] = disp["Appointment Date"].dt.strftime("%Y-%m-%d")
        disp.reset_index(drop=True, inplace=True)
        disp.index += 1
        st.dataframe(disp[["Appointment Date", "Patient Name", "Appointment Time (manual)", "Payment"]], use_container_width=True)

# ---------- Sidebar: Add Booking Form ----------
st.sidebar.header("Add Appointment")
picked_date = st.sidebar.date_input("Appointment Date", value=date.today())
patient_name = st.sidebar.text_input("Patient Name")
appt_time = st.sidebar.text_input("Appointment Time (manual)", placeholder="HH:MM")
payment = st.sidebar.text_input("Payment")

if st.sidebar.button("💾 Save Appointment"):
    if not patient_name or not appt_time or not payment:
        st.sidebar.error("All fields are required.")
    elif check_overlap(bookings, picked_date, patient_name, appt_time):
        st.sidebar.error("This appointment already exists.")
    else:
        record = {
            "Patient Name": patient_name.strip(),
            "Appointment Date": picked_date.isoformat(),
            "Appointment Time (manual)": appt_time.strip(),
            "Payment": payment.strip()
        }
        append_booking(record)
        st.sidebar.success("Appointment saved successfully.")
        safe_rerun()
