import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from pathlib import Path

# ---------- CSV Storage ----------
CSV_FILE = Path("kawa clinic.csv")  # Local CSV file

# ---------- Streamlit config & Header ----------
st.set_page_config(page_title="Kawa Clinic (Appointments)", layout="wide")
st.title("Kawa Clinic (Appointments)")

# ---------- Data Functions ----------
def load_bookings() -> pd.DataFrame:
    """Load CSV or create empty DataFrame if it doesn't exist."""
    if CSV_FILE.exists():
        df = pd.read_csv(CSV_FILE)
        df["Appointment Date"] = pd.to_datetime(df["Appointment Date"], errors="coerce")
    else:
        df = pd.DataFrame(columns=["Patient Name", "Appointment Date", "Appointment Time (manual)", "Payment"])
        df.to_csv(CSV_FILE, index=False)
    return df

def append_booking(rec: dict):
    """Append a new booking to CSV."""
    df = load_bookings()
    df = pd.concat([df, pd.DataFrame([rec])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)

# ---------- Safe rerun helper ----------
def safe_rerun():
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    elif hasattr(st, "rerun"):
        st.rerun()
    else:
        st.stop()

# ---------- Tabs for Appointments ----------
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
        disp = upcoming.sort_values("Appointment Date", ascending=False)
        for d in disp["Appointment Date"].dt.date.unique():
            day_df = disp[disp["Appointment Date"].dt.date == d]
            with st.expander(d.strftime("📅 %A, %d %B %Y")):
                day_disp = day_df[["Patient Name", "Appointment Time (manual)", "Payment"]].reset_index(drop=True)
                day_disp.index = range(1, len(day_disp)+1)
                st.dataframe(day_disp, use_container_width=True)

# Tab: Archived Appointments
with tabs[1]:
    bookings = load_bookings()
    archive = bookings[bookings["Appointment Date"] <= yesterday]

    st.subheader("📂 Appointment Archive")
    if archive.empty:
        st.info("No archived appointments.")
    else:
        disp = archive.sort_values("Appointment Date", ascending=False).reset_index(drop=True)
        disp.index += 1
        st.dataframe(disp[["Appointment Date", "Patient Name", "Appointment Time (manual)", "Payment"]], use_container_width=True)

# ---------- Sidebar: Add Appointment ----------
st.sidebar.header("Add Appointment")
picked_date = st.sidebar.date_input("Appointment Date", value=date.today())
appt_name = st.sidebar.text_input("Patient Name")
appt_time = st.sidebar.text_input("Appointment Time (manual)")
payment = st.sidebar.text_input("Payment (optional)")

if st.sidebar.button("💾 Save Appointment"):
    if not appt_name:
        st.sidebar.error("Patient name required.")
    elif not appt_time:
        st.sidebar.error("Appointment time required.")
    else:
        record = {
            "Patient Name": appt_name.strip(),
            "Appointment Date": picked_date.isoformat(),
            "Appointment Time (manual)": appt_time.strip(),
            "Payment": payment.strip()
        }
        append_booking(record)
        st.sidebar.success("Appointment saved successfully.")
        safe_rerun()
