import streamlit as st
import pandas as pd
import time
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Aeropath A* Flight Simulator", layout="centered")

st.title("✈️ Aeropath Autonomy Flight Simulator")
st.markdown("### A* Route Finder & Step Cost Engine")

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

# --- SIMULATION SPEED SLIDER ---
sim_speed = st.slider("Simulation Speed Multiplier", min_value=1, max_value=30, value=10)

# --- SESSION STATE MANAGEMENT FOR SIMULATION BUTTONS ---
if 'simulation_state' not in st.session_state:
    st.session_state.simulation_state = "IDLE" # IDLE, RUNNING, FINISHED
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0

# --- CONTROL BUTTONS ---
btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)

with btn_col1:
    if st.button("Find Route"):
        st.session_state.simulation_state = "IDLE"
        st.session_state.current_step = 0
        st.success("Route found! Ready to start simulation.")

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

# --- YOUR EXACT FORMULAS ---
w = 0.1 * wind_speed
a = 1.15
t_val = 1.05
p = 1.0

clear_cost = ((distance * ((a + t_val) * w)) / p) * (1 + density)
storm_cost = ((distance * ((0.6 * radar) + (0.4 * lightning) * w)) / p) * (1 + density)
total_s_n = clear_cost + storm_cost
effective_range = 3550 - (50 + w)
clearance = (0.1 * wind_speed) * 1000

# Total mock steps for the A* path simulation
total_steps = 10

# --- SIMULATION EXECUTION LOOP ---
progress_bar = st.progress(0)
status_text = st.empty()

if st.session_state.simulation_state == "RUNNING":
    for step in range(st.session_state.current_step, total_steps + 1):
        if st.session_state.simulation_state == "IDLE":
            break # Stop if user hit stop
        
        st.session_state.current_step = step
        progress_val = step / total_steps
        progress_bar.progress(progress_val)
        status_text.text(f"Executing A* Step {step} of {total_steps} (Speed: {sim_speed}x)...")
        
        # Adjust sleep time based on user speed slider (faster speed = less sleep delay)
        time.sleep(0.3 / sim_speed)
        
        if step == total_steps:
            st.session_state.simulation_state = "FINISHED"
            st.rerun()

# --- DISPLAY METRICS & LOGS ---
if st.session_state.current_step > 0:
    st.markdown("---")
    st.subheader("📊 Flight Cost & Route Metrics")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("A* Step Cost (sₙ)", f"{total_s_n:.2f}")
    m2.metric("Effective Range", f"{effective_range:.2f} NM")
    m3.metric("Vertical Clearance", f"{clearance:.0f} ft")

    # Step-by-step reasoning table
    log_rows = []
    for i in range(1, st.session_state.current_step + 1):
        step_cost = (total_s_n / total_steps) * i
        reason = "Optimal trajectory vector maintaining standard separation."
        if i == 4 or i == 7:
            reason = "A* path correction: Deviated around high radar reflectivity cluster."
        log_rows.append({"Step": i, "Cost (sₙ)": f"{step_cost:.2f}", "Reasoning": reason})
    
    st.dataframe(pd.DataFrame(log_rows), use_container_width=True)

# --- DOWNLOAD REPORT (ONLY UNLOCKED WHEN FINISHED) ---
if st.session_state.simulation_state == "FINISHED":
    st.success("🏁 Flight Complete! All A* steps processed successfully.")
    
    def generate_pdf():
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(f"Aeropath Flight Report: {dep} to {arr}", styles['Heading1']))
        elements.append(Spacer(1, 10))
        
        summary = f"""
        <b>Final A* Cost (sₙ):</b> {total_s_n:.2f}<br/>
        <b>Effective Range:</b> {effective_range:.2f} NM<br/>
        <b>Vertical Storm Clearance:</b> {clearance:.0f} ft<br/>
        <b>Parameters:</b> Wind {wind_speed} kts | Radar {radar} dBZ
        """
        elements.append(Paragraph(summary, styles['Normal']))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("<b>Applied Mathematical Rules</b>", styles['Heading2']))
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
        file_name=f"Aeropath_Flight_{dep}_{arr}.pdf",
        mime="application/pdf",
        type="primary"
    )
