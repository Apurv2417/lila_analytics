# Level Design Insights: LILA BLACK Telemetry

### 1. Bot Navigation Bottlenecks
- **Observation**: By toggling "Show Bots," it is clear that AI follows strict NavMesh paths.
- **Insight**: Several areas of Ambrose Valley have zero bot activity despite being high-loot zones. 
- **Action**: Level designers should check for "NavMesh breaks" or invisible walls preventing AI from entering these buildings.

### 2. High-Intensity "Meat Grinders"
- **Observation**: The Tactical Heatmap shows a deep crimson cluster (high kill count) near the central bridge on the Lockdown map.
- **Insight**: This bridge is currently the only viable rotation for players caught in the storm, leading to unfair "gatekeeping."
- **Action**: Add a secondary subterranean path or a zip-line to provide players an alternative to the main bridge choke point.

### 3. Early-Session Attrition
- **Observation**: Using the Playback Slider, many Human players show a `Killed` event within the first 45 seconds.
- **Insight**: Spawn points may be too close together, or the initial "Safe Zone" is shrinking too fast.
- **Action**: Increase the distance between initial spawn clusters to allow players at least 60 seconds of looting before forced engagement.