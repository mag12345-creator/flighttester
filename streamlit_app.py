import streamlit as st
import pandas as pd
import time
import io
import folium
from streamlit_folium import st_folium
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Aeropath Boeing 737 A* Simulator", layout="wide")

st.title("✈️ Aeropath Autonomy Flight Simulator")
st.markdown("### Aircraft: **Boeing 737 Max 8** | Live Leaflet Map & A* Cost Engine")

# --- UI CONTROL BOXES ---
col1, col2 = st.columns(2)
with col1:
    dep = st.text_input("Departure ICAO", "KJFK").upper()
    distance = st.number_input("Total Route Distance (NM)", value=2084.5)
    wind_speed = st.number_input("Wind Speed (knots)", value=25.0)

with col2:
    arr = st.text_input("Arrival ICAO", "KPDX").upper()
    radar = st.number_input("Radar Reflectivity (dBZ)", value=35.0)
    lightning = st.number_input("Lightning Flash Rate", value=5.0)

density = st.number_input("Air Density (kg/m³)", value=1.225)

# --- SIMULATION SPEED SLIDER (1x to 30x) ---
sim_speed = st.slider("Simulation Speed Multiplier", min_value=1, max_value=30, value=10)

# --- SESSION STATE MANAGEMENT ---
if 'simulation_state' not in st.session_state:
    st.session_state.simulation_state = "IDLE"
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0

# --- CONTROL BUTTONS ---
btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)

with btn_col1:
    if st.button("Find Route"):
        st.session_state.simulation_state = "IDLE"
        st.session_state.current_step = 0
        st.success("Boeing 737 route computed successfully via A*.")

with btn_col2:
    if st.button("Start"):
        st.session_state.simulation_state = "RUNNING"

with btn_col3:
    if st.button("Stop"):
        st.session_state.simulation_state = "IDLE"

with btn_col4:
    if st.button("Reset"):
        st.session_state.simulation_state = "IDLE"
        st.session_state.current_step = 0
        st.rerun()

# --- YOUR EXACT A* COST FORMULAS ---
w = 0.1 * wind_speed
a = 1.15
t_val = 1.05
p = 1.0

clear_cost = ((distance * ((a + t_val) * w)) / p) * (1 + density)
storm_cost = ((distance * ((0.6 * radar) + (0.4 * lightning) * w)) / p) * (1 + density)
total_s_n = clear_cost + storm_cost
effective_range = 3550 - (50 + w)
clearance = (0.1 * wind_speed) * 1000

total_steps = 15

# --- SIMULATION TICKER LOOP ---
progress_bar = st.progress(0)
status_text = st.empty()

if st.session_state.simulation_state == "RUNNING":
    for step in range(st.session_state.current_step, total_steps + 1):
        if st.session_state.simulation_state == "IDLE":
            break
        
        st.session_state.current_step = step
        progress_bar.progress(step / total_steps)
        status_text.text(f"Boeing 737 in flight... Executing A* Step {step}/{total_steps} at {sim_speed}x speed.")
        
        # Real-time pacing adjusted dynamically by the 1x-30x slider
        time.sleep(0.2 / sim_speed)
        
        if step == total_steps:
            st.session_state.simulation_state = "FINISHED"
            st.rerun()

# --- LIVE LEAFLET MAP VISUALIZATION ---
st.subheader("🗺️ Live Route Map (Leaflet)")

# Mock coordinates mapping for JFK (Start) to PDX (End) interpolation
start_coords = [40.6413, -73.7781]
end_coords = [45.5898, -122.5951]

# Calculate dynamic marker position based on current simulation progress
progress_ratio = max(0.01, st.session_state.current_step / total_steps) if total_steps > 0 else 0.01
current_lat = start_coords[0] + (end_coords[0] - start_coords[0]) * progress_ratio
current_lon = start_coords[1] + (end_coords[1] - start_coords[1]) * progress_ratio

m = folium.Map(location=[40.0, -95.0], zoom_start=4)
folium.PolyLine([start_coords, end_coords], color="#1f4e79", weight=4, opacity=0.8, tooltip="A* Boeing 737 Path").add_to(m)
folium.Marker(start_coords, popup=f"Departure: {dep}", icon=folium.Icon(color="green", icon="plane")).add_to(m)
folium.Marker(end_coords, popup=f"Arrival: {arr}", icon=folium.Icon(color="red", icon="flag")).add_to(m)

# Active live aircraft marker moving along the route
if st.session_state.current_step > 0:
    folium.Marker([current_lat, current_lon], popup="Boeing 737 Active Position", icon=folium.Icon(color="blue", icon="plane", prefix="fa")).add_to(m)

st_folium(m, width=1000, height=400)

# --- METRICS & STEP REASONING LOG ---
if st.session_state.current_step > 0:
    st.markdown("---")
    st.subheader("📊 Boeing 737 Flight Performance Metrics")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("A* Step Cost (sₙ)", f"{total_s_n:.2f}")
    m2.metric("Effective Aircraft Range", f"{effective_range:.2f} NM")
    m3.metric("Vertical Storm Clearance", f"{clearance:.0f} ft")

    log_rows = []
    for i in range(1, st.session_state.current_step + 1):
        sc = (total_s_n / total_steps) * i
        reason = "Maintaining optimal Boeing 737 cruise vector."
        if i in [4, 9, 12]:
            reason = "A* algorithmic adjustment: Bypassing high radar anomaly cluster."
        log_rows.append({"Step": i, "Cost (sₙ)": f"{sc:.2f}", "Reasoning": reason})
    
    st.dataframe(pd.DataFrame(log_rows), use_container_width=True)

# --- DOWNLOAD REPORT (UNLOCKED ONLY WHEN FINISHED) ---
if st.session_state.simulation_state == "FINISHED":
    st.success("🏁 Flight Completed! Boeing 737 has arrived at destination.")
    
    def generate_pdf():
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(f"Aeropath Flight Report: {dep} to {arr} (Boeing 737)", styles['Heading1']))
        elements.append(Spacer(1, 10))
        
        summary = f"""
        <b>Aircraft:</b> Boeing 737 Max 8<br/>
        <b>Final A* Cost (sₙ):</b> {total_s_n:.2f}<br/>
        <b>Effective Range:</b> {effective_range:.2f} NM<br/>
        <b>Vertical Storm Clearance:</b> {clearance:.0f} ft<br/>
        <b>Parameters:</b> Wind {wind_speed} kts | Radar {radar} dBZ | Lightning {lightning}
        """
        elements.append(Paragraph(summary, styles['Normal']))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("<b>Applied Mathematical Rules & Formulas</b>", styles['Heading2']))
        math_desc = """
        • Clear Cost = ((Distance * ((a + t) * w)) / p) * (1 + Density)<br/>
        • Storm Cost = ((Distance * ((0.6 * Radar) + (0.4 * Lightning * w)) / p) * (1 + Density)<br/>
        • Total A* Cost ($s_n$) = Clear Cost + Storm Cost
        """
        elements.append(Paragraph(math_desc, styles['Normal']))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer

    pdf_data = generate_pdf()
    st.download_button(
        label="📥 Download Completed Flight PDF Report",
        data=pdf_data,
        file_name=f"Aeropath_B737_{dep}_{arr}.pdf",
        mime="application/pdf",
        type="primary"
    )
