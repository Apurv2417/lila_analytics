import streamlit as st
import pandas as pd
import os
import glob
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
RUNNING_LOCALLY = False 

if RUNNING_LOCALLY:
    DATA_INPUT_PATH = r"E:\lila_analytics\player_data"
else:
    DATA_INPUT_PATH = "player_data"
# ==========================================

st.set_page_config(page_title="LILA BLACK Analytics", layout="wide")
st.title("🎮 LILA BLACK: Level Design Explorer")

# --- DATA ENGINE ---
@st.cache_data
def load_all_data(base_path):
    search_pattern = os.path.join(base_path, "**", "*.nakama-0*")
    all_files = glob.glob(search_pattern, recursive=True)
    frames = []
    
    if not all_files:
        return pd.DataFrame()

    for f in all_files:
        try:
            df = pd.read_parquet(f)
            
            # --- CRITICAL FIX: Ensure 'ts' is a number ---
            df['ts'] = pd.to_numeric(df['ts'], errors='coerce')
            
            path_parts = f.split(os.sep)
            df['date'] = path_parts[-2] if len(path_parts) >= 2 else "Unknown"
            df['event'] = df['event'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
            uid = os.path.basename(f).split('_')[0]
            df['is_bot'] = uid.isdigit()
            
            frames.append(df)
        except: 
            continue
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

def map_coords(df):
    if df.empty: return df
    configs = {
        "AmbroseValley": {"scale": 900, "ox": -370, "oz": -473},
        "GrandRift": {"scale": 581, "ox": -290, "oz": -290},
        "Lockdown": {"scale": 1000, "ox": -500, "oz": -500}
    }
    def transform(row):
        c = configs.get(row['map_id'])
        if not c: return pd.Series([None, None])
        u = (row['x'] - c['ox']) / c['scale']
        v = (row['z'] - c['oz']) / c['scale']
        return pd.Series([u * 1024, (1 - v) * 1024])
    
    df[['px', 'py']] = df.apply(transform, axis=1)
    return df

# --- LOADING ---
with st.spinner("Processing telemetry..."):
    raw_df = load_all_data(DATA_INPUT_PATH) 
    df = map_coords(raw_df)

if not df.empty:
    st.sidebar.header("Data Selection")
    all_dates = sorted(df['date'].unique())
    selected_dates = st.sidebar.multiselect("Select Dates", all_dates, default=all_dates)
    
    show_humans = st.sidebar.checkbox("Show Human Players", value=True)
    show_bots = st.sidebar.checkbox("Show AI Bots", value=True)

    filtered_df = df[df['date'].isin(selected_dates)]
    if not show_humans:
        filtered_df = filtered_df[filtered_df['is_bot'] == True]
    if not show_bots:
        filtered_df = filtered_df[filtered_df['is_bot'] == False]
    
    if not filtered_df.empty:
        available_maps = sorted(filtered_df['map_id'].unique())
        selected_map = st.sidebar.selectbox("Select Map", available_maps)
        map_df = filtered_df[filtered_df['map_id'] == selected_map]

        # --- UPDATED SMART MATCH SELECTION ---
        def get_duration(m_id):
            m_data = map_df[map_df['match_id'] == m_id]
            # README says ts is milliseconds. Max - Min / 1000 = Seconds.
            diff = m_data['ts'].max() - m_data['ts'].min()
            return int(diff / 1000) if diff > 0 else 0

        match_list = sorted(map_df['match_id'].unique())
        match_options = {m: f"{m[:8]}... ({get_duration(m)}s)" for m in match_list}
        sorted_matches = sorted(match_list, key=get_duration, reverse=True)

        selected_match = st.sidebar.selectbox(
            "Select Match ID", 
            sorted_matches, 
            format_func=lambda x: match_options[x]
        )
        
        match_data = map_df[map_df['match_id'] == selected_match].sort_values('ts')

        tab1, tab2 = st.tabs(["🎥 Match Playback", "🔥 Combat Glow Map"])

        with tab1:
            if not match_data.empty:
                # Force relative seconds calculation
                match_data['seconds'] = ((match_data['ts'] - match_data['ts'].min()) / 1000).astype(int)
                max_sec = int(match_data['seconds'].max())
                
                if max_sec > 0:
                    st.write(f"⏱️ **Match Duration:** {max_sec} seconds")
                    time_slice = st.slider("Scrub Through Timeline", 0, max_sec, max_sec)
                else:
                    st.info("⏱️ Single-event or 0s match. Showing static view.")
                    time_slice = 0
                
                current_data = match_data[match_data['seconds'] <= time_slice]
                
                fig = px.scatter(current_data, x="px", y="py", color="event", symbol="is_bot",
                                 hover_name="user_id", title=f"Replay: {selected_match}")
                
                for ext in ['.png', '.jpg']:
                    img_path = f"minimaps/{selected_map}_Minimap{ext}"
                    if os.path.exists(img_path):
                        img = Image.open(img_path)
                        fig.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", opacity=0.7, layer="below"))
                        break
                fig.update_xaxes(range=[0, 1024], visible=False)
                fig.update_yaxes(range=[1024, 0], visible=False)
                st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader(f"Combat Intensity: {selected_map}")
            event_filter = st.multiselect("Select Events", sorted(df['event'].unique()), default=['Kill', 'Killed'])
            heat_df = map_df[map_df['event'].isin(event_filter)]
            
            if not heat_df.empty:
                fig_heat = go.Figure()
                fig_heat.add_trace(go.Histogram2dContour(
                    x=heat_df['px'], y=heat_df['py'],
                    colorscale=[[0, 'rgba(255,255,255,0)'], [0.1, 'rgba(255,255,255,0.7)'], [0.4, 'rgba(255,100,100,0.8)'], [1.0, 'rgba(139,0,0,1)']],
                    ncontours=30, contours=dict(coloring='heatmap', showlines=False),
                    nbinsx=50, nbinsy=50,
                    hovertemplate="<b>Kills in Area: %{z}</b><br>Location: %{x:.0f}, %{y:.0f}<extra></extra>"
                ))
                for ext in ['.png', '.jpg']:
                    img_path = f"minimaps/{selected_map}_Minimap{ext}"
                    if os.path.exists(img_path):
                        img = Image.open(img_path)
                        fig_heat.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", opacity=1.0, layer="below"))
                        break
                fig_heat.update_layout(margin=dict(l=0, r=0, t=40, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(range=[0, 1024], visible=False), yaxis=dict(range=[1024, 0], visible=False))
                st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("Adjust filters to load data.")
else:
    st.error("Telemetry data not found.")