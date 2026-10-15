from flask import Flask, jsonify, render_template
import csv
import os
import random
import threading
import time
from datetime import datetime

app = Flask(__name__)

# data ruangan - ganti sesuai kondisi kampus masing-masing
rooms = [
    {"id": 1, "name": "R.105", "building": "Gedung FST Lantai 1", "ac_on": True,
     "power_watt": 850, "motion": True, "minutes_since_motion": 0,
     "wasted_minutes_today": 0, "capacity": 40},
    {"id": 2, "name": "Lab Basic Science", "building": "Gedung FST Lantai 1", "ac_on": True,
     "power_watt": 900, "motion": False, "minutes_since_motion": 35,
     "wasted_minutes_today": 35, "capacity": 30},
    {"id": 3, "name": "R.110", "building": "Gedung FST Lantai 1", "ac_on": True,
     "power_watt": 780, "motion": True, "minutes_since_motion": 2,
     "wasted_minutes_today": 0, "capacity": 35},
    {"id": 4, "name": "R.205", "building": "Gedung FST Lantai 2", "ac_on": False,
     "power_watt": 0, "motion": False, "minutes_since_motion": 120,
     "wasted_minutes_today": 0, "capacity": 35},
    {"id": 5, "name": "R.211 (Kuliah/Sidang)", "building": "Gedung FST Lantai 2", "ac_on": True,
     "power_watt": 1200, "motion": False, "minutes_since_motion": 58,
     "wasted_minutes_today": 58, "capacity": 60},
    {"id": 6, "name": "R.216", "building": "Gedung FST Lantai 2", "ac_on": True,
     "power_watt": 800, "motion": True, "minutes_since_motion": 5,
     "wasted_minutes_today": 0, "capacity": 40},
    {"id": 7, "name": "R.305", "building": "Gedung FST Lantai 3", "ac_on": True,
     "power_watt": 820, "motion": True, "minutes_since_motion": 0,
     "wasted_minutes_today": 0, "capacity": 40},
    {"id": 8, "name": "R.312", "building": "Gedung FST Lantai 3", "ac_on": True,
     "power_watt": 1500, "motion": False, "minutes_since_motion": 25,
     "wasted_minutes_today": 25, "capacity": 80},
    {"id": 9, "name": "R.317", "building": "Gedung FST Lantai 3", "ac_on": True,
     "power_watt": 870, "motion": True, "minutes_since_motion": 3,
     "wasted_minutes_today": 0, "capacity": 40},
]

ANOMALY_THRESHOLD_MINUTES = 20
# tarif PLN golongan P-1 (Oktober 2026); sesuaikan dengan golongan pelanggan gedung
TARIF_LISTRIK_PER_KWH = 1699.53

LOG_FILE = "alert_log.csv"

alert_log = []
data_lock = threading.Lock()


def log_alert(room, message):
    """Catat kejadian ke memori (untuk dashboard) dan ke CSV (riwayat permanen).
    Harus dipanggil di dalam `with data_lock`."""
    now = datetime.now()
    alert_log.insert(0, {
        "time": now.strftime("%H:%M:%S"),
        "room": room["name"],
        "building": room["building"],
        "message": message,
    })
    del alert_log[20:]

    file_baru = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if file_baru:
            writer.writerow(["timestamp", "room", "building", "message"])
        writer.writerow([now.isoformat(timespec="seconds"), room["name"], room["building"], message])


def get_room_status(room):
    if not room["ac_on"]:
        return "normal"
    if not room["motion"] and room["minutes_since_motion"] >= ANOMALY_THRESHOLD_MINUTES:
        return "anomaly"
    if not room["motion"] and room["minutes_since_motion"] >= 10:
        return "warning"
    return "normal"


def calculate_efficiency_score(room):
    observation_window = 480  # 8 jam operasional per hari
    wasted_ratio = min(room["wasted_minutes_today"] / observation_window, 1.0)
    return round(max(100 - wasted_ratio * 100, 0), 1)


def calculate_building_score(building_name):
    building_rooms = [r for r in rooms if r["building"] == building_name]
    if not building_rooms:
        return 0
    scores = [calculate_efficiency_score(r) for r in building_rooms]
    return round(sum(scores) / len(scores), 1)


def estimate_wasted_kwh_and_cost(room):
    kwh_wasted = (room["power_watt"] * room["wasted_minutes_today"]) / 60000
    cost_wasted = kwh_wasted * TARIF_LISTRIK_PER_KWH
    return round(kwh_wasted, 3), round(cost_wasted, 0)


def simulate_sensors():
    # simulasi sensor gerak, dipakai selama belum ada hardware asli
    while True:
        time.sleep(4)
        with data_lock:
            for room in rooms:
                if not room["ac_on"]:
                    continue

                if random.random() < 0.12:
                    room["motion"] = not room["motion"]
                    if room["motion"]:
                        room["minutes_since_motion"] = 0

                if room["motion"]:
                    room["minutes_since_motion"] = 0
                else:
                    room["minutes_since_motion"] += 1
                    room["wasted_minutes_today"] += 1

                if get_room_status(room) == "anomaly" and room["minutes_since_motion"] == ANOMALY_THRESHOLD_MINUTES:
                    log_alert(
                        room,
                        f'AC {room["name"]} masih menyala, ruangan terdeteksi kosong '
                        f'selama {room["minutes_since_motion"]} menit.'
                    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/rooms")
def api_rooms():
    with data_lock:
        result = []
        for room in rooms:
            kwh, cost = estimate_wasted_kwh_and_cost(room)
            result.append({
                **room,
                "status": get_room_status(room),
                "efficiency_score": calculate_efficiency_score(room),
                "wasted_kwh_today": kwh,
                "wasted_cost_today": cost,
            })
        return jsonify(result)


@app.route("/api/buildings")
def api_buildings():
    with data_lock:
        building_names = sorted(set(r["building"] for r in rooms))
        result = []
        for b in building_names:
            b_rooms = [r for r in rooms if r["building"] == b]
            total_kwh = sum(estimate_wasted_kwh_and_cost(r)[0] for r in b_rooms)
            total_cost = sum(estimate_wasted_kwh_and_cost(r)[1] for r in b_rooms)
            result.append({
                "building": b,
                "score": calculate_building_score(b),
                "room_count": len(b_rooms),
                "wasted_kwh_today": round(total_kwh, 2),
                "wasted_cost_today": round(total_cost, 0),
            })
        return jsonify(result)


@app.route("/api/alerts")
def api_alerts():
    with data_lock:
        return jsonify(alert_log)


@app.route("/api/rooms/<int:room_id>/shutoff", methods=["POST"])
def api_shutoff(room_id):
    with data_lock:
        for room in rooms:
            if room["id"] == room_id:
                room["ac_on"] = False
                room["power_watt"] = 0
                room["motion"] = False
                log_alert(room, f'AC {room["name"]} dimatikan jarak jauh oleh petugas.')
                return jsonify({"success": True, "room": room})
        return jsonify({"success": False, "error": "Ruangan tidak ditemukan"}), 404


@app.route("/api/rooms/<int:room_id>/turn_on", methods=["POST"])
def api_turn_on(room_id):
    with data_lock:
        for room in rooms:
            if room["id"] == room_id:
                room["ac_on"] = True
                room["power_watt"] = 800
                room["motion"] = True
                room["minutes_since_motion"] = 0
                return jsonify({"success": True, "room": room})
        return jsonify({"success": False, "error": "Ruangan tidak ditemukan"}), 404


if __name__ == "__main__":
    threading.Thread(target=simulate_sensors, daemon=True).start()
    # use_reloader=False supaya thread simulasi tidak berjalan dua kali
    # (kalau jalan dua kali, log CSV akan tercatat ganda)
    app.run(debug=True, use_reloader=False, host="127.0.0.1", port=5000)