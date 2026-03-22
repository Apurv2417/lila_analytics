# Architecture Documentation: LILA BLACK Analytics

## 1. Technical Stack
- **Language**: Python 
- **Frontend**: Streamlit (Web-based UI for Level Designers)
- **Visualization**: Plotly (Scatter & Heatmap Engines)
- **Data Handling**: Pandas & PyArrow (Parquet ingestion)

## 2. Optimized Data Pipeline
- **Selective Column Loading**: Only 6 essential columns are loaded from Parquet files, reducing RAM usage by ~80%.
- **Smart Timestamp Detection**: Telemetry often mixes milliseconds and seconds. The engine auto-detects the unit based on maximum values to ensure the 1024x1024 mapping remains accurate.
- **Bot vs. Human Heuristics**: Implemented a filtering layer that distinguishes between UUIDs (Humans) and numeric IDs (Bots) based on filename conventions.

## 3. Coordinate Mapping (3D to 2D)
The tool translates 3D game world coordinates $(x, z)$ into a $1024 \times 1024$ pixel space for minimap overlays using the following normalization:
$$px = \frac{x - origin_x}{scale} \times 1024$$
$$py = \left(1 - \frac{z - origin_z}{scale}\right) \times 1024$$

## 4. Heatmap Binning Logic
Instead of plotting 90,000 individual points which can clutter a map, the tool uses **Spatial Binning**:
- The map is divided into a **60x60 grid**.
- Events are aggregated into these "bins."
- The UI renders circles where the **Color Intensity** (Light to Dark Red) and **Size** represent the "Kill Count" in that specific zone.
- **Hover Logic**: Interactive tooltips provide the exact bin location and event density.