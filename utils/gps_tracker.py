# utils/gps_tracker.py
import json
import os
from datetime import datetime
import random

class GPSTracker:
    def __init__(self):
        self.current_location = {
            "lat": 28.6139,
            "lon": 77.2090,
            "address": "Central Station, New Delhi",
            "timestamp": datetime.now().isoformat()
        }
        self.route_stops = [
            {"stop_id": "S001", "name": "Central Station", "lat": 28.6139, "lon": 77.2090},
            {"stop_id": "S002", "name": "City Mall", "lat": 28.6189, "lon": 77.2140},
            {"stop_id": "S003", "name": "University", "lat": 28.6239, "lon": 77.2190},
            {"stop_id": "S004", "name": "Downtown", "lat": 28.6289, "lon": 77.2240},
            {"stop_id": "S005", "name": "Hospital", "lat": 28.6339, "lon": 77.2290}
        ]
        self.current_stop_index = 0
    
    def get_current_location(self):
        """Get current GPS location"""
        # In production, this would read from actual GPS hardware
        # For demo, simulate movement along route
        import time
        self.current_stop_index = (self.current_stop_index + 0.01) % len(self.route_stops)
        idx = int(self.current_stop_index)
        
        current_stop = self.route_stops[idx]
        self.current_location = {
            "lat": current_stop["lat"],
            "lon": current_stop["lon"],
            "address": current_stop["name"],
            "stop_id": current_stop["stop_id"],
            "timestamp": datetime.now().isoformat()
        }
        return self.current_location
    
    def get_nearby_stops(self):
        """Get nearby stops"""
        return self.route_stops

class AlertManager:
    def __init__(self):
        self.alerts = []
        self.alert_history = []
        
    def generate_alert(self, alert_type, passenger_info, location, confidence=0.85):
        """Generate a security alert"""
        alert = {
            "alert_id": f"ALT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(100,999)}",
            "type": alert_type,
            "severity": "HIGH" if alert_type == "UNAUTHORIZED_ENTRY" else "MEDIUM",
            "timestamp": datetime.now().isoformat(),
            "location": location,
            "passenger": passenger_info,
            "confidence": confidence,
            "status": "ACTIVE",
            "message": self._get_alert_message(alert_type, passenger_info, location)
        }
        self.alerts.append(alert)
        self.alert_history.append(alert)
        return alert
    
    def _get_alert_message(self, alert_type, passenger_info, location):
        """Generate alert message"""
        if alert_type == "UNAUTHORIZED_ENTRY":
            return f"⚠️ ALERT: Unregistered person detected entering vehicle at {location.get('address', 'Unknown Location')}! Face confidence: {passenger_info.get('confidence', 0)*100:.1f}%"
        elif alert_type == "BLACKLISTED_ENTRY":
            return f"🚨 CRITICAL: Blacklisted person {passenger_info.get('name', 'Unknown')} detected entering at {location.get('address', 'Unknown Location')}! Security team notified."
        elif alert_type == "REGISTERED_ENTRY":
            return f"✅ INFO: Registered passenger {passenger_info.get('name', 'Unknown')} entered at {location.get('address', 'Unknown Location')}"
        return f"Alert at {location.get('address', 'Unknown Location')}"
    
    def get_active_alerts(self):
        """Get all active alerts"""
        return [a for a in self.alerts if a["status"] == "ACTIVE"]
    
    def resolve_alert(self, alert_id):
        """Resolve an alert"""
        for alert in self.alerts:
            if alert["alert_id"] == alert_id:
                alert["status"] = "RESOLVED"
                alert["resolved_at"] = datetime.now().isoformat()
                return True
        return False
