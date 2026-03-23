# 🎮 LILA BLACK: Level Design Explorer

An interactive telemetry visualization suite built for the **LILA BLACK** Level Design team. This tool transforms high-density player data into actionable insights regarding combat flow, map utilization, and AI behavior.

**🔗https://lilaanalytics-cmkbrjlg5q2skqlwzwelfu.streamlit.app/**

---

## 🚀 Key Features
* **Smart Bot Detection:** Built-in heuristics to separate Human players (UUIDs) from AI Bots (Numeric IDs), allowing designers to filter out "bot noise."
* **Tactical Heat Distribution:** A binned intensity map (60x60 grid) that identifies "meat grinders" with interactive tooltips showing exact Kill Counts and Coordinates.
* **Match Playback Engine:** A temporal replay system with a precise time-scrubbing slider to investigate individual player sessions from spawn to extraction.
* **High Performance:** Optimized memory ingestion using selective column loading to handle 90,000+ rows of telemetry without performance lag.

---

## 🛠️ Tech Stack
* **Language:** Python 3.13
* **Framework:** Streamlit (Web UI for rapid deployment)
* **Visualization:** Plotly with WebGL (High-performance rendering)
* **Data Science:** Pandas & PyArrow (Efficient Parquet ingestion)

---

## 💻 Local Setup & Installation
1. **Prerequisites:** Ensure you have **Python 3.10+** installed.
2. **Clone & Install:**
   ```bash
   git clone [https://github.com/Apurv2417/Lila-Analytics.git](https://github.com/Apurv2417/Lila-Analytics.git)
   cd Lila-Analytics
   pip install -r requirements.txt
Configuration: In app.py, set RUNNING_LOCALLY = True for local testing
