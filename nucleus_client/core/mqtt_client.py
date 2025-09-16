from __future__ import annotations
import threading, queue
from dataclasses import dataclass
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from paho.mqtt.client import Client as MQTTClient, MQTTMessage

@dataclass
class MqttConfig:
    host: str
    port: int = 1883
    username: str = ""
    password: str = ""
    use_tls: bool = False

class QtMqttBridge(QObject):
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    telemetry = pyqtSignal(str, str)
    error = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self._client: Optional[MQTTClient] = None
        self._thread: Optional[threading.Thread] = None
        self._outgoing: "queue.Queue[tuple[str, bytes, int, bool]]" = queue.Queue()
        self._stop_evt = threading.Event()
    def connect(self, cfg: MqttConfig):
        if self._thread and self._thread.is_alive():
            self.error.emit("Already connected"); return
        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._run, args=(cfg,), daemon=True); self._thread.start()
    def disconnect(self):
        self._stop_evt.set()
        if self._client:
            try: self._client.disconnect()
            except Exception: pass
    def publish(self, topic: str, payload: bytes | str = b"", qos: int = 0, retain: bool = False):
        if isinstance(payload, str): payload = payload.encode("utf-8")
        self._outgoing.put((topic, payload, qos, retain))
    def _run(self, cfg: MqttConfig):
        try:
            self._client = MQTTClient(client_id="nucleus-client", clean_session=True, protocol=MQTTClient.MQTTv311)
            if cfg.username: self._client.username_pw_set(cfg.username, cfg.password or None)
            if cfg.use_tls: self._client.tls_set()
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_message = self._on_message
            self._client.connect(cfg.host, cfg.port, keepalive=30)
            self._client.loop_start()
            self._client.subscribe("luna/telemetry/#", qos=0)
            while not self._stop_evt.is_set():
                try:
                    topic, payload, qos, retain = self._outgoing.get(timeout=0.2)
                    self._client.publish(topic, payload=payload, qos=qos, retain=retain)
                except queue.Empty: pass
        except Exception as e:
            self.error.emit(f"MQTT error: {e}")
        finally:
            if self._client:
                try: self._client.loop_stop()
                except Exception: pass
            self.disconnected.emit()
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0: self.connected.emit()
        else: self.error.emit(f"MQTT connect failed: rc={rc}")
    def _on_disconnect(self, client, userdata, rc, properties=None):
        self.disconnected.emit()
    def _on_message(self, client, userdata, msg: MQTTMessage):
        try: payload = msg.payload.decode("utf-8", errors="replace")
        except Exception: payload = "<binary>"
        self.telemetry.emit(msg.topic, payload)
