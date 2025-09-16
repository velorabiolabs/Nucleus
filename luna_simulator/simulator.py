from __future__ import annotations
import argparse, random, time, json
from paho.mqtt.client import Client
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--broker", default="127.0.0.1"); ap.add_argument("--port", type=int, default=1883)
    args = ap.parse_args()
    client = Client(client_id="luna-simulator"); client.connect(args.broker, args.port, keepalive=30)
    def on_message(client, userdata, msg):
        topic = msg.topic; payload = msg.payload.decode("utf-8", errors="replace")
        if topic == "luna/cmd/start_task":
            try: print("[Luna] START", json.loads(payload))
            except Exception: print("[Luna] START (raw)", payload)
            client.publish("luna/telemetry/status", "RUNNING")
        elif topic == "luna/cmd/stop_task":
            print("[Luna] STOP"); client.publish("luna/telemetry/status", "READY")
        elif topic == "luna/cmd/estop":
            print("[Luna] E-STOP!!!"); client.publish("luna/telemetry/status", "ERROR")
    client.on_message = on_message; client.subscribe("luna/cmd/#"); client.loop_start()
    try:
        while True:
            temp = round(24.0 + random.uniform(-0.5,1.5),2); hum = round(40.0 + random.uniform(-2.0,2.0),1)
            client.publish("luna/telemetry/temperature", str(temp)); client.publish("luna/telemetry/humidity", str(hum))
            time.sleep(1.5)
    except KeyboardInterrupt: pass
    finally: client.loop_stop(); client.disconnect()
if __name__ == "__main__": main()
