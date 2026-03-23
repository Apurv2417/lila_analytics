# 🏗️ Architecture: LILA BLACK Analytics Tool

## 1. Tech Stack & Rationale
* **Python 3.13:** Chosen as the core language for its powerful data processing ecosystem.
* **Streamlit:** Selected for **rapid deployment** and ease of use. It allows Level Designers to access a complex data suite via a web browser without local environment setup.
* **Plotly:** Utilized for the rendering engine because it supports **WebGL**, which is essential for handling high-density telemetry (90,000+ points) without browser lag.
* **Pandas & PyArrow:** Chosen for high-speed Parquet ingestion and efficient column-based data manipulation.

## 2. Data Flow: From Parquet to UI
1. **Selective Ingestion:** To prevent memory crashes (the "Oh no!" error), the app only loads essential columns (`x`, `z`, `ts`, `event`, `map_id`, `match_id`).
2. **Byte Decoding:** Binary event data is decoded to UTF-8 strings.
3. **Smart Timestamp Normalization:** The engine auto-detects if the raw data is in seconds or milliseconds and converts everything into a standard Python `datetime` object.
4. **Coordinate Transformation:** World units are translated into a 1024px UV space (see below).
5. **Spatial Binning:** For the heatmap, coordinates are grouped into a 60x60 grid to calculate combat density and prevent visual clutter.

## 3. Coordinate Mapping (The Tricky Part)
Game worlds use a 3D Cartesian system, but the minimaps are 2D images. I implemented a **UV Normalization** approach to bridge this gap:

* **Normalization:** $(x - origin) / scale$. This converts world units into a $0.0$ to $1.0$ ratio.
* **Scaling:** Multiplied by $1024$ to match the minimap resolution.
* **The Y-Flip:** In game engines, $Z$ increases "up." In web images, $Y$ increases "down." I inverted the vertical axis to ensure player dots aligned correctly with buildings.

**Formula:**
$$px = \frac{x - ox}{scale} \times 1024$$
$$py = \left(1 - \frac{z - oz}{scale}\right) \times 1024$$

## 4. Assumptions & Ambiguities
* **Numeric IDs = Bots:** Per the project requirements, I assumed all numeric User IDs are AI Bots. This was used to build the "Noise Filter" in the sidebar.
* **Timestamp Units:** Since the data was ambiguous, I built an **Auto-Detect** layer: if `max(ts) > 10^11`, it is treated as milliseconds; otherwise, seconds.

## 5. Major Trade-offs

| Feature | Decision | Reason |
| :--- | :--- | :--- |
| **Binned Circles vs Heatmap** | **Binned Circles** | Standard heatmaps hide map details. Circles allow designers to see the map *and* get exact kill counts on hover. |
| **Selective vs Full Loading** | **Selective** | Full loading crashed the RAM. Selective loading keeps the app stable for 90k+ rows. |
| **Dynamic vs Static Map** | **Static Overlay** | To save performance, maps are loaded as background layers rather than dynamic textures. |

## 6. Future Improvements (With More Time)
* **Kill-Feed Lines:** Drawing vectors between the 'Killer' and 'Killed' coordinates to show firing lanes.
* **SQL Backend:** Moving from Parquet files to a database for faster global filtering across thousands of matches.