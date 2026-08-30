"""
PharmaShield AI — Live Dashboard

Streamlit dashboard demonstrating the full pipeline: shipment
simulation, risk assessment (TTS + ML prediction), recovery hub
selection, and automated SAP workflow execution.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import time
import folium
from streamlit_folium import st_folium

from simulator.generate_shipment import generate_shipment_data, SAFE_TEMP_MAX, SAFE_TEMP_MIN
from engine.risk_assessment import assess_shipment
from engine.hub_selector import COLD_STORAGE_HUBS

st.set_page_config(page_title="PharmaShield AI", layout="wide")

# ---------- Session state initialization ----------
if "shipment_df" not in st.session_state:
    st.session_state.shipment_df = None
if "current_index" not in st.session_state:
    st.session_state.current_index = 5
if "autoplay" not in st.session_state:
    st.session_state.autoplay = False
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


RISK_COLORS = {
    "SAFE": "green",
    "WARNING": "orange",
    "CRITICAL": "red",
    "SPOILED": "black",
}


def build_map(current_lat, current_lon, risk_level, recovery_hub=None):
    m = folium.Map(location=[current_lat, current_lon], zoom_start=9)

    # Shipment marker
    folium.Marker(
        [current_lat, current_lon],
        popup=f"Shipment - Risk: {risk_level}",
        icon=folium.Icon(color=RISK_COLORS.get(risk_level, "blue"), icon="truck", prefix="fa"),
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
            color="red", weight=3, dash_array="5",
        ).add_to(m)

    return m


# ---------- Sidebar controls ----------
st.sidebar.title("PharmaShield AI")
st.sidebar.subheader("Scenario Setup")

if st.sidebar.button("Healthy Shipment"):
    load_scenario(None, 1.0, "Healthy Shipment")

if st.sidebar.button("Mild Cooling Failure"):
    load_scenario(2, 1.0, "Mild Cooling Failure")

if st.sidebar.button("Severe Cooling Failure"):
    load_scenario(2, 1.8, "Severe Cooling Failure")

st.sidebar.divider()
st.sidebar.subheader("Playback")

col1, col2 = st.sidebar.columns(2)
next_clicked = col1.button("Next Reading ▶")
reset_clicked = col2.button("Reset ⟲")

autoplay_toggle = st.sidebar.checkbox("Auto-play", value=st.session_state.autoplay)
st.session_state.autoplay = autoplay_toggle

# ---------- Main area ----------
st.title("🧊 PharmaShield AI — Cold-Chain Monitoring")

if st.session_state.shipment_df is None:
    st.info("👈 Choose a scenario from the sidebar to begin.")
    st.stop()

df = st.session_state.shipment_df

if reset_clicked:
    st.session_state.current_index = 5
    st.session_state.reroute_triggered_at_index = None
    st.session_state.frozen_recovery = None
    st.session_state.frozen_assessment = None

if next_clicked and st.session_state.current_index < len(df) - 1:
    st.session_state.current_index += 1

st.subheader(f"Scenario: {st.session_state.scenario}")
st.caption(f"Reading {st.session_state.current_index + 1} of {len(df)}")

visible_data = df.iloc[: st.session_state.current_index + 1]
assessment = assess_shipment(visible_data)

if st.session_state.reroute_triggered_at_index is None and assessment["ml_breach_predicted"]:
    st.session_state.reroute_triggered_at_index = st.session_state.current_index
    st.session_state.frozen_recovery = assessment["recovery_recommendation"]

rerouted = st.session_state.reroute_triggered_at_index is not None

# --- Position + travel calculation (must happen before anything displays it) ---
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

    # Freeze condition (temp/humidity/TTS/risk) the moment it arrives
    if arrived_at_hub and st.session_state.frozen_assessment is None:
        st.session_state.frozen_assessment = assessment
        st.session_state.frozen_humidity = visible_data.iloc[-1]["humidity"]

    if st.session_state.frozen_assessment is not None:
        assessment = st.session_state.frozen_assessment
else:
    latest_row = visible_data.iloc[-1]
    recovery_hub = assessment["recovery_recommendation"]["hub"] if assessment["recovery_recommendation"] else None
    arrived_at_hub = False

# --- Metric cards ---
if st.session_state.frozen_humidity is not None:
    current_humidity = st.session_state.frozen_humidity
else:
    current_humidity = visible_data.iloc[-1]["humidity"]
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Current Temperature", f"{assessment['current_temperature']} °C")
m2.metric("Current Humidity", f"{current_humidity:.1f} %")
m3.metric("TTS Remaining", f"{assessment['tts_remaining_hours']} hrs", f"{assessment['percent_remaining']}%")
m4.metric("Risk Level", assessment["rule_based_risk_level"])
m5.metric("ML Breach Probability", f"{assessment['ml_breach_probability'] * 100:.1f}%")

# --- Alert banner ---
if rerouted:
    hub = st.session_state.frozen_recovery["hub"]
    dist = st.session_state.frozen_recovery["distance_km"]
    if arrived_at_hub:
        st.warning(f"✅ ARRIVED at **{hub['name']}** — shipment secured. Load: {hub['current_load']}/{hub['capacity']}")
    else:
        st.warning(f"🔀 REROUTING to **{hub['name']}** ({dist} km) — shipment in transit to recovery hub...")
elif assessment["needs_recovery_action"]:
    st.error("⚠️ RISK DETECTED — evaluating recovery options...")
else:
    st.success("✅ Shipment within safe parameters.")

# --- Map ---
lat_val = latest_row["lat"] if not rerouted else latest_row.lat
lon_val = latest_row["lon"] if not rerouted else latest_row.lon
map_obj = build_map(lat_val, lon_val, assessment["rule_based_risk_level"], recovery_hub)
st_folium(map_obj, width=1200, height=450)

# ---------- Auto-play loop ----------
if st.session_state.autoplay and st.session_state.current_index < len(df) - 1:
    time.sleep(1.5)
    st.session_state.current_index += 1
    st.rerun()