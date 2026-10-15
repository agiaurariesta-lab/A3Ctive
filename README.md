# A3Ctive — Smart AC Energy Management Dashboard (MVP)

Prototipe dashboard untuk memantau AC di ruangan/gedung kampus, mendeteksi
AC yang menyala saat ruangan kosong, menghitung Efficiency Score per
ruangan/gedung, dan menyediakan tombol **matikan AC dari jarak jauh**
(pengganti remot fisik yang sering hilang).

Data sensor pada versi ini **disimulasikan** (lihat `simulate_sensors()` di
`app.py`) supaya bisa langsung didemoin tanpa hardware. Nanti tinggal
ganti bagian simulasi dengan data asli dari sensor PIR / current sensor /
modul IR kalau sudah siap pasang di lapangan. Pada simulasi, satu putaran
(4 detik) mewakili 1 menit waktu nyata.

## Fitur

- Dashboard real-time (update otomatis setiap 2 detik)
- Status ruangan: Normal, Perlu Diperhatikan, Anomali
- Deteksi anomali: AC menyala saat ruangan kosong melebihi ambang waktu
- Tombol **Matikan Semua** untuk mematikan AC dari jarak jauh
- Efficiency Score per ruangan dan per gedung (0-100)
- Estimasi energi (kWh) dan biaya (Rp) yang terbuang
- Log notifikasi di dashboard, tersimpan juga ke `alert_log.csv`

## Struktur folder

```
a3ctive/
├── app.py                # Backend Flask: logic, simulasi sensor, API
├── requirements.txt      # Dependency Python
├── alert_log.csv         # Riwayat log (dibuat otomatis saat ada kejadian)
├── templates/
│   └── index.html        # Halaman dashboard (HTML)
└── static/
    ├── style.css         # Styling dashboard
    ├── extra.css         # Layout melebar & indikator server terputus
    └── script.js         # Fetch API & render dinamis (JavaScript)
```

## Cara menjalankan di VS Code

1. Buka folder `a3ctive` ini di VS Code (`File > Open Folder`).
2. Buka terminal di VS Code (``Ctrl+` ``), lalu buat virtual environment (opsional tapi disarankan):
```
   python -m venv venv
   venv\Scripts\activate       # Windows
   source venv/bin/activate    # Mac/Linux
```
   Jika PowerShell menolak mengaktifkan venv, jalankan dulu:
```
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```
3. Install dependency:
```
   py -m pip install -r requirements.txt
```
4. Pastikan terminal berada di folder yang berisi `app.py` (gunakan `cd a3ctive` jika perlu), lalu jalankan server:
```
   py app.py
```
5. Buka browser ke **http://127.0.0.1:5000**

Dashboard akan otomatis update setiap 2 detik. Jika tampilan tidak berubah
setelah file diedit, tekan `Ctrl+F5`. Untuk berhenti, tekan `Ctrl+C` di terminal.

## Pengaturan

Parameter berikut diatur langsung di bagian atas `app.py`:

| Parameter | Bawaan | Keterangan |
|---|---|---|
| `ANOMALY_THRESHOLD_MINUTES` | 20 | Ruangan kosong selama ini dengan AC menyala = anomali |
| `TARIF_LISTRIK_PER_KWH` | 1699.53 | Tarif PLN golongan P-1 (Oktober 2026); sesuaikan dengan golongan pelanggan gedung |
| `rooms` | 9 ruangan | Data ruangan, gedung/lantai, daya AC, dan kondisi awal |

Status "Perlu Diperhatikan" muncul setelah ruangan kosong 10 menit.
Restart server setelah mengubah nilai.

## Endpoint API

| Method | Endpoint | Fungsi |
|---|---|---|
| GET | `/api/rooms` | Status semua ruangan |
| GET | `/api/buildings` | Ringkasan skor dan pemborosan per gedung |
| GET | `/api/alerts` | 20 kejadian terakhir |
| POST | `/api/rooms/<id>/shutoff` | Matikan AC di satu ruangan |
| POST | `/api/rooms/<id>/turn_on` | Nyalakan AC di satu ruangan (demo) |

## Catatan

- Data ruangan disimpan di memori, jadi status kembali ke kondisi awal saat server dimulai ulang. Log kejadian tetap tersimpan di `alert_log.csv`.
- Server dijalankan dengan `use_reloader=False` supaya simulasi tidak berjalan dua kali dan log CSV tidak tercatat ganda.