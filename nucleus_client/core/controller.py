from __future__ import annotations
import json
from .mqtt_client import QtMqttBridge
class NucleusController:
    def __init__(self, mqtt: QtMqttBridge): self.mqtt = mqtt
    def start_task(self, name: str = "PCR", params: dict | None = None):
        payload = json.dumps({"name": name, "params": params or {}})
        self.mqtt.publish("luna/cmd/start_task", payload)
    def stop_task(self): self.mqtt.publish("luna/cmd/stop_task", "")
    def estop(self): self.mqtt.publish("luna/cmd/estop", "")
