# agents/passenger_agent.py
import json
from datetime import datetime
from collections import defaultdict

class PassengerTrackingAgent:
    """AI Agent for tracking passengers in vehicle"""
    
    def __init__(self):
        self.vehicle_occupancy = defaultdict(int)  # bus_id -> current count
        self.active_passengers = {}  # passenger_id -> {entry_time, entry_location, bus_id}
        self.passenger_history = []  # Complete history of all passengers
        self.entry_exit_logs = []  # All entry/exit events
        
    def process_entry(self, passenger, location, bus_id):
        """Process passenger entry into vehicle"""
        passenger_id = passenger.get("passenger_id")
        passenger_name = passenger.get("name")
        timestamp = datetime.now().isoformat()
        
        # Update occupancy
        self.vehicle_occupancy[bus_id] += 1
        
        # Store active passenger
        self.active_passengers[passenger_id] = {
            "passenger_id": passenger_id,
            "name": passenger_name,
            "passenger_type": passenger.get("passenger_type"),
            "entry_time": timestamp,
            "entry_location": location,
            "bus_id": bus_id,
            "status": "IN_VEHICLE"
        }
        
        # Log entry event
        entry_log = {
            "event_id": f"ENTRY_{timestamp}_{passenger_id}",
            "event_type": "ENTRY",
            "passenger_id": passenger_id,
            "passenger_name": passenger_name,
            "timestamp": timestamp,
            "location": location,
            "bus_id": bus_id,
            "vehicle_occupancy": self.vehicle_occupancy[bus_id]
        }
        self.entry_exit_logs.append(entry_log)
        
        return entry_log
    
    def process_exit(self, passenger_id, location, bus_id):
        """Process passenger exit from vehicle"""
        if passenger_id in self.active_passengers:
            passenger_info = self.active_passengers[passenger_id]
            timestamp = datetime.now().isoformat()
            
            # Calculate journey duration
            entry_time = datetime.fromisoformat(passenger_info["entry_time"])
            exit_time = datetime.fromisoformat(timestamp)
            journey_duration = str(exit_time - entry_time)
            
            # Update occupancy
            self.vehicle_occupancy[bus_id] = max(0, self.vehicle_occupancy[bus_id] - 1)
            
            # Create exit log
            exit_log = {
                "event_id": f"EXIT_{timestamp}_{passenger_id}",
                "event_type": "EXIT",
                "passenger_id": passenger_id,
                "passenger_name": passenger_info["name"],
                "entry_time": passenger_info["entry_time"],
                "entry_location": passenger_info["entry_location"],
                "exit_time": timestamp,
                "exit_location": location,
                "journey_duration": journey_duration,
                "bus_id": bus_id,
                "vehicle_occupancy": self.vehicle_occupancy[bus_id]
            }
            self.entry_exit_logs.append(exit_log)
            
            # Move to history
            self.passenger_history.append({
                **passenger_info,
                "exit_time": timestamp,
                "exit_location": location,
                "journey_duration": journey_duration
            })
            
            # Remove from active
            del self.active_passengers[passenger_id]
            
            return exit_log
        return None
    
    def get_current_occupancy(self, bus_id):
        """Get current number of passengers in vehicle"""
        return self.vehicle_occupancy.get(bus_id, 0)
    
    def get_active_passengers(self, bus_id):
        """Get list of passengers currently in vehicle"""
        return [p for p in self.active_passengers.values() if p["bus_id"] == bus_id]
    
    def get_occupancy_history(self, bus_id, limit=50):
        """Get recent occupancy history"""
        return [log for log in self.entry_exit_logs if log["bus_id"] == bus_id][-limit:]

class AlertAgent:
    """AI Agent for security alerts"""
    
    def __init__(self):
        self.alerts = []
        
    def generate_alert(self, alert_type, message, location, severity="HIGH", passenger_info=None):
        """Generate security alert"""
        alert = {
            "alert_id": f"ALT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": alert_type,
            "severity": severity,
            "message": message,
            "location": location,
            "passenger_info": passenger_info,
            "timestamp": datetime.now().isoformat(),
            "status": "ACTIVE",
            "gps_coordinates": {
                "lat": location.get("lat"),
                "lon": location.get("lon"),
                "address": location.get("address")
            }
        }
        self.alerts.append(alert)
        return alert
    
    def get_active_alerts(self):
        return [a for a in self.alerts if a["status"] == "ACTIVE"]
    
    def resolve_alert(self, alert_id):
        for alert in self.alerts:
            if alert["alert_id"] == alert_id:
                alert["status"] = "RESOLVED"
                alert["resolved_at"] = datetime.now().isoformat()
                return True
        return False
