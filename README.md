🎮 LILA BLACK: Level Design Explorer
An interactive telemetry visualization suite built for the LILA BLACK Level Design team. This tool processes high-density player data (Parquet) to provide actionable insights into player journeys, combat hotspots, and AI behavior.

(https://lilaanalytics-cmkbrjlg5q2skqlwzwelfu.streamlit.app/)

🚀 Key Features
Smart Bot Detection: Automatically distinguishes between Human players (UUIDs) and AI Bots (Numeric IDs) to allow designers to filter out "bot noise."
Tactical Heat Distribution: A binned intensity map that identifies "meat grinders" and combat choke points with interactive hover-data (Location & Kill Counts).
Match Playback Engine: A temporal replay system with a precise time-scrubbing slider to investigate individual player sessions from spawn to extraction.
Multi-Map Support: Full coordinate mapping for Ambrose Valley, Grand Rift, and Lockdown.

🛠️ Tech Stack
Language: Python 3.13
Framework: Streamlit (Web UI)
Visualization: Plotly (Interactive Scatter & Heatmap engines)
Data Science: Pandas & PyArrow (Efficient Parquet ingestion)

📂 Repository Structure
app.py: The core Streamlit application logic.
ARCHITECTURE.md: Technical deep-dive into the data pipeline and coordinate mapping.
INSIGHTS.md: Gameplay analysis and level design recommendations derived from the data.
DEMO_GUIDE.md: A structured walkthrough for a 15-minute technical presentation.
requirements.txt: Python dependencies.
player_data/: Raw telemetry files (organized by date).
minimaps/: High-resolution map overlays.
