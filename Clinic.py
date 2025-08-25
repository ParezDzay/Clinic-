import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from pathlib import Path

# ---------- CSV File Setup ----------
BASE_DIR = Path(__file__).parent if "__file__" in globals() else Path.cwd()
CSV_FILE = BASE_DIR / "kawaclinic.csv"

# ---------- Load and Save Functions ----------
def load_bookings():
    if CSV_FILE.exists():
        df = pd.read_csv(CSV_FILE)
    else:
        df = pd.DataFrame(columns=[
            "Patient Name", "Appointment Date", "Appointment Time (manual)", "Payment"
        ])
        df.to_csv(CSV_FILE, index=False)
    return df

def save_bookings(df):
    df.to_csv(CSV_FILE, index=False)

# ---------- Safe rerun helper ----------
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.stop()

# ---------- Streamlit Page Setup ----------
st.set_page_config(page_title="Global Eye Center (Appointments)", layout="wide")
st.title("Global Eye Center (Appointments)")

# ---------- Main Tabs ----------
tabs = st.tabs(["📌 Upcoming Appointments", "📂 Appointment Archive"])

# ---------- Sidebar Form ----------
st.sidebar.header("Add New Appointment")
patient_name = st.sidebar.text_input("Patient Name")
appt_date = st.sidebar.date_input("Appointment Date", value=date.today())
appt_time = st.sidebar.text_input("Appointment Time (manual)", placeholder="HH:MM")
payment = st.sidebar.text_input("Payment", placeholder="e.g., Cash / Card / None")

if st.sidebar.button("💾 Save Appointment"):
    if not patient_name:
        st.sidebar.error("Patient Name is required.")
    elif not appt_time:
        st.sidebar.error("Appointment Time is required.")
    else:
        df = load_bookings()
        new_record = {
            "Patient Name": patient_name.strip(),
            "Appointment Date": appt_date.strftime("%Y-%m-%d"),
            "Appointment Time (manual)": appt_time.strip(),
            "Payment": payment.strip()
        }
        df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
        save_bookings(df)
        st.sidebar.success("Appointment saved successfully.")
        safe_rerun()

# ---------- Load Bookings ----------
bookings = load_bookings()
bookings["Appointment Date"] = pd.to_datetime(bookings["Appointment Date"], errors="coerce")
yesterday = pd.Timestamp(date.today() - timedelta(days=1))

# ---------- Upcoming Tab ----------
with tabs[0]:
    upcoming = bookings[bookings["Appointment Date"] > yesterday]
    st.subheader("📌 Upcoming Appointments")
    if upcoming.empty:
        st.info("No upcoming appointments.")
    else:
        upcoming_disp = upcoming.sort_values("Appointment Date")
        for d in upcoming_disp["Appointment Date"].dt.date.unique():
            day_df = upcoming_disp[upcoming_disp["Appointment Date"].dt.date == d]
            with st.expander(d.strftime("📅 %A, %d %B %Y")):
                day_df_display = day_df[["Patient Name", "Appointment Time (manual)", "Payment"]].reset_index(drop=True)
                day_df_display.index = range(1, len(day_df_display)+1)
                st.dataframe(day_df_display, use_container_width=True)

# ---------- Archive Tab ----------
with tabs[1]:
    archive = bookings[bookings["Appointment Date"] <= yesterday]
    st.subheader("📂 Appointment Archive")
    if archive.empty:
        st.info("No archived appointments.")
    else:
        archive_disp = archive.sort_values("Appointment Date", ascending=False).reset_index(drop=True)
        archive_disp.index += 1
        st.dataframe(archive_disp[["Patient Name", "Appointment Date", "Appointment Time (manual)", "Payment"]],
                     use_container_width=True)
