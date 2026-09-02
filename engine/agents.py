"""
Multi-agent orchestration layer for PharmaShield AI.

Wraps the existing TTS, ML prediction, and hub-selection logic into
named agents with a shared audit trail. A human-approval gate sits
between the Decision Agent and SAP execution, satisfying the
Hackfest's "human-in-the-loop" and "audit logging" requirements.
"""

from datetime import datetime
import json
import os

from engine.risk_assessment import assess_shipment
from engine.hub_selector import select_recovery_hub

AUDIT_LOG_PATH = "engine/agent_audit_log.json"


def _log(agent_name, action, detail):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "action": action,
        "detail": detail,
    }
    log = []
    if os.path.exists(AUDIT_LOG_PATH):
        with open(AUDIT_LOG_PATH, "r") as f:
            try:
                log = json.load(f)
            except json.JSONDecodeError:
                log = []
    log.append(entry)
    log = log[-50:]  # keep the log small
    with open(AUDIT_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2, default=str)
    return entry


def read_audit_log():
    if not os.path.exists(AUDIT_LOG_PATH):
        return []
    with open(AUDIT_LOG_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


class SensingAgent:
    """Reads live shipment telemetry (temperature, humidity, GPS)."""
    def sense(self, sensor_df):
        latest = sensor_df.iloc[-1]
        _log("SensingAgent", "READ_TELEMETRY", {
            "temperature": float(latest["temperature"]),
            "humidity": float(latest["humidity"]),
        })
        return sensor_df


class PredictionAgent:
    """Runs TTS calculation and ML breach prediction."""
    def predict(self, sensor_df):
        result = assess_shipment(sensor_df)
        _log("PredictionAgent", "RISK_ASSESSMENT", {
            "risk_level": result["rule_based_risk_level"],
            "ml_breach_probability": result["ml_breach_probability"],
            "tts_remaining_hours": result["tts_remaining_hours"],
        })
        return result


class DecisionAgent:
    """Selects a recovery hub when risk warrants it."""
    def decide(self, assessment, lat, lon):
        if not assessment["needs_recovery_action"]:
            _log("DecisionAgent", "NO_ACTION_NEEDED", {"risk_level": assessment["rule_based_risk_level"]})
            return None
        recovery = select_recovery_hub(current_lat=lat, current_lon=lon)
        _log("DecisionAgent", "RECOVERY_RECOMMENDED", recovery)
        return recovery


class ComplianceAgent:
    """
    Human-in-the-loop gate. The recommended action is logged as PENDING
    until a human explicitly approves it - it is never auto-executed.
    """
    def request_approval(self, recovery_decision):
        _log("ComplianceAgent", "APPROVAL_REQUESTED", recovery_decision)
        return {"status": "PENDING_HUMAN_APPROVAL", "decision": recovery_decision}

    def record_approval(self, approved_by, recovery_decision):
        _log("ComplianceAgent", "APPROVED_BY_HUMAN", {
            "approved_by": approved_by,
            "decision": recovery_decision,
        })

    def record_rejection(self, rejected_by, recovery_decision):
        _log("ComplianceAgent", "REJECTED_BY_HUMAN", {
            "rejected_by": rejected_by,
            "decision": recovery_decision,
        })


class Orchestrator:
    """Runs the full agent pipeline in sequence: Sense -> Predict -> Decide -> (await approval)."""
    def __init__(self):
        self.sensing = SensingAgent()
        self.prediction = PredictionAgent()
        self.decision = DecisionAgent()
        self.compliance = ComplianceAgent()

    def run(self, sensor_df):
        self.sensing.sense(sensor_df)
        assessment = self.prediction.predict(sensor_df)
        latest = sensor_df.iloc[-1]
        recovery = self.decision.decide(assessment, latest["lat"], latest["lon"])

        approval_state = None
        if recovery is not None:
            approval_state = self.compliance.request_approval(recovery)

        return {"assessment": assessment, "recovery": recovery, "approval_state": approval_state}