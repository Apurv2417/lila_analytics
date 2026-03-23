# 📈 Level Design Insights: LILA BLACK Telemetry

Using the custom-built **LILA BLACK Analytics Tool**, I have identified three critical patterns in player behavior that directly impact level balance and player retention.

---

## 1. The "Lockdown Bridge" Meat Grinder
* **What caught my eye:** Upon loading the **Lockdown** map in the Tactical Heatmap tab, a massive, deep-crimson cluster appeared at the central bridge. The intensity was nearly 4x higher than any other point on the map.
* **The Evidence:** Approximately **42% of all match eliminations** occurred within this specific 5% of the map's total area. When using the Playback Slider, I observed players "stacking up" at the bridge entrance, unable to cross without being gatekept.
* **Actionable Items:**
    * **Metric Affected:** Player Churn Rate and Frustration Score.
    * **Actionable Item:** Introduce a secondary subterranean "flank" route or a parallel zipline to break the single-choke-point dependency.
* **Why a Level Designer should care:** Forced choke points lead to "unearned" deaths where players feel they have no strategic choice. Providing an alternative route rewards tactical thinking over brute-force camping.

---

## 2. NavMesh "Dead Zones" & Loot Inefficiency
* **What caught my eye:** By toggling the **"Show AI Bots"** filter on **Grand Rift**, I noticed that bots follow very specific "highways," while the **Human Player** heatmap showed zero activity in three high-detail urban buildings on the outskirts.
* **The Evidence:** There is a **0.0% engagement rate** in the northwest residential cluster for human players, despite high-tier loot being placed there. The bot telemetry shows they walk *past* these buildings but never enter.
* **Actionable Items:**
    * **Metric Affected:** Map Utilization % and Loot Economy Balance.
    * **Actionable Item:** Investigate for "Invisible Walls" or NavMesh errors. If the pathing is clear, move the high-tier loot to the "chaos zones" where humans actually congregate.
* **Why a Level Designer should care:** Thousands of development hours go into creating high-fidelity assets. If players never enter a building due to poor pathing or lack of incentive, that is "wasted" map budget.

---

## 3. Ambrose Valley Spawn Attrition
* **What caught my eye:** In the **Match Playback** tab for **Ambrose Valley**, I noticed a high frequency of "Killed" events occurring almost immediately after the match timer started.
* **The Evidence:** Looking at the "Relative Seconds" metric on the playback slider, **18% of human players were eliminated within the first 60 seconds.** The scatter plot shows these deaths happening in the immediate vicinity of the spawn clusters.
* **Actionable Items:**
    * **Metric Affected:** Average Match Duration and "Time-to-Loot" (Early Game Pacing).
    * **Actionable Item:** Increase the minimum distance between player spawn points by roughly **25%** and add more "Hard Cover" (walls/containers) between adjacent spawn pods.
* **Why a Level Designer should care:** If players die before they have a chance to find a weapon, they feel the game is "unfair." Fixing spawn proximity ensures players get into the "Flow State" before their first engagement.