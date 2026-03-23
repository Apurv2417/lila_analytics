# Demo Script: LILA BLACK Analytics Walkthrough

## The Hook & High-Level Goal
* **The Intro:** "I built this Level Design Explorer to turn raw, complex telemetry into actionable insights. The goal was to empower designers to identify player pain points and balance issues without needing to write a single line of code."
* **The Tech:** "It’s a Python-based Streamlit application utilizing Plotly with WebGL-accelerated rendering. This architecture allows us to handle nearly 100,000 data points smoothly directly in a web browser, ensuring accessibility for the entire design team."

## Technical Architecture & Memory Management
* **Data Integrity:** "To ensure stability and prevent memory crashes on high-density datasets, I implemented a **Selective Column Loading** system. Instead of ingesting full Parquet files, I only load the six essential columns required for visualization, reducing RAM overhead significantly."
* **The Mapping Logic:** "The most technical challenge was mapping 3D world coordinates to a 2D minimap. I developed a UV normalization formula to translate world $x$ and $z$ into a $1024 \times 1024$ pixel space, accounting for map-specific origins and scales while inverting the Y-axis to match web standards."

**The Formula:**
$$px = \frac{x - ox}{scale} \times 1024$$
$$py = \left(1 - \frac{z - oz}{scale}\right) \times 1024$$

## Feature: The "Noise Filter" (Sidebar)
* **Bot vs. Human Segmentation:** "Game telemetry is often skewed by AI behavior. I built a heuristic filter that separates UUIDs (Human players) from numeric IDs (Bots). This allows a designer to strip away scripted AI paths and focus purely on the organic, often unpredictable 'chaos' of real human players."
* **Filter Logic:** *[Demonstrate toggling the checkboxes and show how the map updates instantly to reflect player-only data].*

## Feature: Match Playback & Player Journeys
* **Timeline Scrubbing:** "The **Match Playback** tab uses a relative time calculation. Even though raw timestamps vary across matches, the tool normalizes everything to 'seconds since start' to power an intuitive timeline slider."
* **The Value:** "We can watch exactly where a player spawned, their rotation through the map, where they stalled in the geometry, and their final engagement point."

## Feature: Tactical Heatmap & Intensity Binning
* **Combat Density:** "To prevent visual clutter from thousands of overlapping points, I created a **Spatial Binning** system that groups combat events into a 60x60 grid."
* **Visual Representation:** "The markers utilize an intensity gradient scaling from **Light to Dark Red**. This immediately highlights 'Meat Grinders'—areas where players are dying at a disproportionately high rate."
* **Interactive Tooltips:** "Hovering over any cluster provides the exact **Kill Count** and the precise **X/Y coordinates**, allowing a designer to find that exact location in the game engine for immediate adjustment."

## The Closing: Actionable Design Value
* **The 'So What?':** "This isn't just a visualization tool; it's a balance tool. For example, my analysis of Ambrose Valley showed 18% of human players dying within the first 60 seconds. This data suggests our spawn points are currently too close to high-tier loot clusters, providing a clear path for a design fix."
* **Conclusion:** "I’ve designed this to be a stable, scalable framework that can grow as the game adds more maps and events. Any questions on the data pipeline or the coordinate math?"