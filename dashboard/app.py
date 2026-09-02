"""
PharmaShield AI — Enterprise Live Dashboard

Streamlit dashboard demonstrating cold-chain shipment monitoring,
TTS calculation, ML breach prediction, recovery hub selection,
and real-time notification dispatch to hospital & recovery networks.
"""

import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import time
import folium
from streamlit_folium import st_folium
import requests

from simulator.generate_shipment import generate_shipment_data, SAFE_TEMP_MAX, SAFE_TEMP_MIN
from engine.risk_assessment import assess_shipment
from engine.hub_selector import COLD_STORAGE_HUBS
from engine.state_bridge import broadcast_shipment_state
from engine.agents import Orchestrator, read_audit_log

st.set_page_config(
    page_title="PharmaShield AI — Enterprise Dashboard",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Custom Enterprise Theme & CSS Injection ----------
CUSTOM_CSS = """
<style>
    /* Dark Theme Core Reset */
    .stApp {
        background-color: #0E1117;
        color: #E5E7EB;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Headers & Typography */
    h1, h2, h3, h4, h5, h6 {
        color: #F9FAFB !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }
    
    .brand-header {
        display: flex;
        align-items: center;
        gap: 12px;
        border-bottom: 1px solid #2A2E37;
        padding-bottom: 14px;
        margin-bottom: 20px;
    }
    
    .brand-title {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #38BDF8 0%, #2DD4BF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .brand-subtitle {
        font-size: 0.85rem;
        color: #9CA3AF;
        margin-top: -4px;
    }
    
    /* Container & Panel Styling */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #F9FAFB !important;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.82rem !important;
        color: #9CA3AF !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .hero-card {
        background-color: #1A1D23;
        border: 1px solid #2A2E37;
        border-radius: 10px;
        padding: 18px 22px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        margin-bottom: 14px;
        position: relative;
        overflow: hidden;
    }
    
    .hero-card-title {
        font-size: 0.8rem;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
    }
    
    .hero-card-value {
        font-size: 2.2rem;
        font-weight: 800;
        line-height: 1.1;
    }
    
    .hero-card-sub {
        font-size: 0.85rem;
        color: #6B7280;
        margin-top: 4px;
    }
    
    /* Status Badge Styles */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    
    .badge-safe {
        background-color: rgba(34, 197, 94, 0.15);
        color: #22C55E;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    
    .badge-warning {
        background-color: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    
    .badge-critical {
        background-color: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    .badge-spoiled {
        background-color: rgba(100, 116, 139, 0.15);
        color: #64748B;
        border: 1px solid rgba(100, 116, 139, 0.3);
    }
    
    /* Animated Micro-element: Status Dot Pulse */
    .status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
    }
    
    .dot-safe { background-color: #22C55E; box-shadow: 0 0 8px #22C55E; }
    .dot-warning { 
        background-color: #F59E0B; 
        box-shadow: 0 0 10px #F59E0B;
        animation: pulse-ring 1.8s infinite;
    }
    .dot-critical { 
        background-color: #EF4444; 
        box-shadow: 0 0 12px #EF4444;
        animation: pulse-ring 1.0s infinite;
    }
    .dot-spoiled { background-color: #64748B; }
    
    @keyframes pulse-ring {
        0% { transform: scale(0.95); opacity: 1; }
        50% { transform: scale(1.3); opacity: 0.6; }
        100% { transform: scale(0.95); opacity: 1; }
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #111418 !important;
        border-right: 1px solid #2A2E37;
    }
    
    .stButton > button {
        background-color: #1A1D23;
        color: #E5E7EB;
        border: 1px solid #2A2E37;
        border-radius: 6px;
        transition: all 0.2s ease;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        border-color: #2DD4BF;
        color: #2DD4BF;
        background-color: rgba(45, 212, 191, 0.05);
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------- Session state initialization ----------
if "shipment_df" not in st.session_state:
    st.session_state.shipment_df = None
if "current_index" not in st.session_state:
    st.session_state.current_index = 5
if "autoplay" not in st.session_state:
    st.session_state.autoplay = False
if "_reset_live_mode" not in st.session_state:
    st.session_state._reset_live_mode = False    
if "scenario" not in st.session_state:
    st.session_state.scenario = None
if "reroute_triggered_at_index" not in st.session_state:
    st.session_state.reroute_triggered_at_index = None
if "frozen_recovery" not in st.session_state:
    st.session_state.frozen_recovery = None    
if "frozen_assessment" not in st.session_state:
    st.session_state.frozen_assessment = None    
if "frozen_humidity" not in st.session_state:
    st.session_state.frozen_humidity = None    
if "live_history" not in st.session_state:
    st.session_state.live_history = []
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator()
if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = None
if "approved_reroutes" not in st.session_state:
    st.session_state.approved_reroutes = {}    
if st.session_state._reset_live_mode:
    st.session_state["use_live_hardware_feed"] = False
    st.session_state._reset_live_mode = False

def load_scenario(failure_start_index, failure_severity, scenario_name):
    df = generate_shipment_data(
        failure_start_index=failure_start_index,
        failure_severity=failure_severity,
        points_per_leg=9,
    )
    st.session_state.shipment_df = df
    st.session_state.current_index = 5
    st.session_state.scenario = scenario_name
    st.session_state.autoplay = False
    st.session_state.reroute_triggered_at_index = None
    st.session_state.frozen_recovery = None
    st.session_state.frozen_assessment = None
    st.session_state.frozen_humidity = None
    st.session_state._reset_live_mode = True


RISK_COLORS = {
    "SAFE": "#22C55E",
    "WARNING": "#F59E0B",
    "CRITICAL": "#EF4444",
    "SPOILED": "#64748B",
}

MAP_MARKER_COLORS = {
    "SAFE": "green",
    "WARNING": "orange",
    "CRITICAL": "red",
    "SPOILED": "gray",
}

def fetch_live_reading():
    try:
        response = requests.get(LIVE_SERVER_URL, timeout=2)
        data = response.json()
        if data.get("temperature") is not None:
            return data
    except Exception:
        pass
    return None

def dispatch_sap_sto(shipment_id, origin_hub, destination_hub, reason, tts_remaining_hours, risk_level, distance_km):
    try:
        requests.post(
            "http://127.0.0.1:5000/api/sap/stock-transport-order",
            json={
                "shipment_id": shipment_id,
                "origin_hub": origin_hub,
                "destination_hub": destination_hub,
                "reason": reason,
                "tts_remaining_hours": tts_remaining_hours,
                "risk_level": risk_level,
                "distance_km": distance_km
            },
            timeout=2
        )
    except Exception as e:
        print(f"Mock SAP server unreachable: {e}")

def build_map(current_lat, current_lon, risk_level, recovery_hub=None):
    m = folium.Map(location=[current_lat, current_lon], zoom_start=9)

    # Shipment marker
    folium.Marker(
        [current_lat, current_lon],
        popup=f"Shipment #SHP-9942 - Risk: {risk_level}",
        icon=folium.Icon(color=MAP_MARKER_COLORS.get(risk_level, "blue"), icon="truck", prefix="fa"),
    ).add_to(m)

    # All cold-storage hubs
    for hub in COLD_STORAGE_HUBS:
        color = "gray" if not hub["operational"] else ("red" if hub["current_load"] >= hub["capacity"] else "blue")
        folium.Marker(
            [hub["lat"], hub["lon"]],
            popup=f"{hub['name']} ({hub['current_load']}/{hub['capacity']})",
            icon=folium.Icon(color=color, icon="snowflake-o", prefix="fa"),
        ).add_to(m)

    # Highlight recommended recovery hub with a line
    if recovery_hub:
        folium.PolyLine(
            locations=[[current_lat, current_lon], [recovery_hub["lat"], recovery_hub["lon"]]],
            color="#EF4444", weight=3, dash_array="5",
        ).add_to(m)

    return m


# ---------- Sidebar controls ----------
st.sidebar.title("PharmaShield AI")
st.sidebar.caption("Cold-Chain Operations Portal")
st.sidebar.divider()

st.sidebar.subheader("Scenario Selector")

if st.sidebar.button("🟢 Healthy Shipment", use_container_width=True):
    load_scenario(None, 1.0, "Healthy Shipment")

if st.sidebar.button("🟡 Mild Cooling Failure", use_container_width=True):
    load_scenario(2, 1.0, "Mild Cooling Failure")

if st.sidebar.button("🔴 Severe Cooling Failure", use_container_width=True):
    load_scenario(2, 1.8, "Severe Cooling Failure")

st.sidebar.divider()
st.sidebar.subheader("Telemetry Feed")
live_mode = st.sidebar.checkbox("Use Live ESP32 Hardware Feed", value=False, key="use_live_hardware_feed")
LIVE_SERVER_URL = "http://127.0.0.1:5001/api/live-reading"

st.sidebar.divider()
st.sidebar.subheader("Simulation Controls")

col1, col2 = st.sidebar.columns(2)
next_clicked = col1.button("Next ▶", use_container_width=True)
reset_clicked = col2.button("Reset ⟲", use_container_width=True)

autoplay_toggle = st.sidebar.checkbox("Auto-play Simulation", value=st.session_state.autoplay)
st.session_state.autoplay = autoplay_toggle


# ---------- Main Header ----------
st.markdown("""
<div class="brand-header">
    <div>
        <h1 class="brand-title">🧊 PharmaShield AI</h1>
        <div class="brand-subtitle">Enterprise Pharmaceutical Cold-Chain Monitoring & Recovery Engine</div>
    </div>
</div>
""", unsafe_allow_html=True)


if live_mode:
    reading = fetch_live_reading()
    if reading is None:
        st.warning("Waiting for live sensor data... Make sure the ESP32 and live_data_server.py are running.")
        st.stop()

    st.session_state.live_history.append({
        "timestamp": reading["timestamp"],
        "temperature": reading["temperature"],
        "humidity": reading["humidity"],
        "lat": reading["lat"] if reading["lat"] else 19.0760,
        "lon": reading["lon"] if reading["lon"] else 72.8777,
        "waypoint_index": 0,
    })

    st.session_state.live_history = st.session_state.live_history[-30:]

    if len(st.session_state.live_history) < 4:
        st.info(f"Collecting live readings... ({len(st.session_state.live_history)}/4 needed to start prediction)")
        time.sleep(2)
        st.rerun()

    df = pd.DataFrame(st.session_state.live_history)
    st.session_state.current_index = len(df) - 1
    st.session_state.scenario = "🔴 LIVE Hardware Feed"

else:
    if st.session_state.shipment_df is None:
        load_scenario(None, 1.0, "Healthy Shipment")
    df = st.session_state.shipment_df

if reset_clicked:
    st.session_state.current_index = 5
    st.session_state.reroute_triggered_at_index = None
    st.session_state.frozen_recovery = None
    st.session_state.frozen_assessment = None
    st.session_state.frozen_humidity = None

if next_clicked and st.session_state.current_index < len(df) - 1:
    st.session_state.current_index += 1

visible_data = df.iloc[: st.session_state.current_index + 1]
pipeline_result = st.session_state.orchestrator.run(visible_data)
assessment = pipeline_result["assessment"]

if (pipeline_result["approval_state"] is not None
        and st.session_state.pending_approval is None
        and st.session_state.reroute_triggered_at_index is None):
    st.session_state.pending_approval = pipeline_result["approval_state"]["decision"]


    st.session_state.reroute_triggered_at_index = st.session_state.current_index
    st.session_state.frozen_recovery = assessment["recovery_recommendation"]

    if assessment["recovery_recommendation"] and assessment["recovery_recommendation"].get("hub"):
        target_hub = assessment["recovery_recommendation"]["hub"]
        dist = assessment["recovery_recommendation"].get("distance_km", 0.0)
        dispatch_sap_sto(
            shipment_id="SHP-9942",
            origin_hub="Origin Cold Transit (MH-12)",
            destination_hub=target_hub["name"],
            reason="COOLING_BREACH_EXCURSION",
            tts_remaining_hours=assessment["tts_remaining_hours"],
            risk_level=assessment["rule_based_risk_level"],
            distance_km=dist
        )

rerouted = st.session_state.reroute_triggered_at_index is not None

# --- Position + travel calculation ---
TRAVEL_STEPS_TO_HUB = 4

if rerouted:
    breach_row = df.iloc[st.session_state.reroute_triggered_at_index]
    hub = st.session_state.frozen_recovery["hub"]
    recovery_hub = hub

    steps_since_reroute = st.session_state.current_index - st.session_state.reroute_triggered_at_index
    travel_frac = min(1.0, steps_since_reroute / TRAVEL_STEPS_TO_HUB)

    interpolated_lat = breach_row["lat"] + (hub["lat"] - breach_row["lat"]) * travel_frac
    interpolated_lon = breach_row["lon"] + (hub["lon"] - breach_row["lon"]) * travel_frac

    class _Pos:
        lat = interpolated_lat
        lon = interpolated_lon
    latest_row = _Pos()
    arrived_at_hub = travel_frac >= 1.0

    if arrived_at_hub and st.session_state.frozen_assessment is None:
        st.session_state.frozen_assessment = assessment
        st.session_state.frozen_humidity = visible_data.iloc[-1]["humidity"]

    if st.session_state.frozen_assessment is not None:
        assessment = st.session_state.frozen_assessment
else:
    latest_row = visible_data.iloc[-1]
    recovery_hub = assessment["recovery_recommendation"]["hub"] if assessment["recovery_recommendation"] else None
    arrived_at_hub = False

if st.session_state.frozen_humidity is not None:
    current_humidity = st.session_state.frozen_humidity
else:
    current_humidity = visible_data.iloc[-1]["humidity"]

# ---------- Broadcast State to Bridge ----------
lat_val = latest_row["lat"] if not rerouted else latest_row.lat
lon_val = latest_row["lon"] if not rerouted else latest_row.lon

broadcast_shipment_state(
    scenario_name=st.session_state.scenario,
    reading_index=st.session_state.current_index,
    total_readings=len(df),
    lat=lat_val,
    lon=lon_val,
    temperature=assessment["current_temperature"],
    humidity=current_humidity,
    assessment=assessment,
    rerouted=rerouted,
    recovery_hub=recovery_hub,
    arrived_at_hub=arrived_at_hub
)


# ---------- Hero Metric Header & Cards ----------
risk_lvl = assessment["rule_based_risk_level"]
badge_class = f"badge-{risk_lvl.lower()}"
dot_class = f"dot-{risk_lvl.lower()}"

c_hero1, c_hero2, c_hero3 = st.columns([1.5, 1.5, 2.5])

with c_hero1:
    st.markdown(f"""
    <div class="hero-card">
        <div class="hero-card-title">Current Risk Status</div>
        <div class="status-badge {badge_class}">
            <span class="status-dot {dot_class}"></span>
            {risk_lvl}
        </div>
        <div class="hero-card-sub">Scenario: {st.session_state.scenario}</div>
    </div>
    """, unsafe_allow_html=True)

with c_hero2:
    st.markdown(f"""
    <div class="hero-card">
        <div class="hero-card-title">TTS Remaining</div>
        <div class="hero-card-value" style="color: {'#EF4444' if assessment['percent_remaining'] < 15 else '#2DD4BF'};">
            {assessment['tts_remaining_hours']} <span style="font-size: 1.1rem; font-weight: 500;">hrs</span>
        </div>
        <div class="hero-card-sub">{assessment['percent_remaining']}% shelf-life budget</div>
    </div>
    """, unsafe_allow_html=True)
if st.session_state.pending_approval is not None:
    hub = st.session_state.pending_approval["hub"]
    st.warning(f"🤖 Compliance Agent requests approval: reroute to **{hub['name']}** ({st.session_state.pending_approval['distance_km']} km)?")
    col1, col2 = st.columns(2)
    if col1.button("✅ Approve Reroute", key="approve_btn"):
        st.session_state.orchestrator.compliance.record_approval("Operator", st.session_state.pending_approval)
        st.session_state.reroute_triggered_at_index = st.session_state.current_index
        st.session_state.frozen_recovery = {"hub": hub, "distance_km": st.session_state.pending_approval["distance_km"]}
        st.session_state.pending_approval = None
        st.rerun()
    if col2.button("❌ Reject", key="reject_btn"):
        st.session_state.orchestrator.compliance.record_rejection("Operator", st.session_state.pending_approval)
        st.session_state.pending_approval = None
        st.rerun()
with c_hero3:
    if rerouted:
        hub = st.session_state.frozen_recovery["hub"]
        dist = st.session_state.frozen_recovery["distance_km"]
        if arrived_at_hub:
            st.markdown(f"""
            <div class="hero-card" style="border-color: #22C55E;">
                <div class="hero-card-title" style="color: #22C55E;">✅ Recovery Completed</div>
                <div style="font-size: 1.3rem; font-weight: 700; color: #F9FAFB;">Arrived at {hub['name']}</div>
                <div class="hero-card-sub">Shipment secured in temperature-controlled storage.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="hero-card" style="border-color: #F59E0B;">
                <div class="hero-card-title" style="color: #F59E0B;">🔀 Active Reroute In-Progress</div>
                <div style="font-size: 1.3rem; font-weight: 700; color: #F9FAFB;">In Transit to {hub['name']} ({dist} km)</div>
                <div class="hero-card-sub">SAP STO Dispatched • Hub Notified</div>
            </div>
            """, unsafe_allow_html=True)
    elif assessment["needs_recovery_action"]:
        st.markdown("""
        <div class="hero-card" style="border-color: #EF4444;">
            <div class="hero-card-title" style="color: #EF4444;">⚠️ Risk Triggered</div>
            <div style="font-size: 1.3rem; font-weight: 700; color: #F9FAFB;">Evaluating Nearest Cold Hub...</div>
            <div class="hero-card-sub">ML Breach Engine actively calculating recovery trajectory.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="hero-card" style="border-color: #22C55E;">
            <div class="hero-card-title" style="color: #22C55E;">✅ Optimal Telemetry</div>
            <div style="font-size: 1.3rem; font-weight: 700; color: #F9FAFB;">Shipment Operating Safely</div>
            <div class="hero-card-sub">All sensors within nominal cold-chain bounds (2.0°C - 8.0°C).</div>
        </div>
        """, unsafe_allow_html=True)


# ---------- Secondary Metric Cards ----------
m1, m2, m3, m4 = st.columns(4)
m1.metric("Temperature", f"{assessment['current_temperature']} °C", delta=None)
m2.metric("Humidity", f"{current_humidity:.1f} %", delta=None)
m3.metric("ML Breach Probability", f"{assessment['ml_breach_probability'] * 100:.1f}%")
m4.metric("Telemetry Index", f"{st.session_state.current_index + 1} / {len(df)}")


# ---------- Map Section ----------
st.subheader("📍 Live Shipment Location & Cold-Storage Network")
map_obj = build_map(lat_val, lon_val, assessment["rule_based_risk_level"], recovery_hub)
st_folium(map_obj, width=1300, height=480)

with st.expander("🤖 Agent Activity Log (Audit Trail)"):
    log_entries = read_audit_log()
    for entry in reversed(log_entries[-15:]):
        st.text(f"[{entry['timestamp'][:19]}] {entry['agent']} → {entry['action']}")

# ---------- Auto-play loop ----------
if st.session_state.autoplay and st.session_state.current_index < len(df) - 1:
    time.sleep(1.5)
    st.session_state.current_index += 1
    st.rerun()

if live_mode:
    time.sleep(3)
    st.rerun()
