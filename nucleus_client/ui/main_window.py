from __future__ import annotations
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QLineEdit, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QGridLayout, QGroupBox, QApplication
from ..core.mqtt_client import QtMqttBridge, MqttConfig
from ..core.controller import NucleusController
from ..core.logger import CsvLogger
class MainWindow(QWidget):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Nucleus — Luna Wireless (MQTT)"); self.resize(900, 520)
        self.broker_edit = QLineEdit("127.0.0.1"); self.port_edit = QLineEdit("1883")
        self.user_edit = QLineEdit(""); self.pass_edit = QLineEdit(""); self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.status_lbl = QLabel("Disconnected"); self.status_lbl.setStyleSheet("color:#b00;font-weight:bold;")
        self.connect_btn = QPushButton("Connect"); self.disconnect_btn = QPushButton("Disconnect"); self.disconnect_btn.setEnabled(False)
        self.temp_lbl = QLabel("-- °C"); self.hum_lbl = QLabel("-- %"); self.state_lbl = QLabel("UNKNOWN")
        self.start_btn = QPushButton("Start Task"); self.stop_btn = QPushButton("Stop Task"); self.estop_btn = QPushButton("E-Stop")
        for b in (self.start_btn, self.stop_btn, self.estop_btn): b.setEnabled(False)
        conn_box = QGroupBox("Broker"); grid = QGridLayout()
        grid.addWidget(QLabel("Host"),0,0); grid.addWidget(self.broker_edit,0,1)
        grid.addWidget(QLabel("Port"),0,2); grid.addWidget(self.port_edit,0,3)
        grid.addWidget(QLabel("User"),1,0); grid.addWidget(self.user_edit,1,1)
        grid.addWidget(QLabel("Pass"),1,2); grid.addWidget(self.pass_edit,1,3)
        grid.addWidget(QLabel("Status"),2,0); grid.addWidget(self.status_lbl,2,1,1,3)
        grid.addWidget(self.connect_btn,3,0,1,2); grid.addWidget(self.disconnect_btn,3,2,1,2); conn_box.setLayout(grid)
        telem_box = QGroupBox("Telemetry"); tl = QGridLayout()
        tl.addWidget(QLabel("Temperature"),0,0); tl.addWidget(self.temp_lbl,0,1)
        tl.addWidget(QLabel("Humidity"),1,0); tl.addWidget(self.hum_lbl,1,1)
        tl.addWidget(QLabel("Device State"),2,0); tl.addWidget(self.state_lbl,2,1); telem_box.setLayout(tl)
        ctl_box = QGroupBox("Controls"); hl = QHBoxLayout(); hl.addWidget(self.start_btn); hl.addWidget(self.stop_btn); hl.addWidget(self.estop_btn); ctl_box.setLayout(hl)
        root = QVBoxLayout(); root.addWidget(conn_box); root.addWidget(telem_box); root.addWidget(ctl_box); root.addStretch(1); self.setLayout(root)
        self.mqtt = QtMqttBridge(); self.controller = NucleusController(self.mqtt); self.logger = CsvLogger(Path("./data/logs"))
        self.connect_btn.clicked.connect(self._do_connect); self.disconnect_btn.clicked.connect(self._do_disconnect)
        self.start_btn.clicked.connect(lambda: self.controller.start_task("PCR", {"cycles":30}))
        self.stop_btn.clicked.connect(self.controller.stop_task); self.estop_btn.clicked.connect(self.controller.estop)
        self.mqtt.connected.connect(self._on_connected); self.mqtt.disconnected.connect(self._on_disconnected)
        self.mqtt.telemetry.connect(self._on_telemetry); self.mqtt.error.connect(self._on_error)
    def closeEvent(self, event):
        try: self.logger.close(); self.mqtt.disconnect()
        finally: return super().closeEvent(event)
    def _do_connect(self):
        host = self.broker_edit.text().strip(); port = int(self.port_edit.text().strip() or 1883)
        user = self.user_edit.text().strip(); pw = self.pass_edit.text()
        cfg = MqttConfig(host=host, port=port, username=user, password=pw, use_tls=(port==8883))
        self.mqtt.connect(cfg); self.connect_btn.setEnabled(False)
    def _do_disconnect(self): self.mqtt.disconnect()
    def _on_connected(self):
        self.status_lbl.setText("Connected"); self.status_lbl.setStyleSheet("color:#080;font-weight:bold;")
        for b in (self.start_btn, self.stop_btn, self.estop_btn, self.disconnect_btn): b.setEnabled(True)
    def _on_disconnected(self):
        self.status_lbl.setText("Disconnected"); self.status_lbl.setStyleSheet("color:#b00;font-weight:bold;"); self.connect_btn.setEnabled(True)
        for b in (self.start_btn, self.stop_btn, self.estop_btn, self.disconnect_btn): b.setEnabled(False)
    def _on_telemetry(self, topic: str, payload: str):
        self.logger.log(topic, payload)
        if topic.endswith("temperature"): self.temp_lbl.setText(f"{payload} °C")
        elif topic.endswith("humidity"): self.hum_lbl.setText(f"{payload} %")
        elif topic.endswith("status"): self.state_lbl.setText(payload)
    def _on_error(self, msg: str): self.status_lbl.setText(msg); self.status_lbl.setStyleSheet("color:#d80;font-weight:bold;")
def run():
    import sys
    app = QApplication(sys.argv); win = MainWindow(); win.show(); sys.exit(app.exec())
