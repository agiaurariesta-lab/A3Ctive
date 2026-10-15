const REFRESH_INTERVAL_MS = 2000;

const buildingContainer = document.getElementById("building-cards");
const roomContainer = document.getElementById("room-grid");
const alertContainer = document.getElementById("alert-list");
const clockEl = document.getElementById("clock");

function updateClock() {
  clockEl.textContent = new Date().toLocaleTimeString("id-ID");
}
setInterval(updateClock, 1000);
updateClock();

function scoreClass(score) {
  if (score >= 80) return "score-good";
  if (score >= 50) return "score-mid";
  return "score-bad";
}

function statusLabel(status) {
  if (status === "anomaly") return "Anomali";
  if (status === "warning") return "Perlu Diperhatikan";
  return "Normal";
}

async function loadBuildings() {
  const res = await fetch("/api/buildings");
  const buildings = await res.json();

  buildingContainer.innerHTML = buildings.map(b => `
    <div class="building-card">
      <h3>${b.building}</h3>
      <div class="score-value ${scoreClass(b.score)}">${b.score}</div>
      <div class="building-meta">
        Efficiency Score &middot; ${b.room_count} ruangan<br/>
        Estimasi boros hari ini: ${b.wasted_kwh_today} kWh
        (± Rp ${b.wasted_cost_today.toLocaleString("id-ID")})
      </div>
    </div>
  `).join("");
}

async function loadRooms() {
  const res = await fetch("/api/rooms");
  const rooms = await res.json();

  roomContainer.innerHTML = rooms.map(r => `
    <div class="room-card status-${r.status}">
      <div class="room-header">
        <div>
          <div class="room-name">${r.name}</div>
          <div class="room-building">${r.building}</div>
        </div>
        <span class="status-badge status-${r.status}">${statusLabel(r.status)}</span>
      </div>
      <div class="room-stats">
        AC: <b>${r.ac_on ? "Menyala" : "Mati"}</b> &middot; Daya: <b>${r.power_watt} W</b><br/>
        Gerakan terdeteksi: <b>${r.motion ? "Ya" : "Tidak"}</b>
        (kosong ${r.minutes_since_motion} menit)<br/>
        Efficiency Score: <b>${r.efficiency_score}</b><br/>
        Boros hari ini: <b>${r.wasted_kwh_today} kWh</b> (± Rp ${r.wasted_cost_today.toLocaleString("id-ID")})
      </div>
      <div class="room-actions">
        <button class="btn-shutoff" onclick="shutoffRoom(${r.id})" ${!r.ac_on ? "disabled" : ""}>
          MATIKAN SEMUA
        </button>
        <button class="btn-turnon" onclick="turnOnRoom(${r.id})" ${r.ac_on ? "disabled" : ""}>
          Nyalakan (demo)
        </button>
      </div>
    </div>
  `).join("");
}

async function loadAlerts() {
  const res = await fetch("/api/alerts");
  const alerts = await res.json();

  if (alerts.length === 0) {
    alertContainer.innerHTML = `<li class="alert-empty">Belum ada notifikasi.</li>`;
    return;
  }

  alertContainer.innerHTML = alerts.map(a => `
    <li>
      <span class="alert-time">${a.time}</span>
      <span>${a.message}</span>
    </li>
  `).join("");
}

async function shutoffRoom(roomId) {
  await fetch(`/api/rooms/${roomId}/shutoff`, { method: "POST" });
  refreshAll();
}

async function turnOnRoom(roomId) {
  await fetch(`/api/rooms/${roomId}/turn_on`, { method: "POST" });
  refreshAll();
}

async function refreshAll() {
  try {
    await Promise.all([loadBuildings(), loadRooms(), loadAlerts()]);
    clockEl.classList.remove("offline");
    document.title = "A3Ctive | Smart AC Energy Management";
  } catch (e) {
    clockEl.classList.add("offline");
    document.title = "(Terputus) A3Ctive";
  }
}

refreshAll();
setInterval(refreshAll, REFRESH_INTERVAL_MS);
