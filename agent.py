import os
import urllib.request
import urllib.parse
import json
import sqlite3
from google.adk.agents import Agent

# --- 1. DATABASE LOKAL (PENGGANTI BIGQUERY) ---
def setup_mock_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE air_quality (
                    date DATE, city TEXT, country TEXT, 
                    latitude REAL, longitude REAL, 
                    pm25 REAL, pm10 REAL, aqi_category TEXT)''')
    data = [
        ('2026-06-30', 'Delhi', 'India', 28.6, 77.2, 372.9, 450.1, '🔴 Sangat Tidak Sehat'),
        ('2026-06-30', 'Hanoi', 'Vietnam', 21.0, 105.8, 182.8, 200.5, '🔴 Sangat Tidak Sehat'),
        ('2026-06-30', 'Dhaka', 'Bangladesh', 23.8, 90.4, 169.5, 190.2, '🔴 Sangat Tidak Sehat'),
        ('2026-06-30', 'Bangkok', 'Thailand', 13.7, 100.5, 97.0, 120.0, '🔴 Tidak Sehat'),
        ('2026-06-30', 'Beijing', 'China', 39.9, 116.4, 93.2, 110.5, '🔴 Tidak Sehat'),
        ('2026-06-30', 'Jakarta', 'Indonesia', -6.2, 106.8, 45.38, 55.0, '🟢 Baik'),
        ('2026-06-29', 'Jakarta', 'Indonesia', -6.2, 106.8, 42.10, 50.0, '🟢 Baik'),
        ('2026-06-30', 'Singapore', 'Singapore', 1.3, 103.8, 25.5, 30.0, '🟢 Baik')
    ]
    c.executemany("INSERT INTO air_quality VALUES (?,?,?,?,?,?,?,?)", data)
    conn.commit()
    return conn

_conn = setup_mock_db()

def query_air_quality(sql: str) -> dict:
    try:
        clean = sql.strip().rstrip(";").replace("`aerosense-ai-501007.aerosense.air_quality`", "air_quality")
        c = _conn.cursor()
        c.execute(clean)
        columns = [description[0] for description in c.description]
        rows = c.fetchall()
        data = []
        for r in rows:
            data.append(dict(zip(columns, r)))
        return {"status": "success", "jumlah_baris": len(data), "hasil": data[:50]}
    except Exception as e:
        return {"status": "error", "pesan": str(e)}

# --- 2. TOOL SEARCH INTERNET ---
def search_internet_for_news(query: str) -> str:
    try:
        query_lower = query.lower()
        if "cuaca" in query_lower or "hujan" in query_lower or "panas" in query_lower:
            url = "https://api.open-meteo.com/v1/forecast?latitude=-6.2088&longitude=106.8456&current=temperature_2m,weather_code&timezone=Asia%2FJakarta"
            req = urllib.request.Request(url, headers={'User-Agent': 'Aerosense/1.0'})
            response = urllib.request.urlopen(req, timeout=5)
            data = json.loads(response.read().decode('utf-8'))
            temp = data.get("current", {}).get("temperature_2m", "Tidak diketahui")
            return f"Info Cuaca (Open-Meteo): Suhu saat ini tercatat sekitar {temp}°C."

        keywords = " ".join(query.split()[:2])
        safe_query = urllib.parse.quote(keywords)
        url = f"https://id.wikipedia.org/w/api.php?action=query&list=search&srsearch={safe_query}&utf8=&format=json"
        req = urllib.request.Request(url, headers={'User-Agent': 'Aerosense/1.0'})
        response = urllib.request.urlopen(req, timeout=5)
        data = json.loads(response.read().decode('utf-8'))
        if data.get('query', {}).get('search'):
            snippet = data['query']['search'][0]['snippet']
            clean = snippet.replace('<span class="searchmatch">', '').replace('</span>', '')
            return f"Info dari Ensiklopedia (Wiki): {clean}..."
        return "Pencarian berhasil, namun tidak ada informasi spesifik."
    except Exception as e:
        return f"Sistem pencarian sedang sibuk, referensikan ke data historis lokal."

# --- 3. ROOT AGENT ---
INSTRUCTION = f"""Kamu adalah AeroSense AI, seorang Pakar Kualitas Udara.
Kamu memiliki 2 alat utama:
1. `query_air_quality` (Akses ke database SQL untuk data historis).
2. `search_internet_for_news` (Akses ke internet).

ATURAN WAJIB:
- SQL FIRST: Untuk angka/peringkat polusi, SELALU tulis query SQL ke tabel `air_quality` (tanpa tanda kutip balik). JANGAN PERNAH mengarang angka.
- GROUNDING FIRST: Untuk berita/cuaca saat ini, gunakan `search_internet_for_news`.
- MULTIMODAL: Jika pengguna mengunggah GAMBAR, WAJIB mengomentari visual di foto tersebut dahulu, baru berikan data.
- Gunakan Tabel Markdown jika mengembalikan lebih dari 2 baris data.
"""

root_agent = Agent(
    name="aerosense_assistant",
    model="gemini-2.5-flash",
    description="Asisten AeroSense AI",
    instruction=INSTRUCTION,
    tools=[query_air_quality, search_internet_for_news], 
)