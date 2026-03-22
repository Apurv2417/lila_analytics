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
            
            # --- CRITICAL FIX 1: Standardize Timestamps immediately ---
            # This converts any format (string, int, float) to a number
            df['ts'] = pd.to_numeric(df['ts'], errors='coerce')
            df = df.dropna(subset=['ts']) # Remove rows with broken time
            
            # Identify if numeric or datetime
            if df['ts'].max() > 10**11: # If it's in milliseconds
                df['ts_dt'] = pd.to_datetime(df['ts'], unit='ms')
            else: # If it's already in seconds
                df['ts_dt'] = pd.to_datetime(df['ts'], unit='s')

            path_parts = f.split(os.sep)
            df['date'] = path_parts[-2] if len(path_parts) >= 2 else "Unknown"
            df['event'] = df['event'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
            
            uid = os.path.basename(f).split('_')[0]
            df['is_bot'] = uid.isdigit()
            
            frames.append(df)
        except Exception: 
            continue
            
    if not frames: return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)

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
with st.spinner("Processing telemetry data..."):
    raw_df = load_all_data(DATA_INPUT_PATH) 
    df = map_coords(raw_df)

if not df.empty:
    # --- SIDEBAR ---
    st.sidebar.header("Data Selection")
    all_dates = sorted(df['date'].unique())
    selected_dates = st.sidebar.multiselect("Select Dates", all_dates, default=all_dates)
    
    st.sidebar.subheader("Filter by Player Type")
    show_humans = st.sidebar.checkbox("Show Human Players", value=True)
    show_bots = st.sidebar.checkbox("Show AI Bots", value=True)

    # Filter Logic
    f_df = df[df['date'].isin(selected_dates)]
    if not show_humans: f_df = f_df[f_df['is_bot'] == True]
    if not show_bots: f_df = f_df[f_df['is_bot'] == False]
    
    if not f_df.empty:
        selected_map = st.sidebar.selectbox("Select Map", sorted(f_df['map_id'].unique()))
        map_df = f_df[f_df['map_id'] == selected_map]

        # --- SMART DURATION LOGIC ---
        # Grouping first makes the sidebar much faster and prevents 0s errors
        stats = map_df.groupby('match_id')['ts_dt'].agg(['min', 'max'])
        stats['duration'] = (stats['max'] - stats['min']).dt.total_seconds().astype(int)
        
        match_list = sorted(map_df['match_id'].unique(), key=lambda x: stats.loc[x, 'duration'], reverse=True)
        match_options = {m: f"{m[:8]}... ({stats.loc[m, 'duration']}s)" for m in match_list}

        selected_match = st.sidebar.selectbox("Select Match ID", match_list, format_func=lambda x: match_options[x])
        match_data = map_df[map_df['match_id'] == selected_match].sort_values('ts_dt')

        # --- TABS ---
        tab1, tab2 = st.tabs(["🎥 Match Playback", "🔥 Combat Glow Map"])

        with tab1:
            if not match_data.empty:
                # Calculate relative seconds
                match_data['rel_sec'] = (match_data['ts_dt'] - match_data['ts_dt'].min()).dt.total_seconds().astype(int)
                max_dur = int(match_data['rel_sec'].max())
                
                if max_dur > 0:
                    st.write(f"⏱️ **Match Duration:** {max_dur} seconds")
                    time_slice = st.slider("Scrub Timeline", 0, max_dur, max_dur)
                else:
                    st.info("⏱️ This match data has only one recorded timestamp.")
                    time_slice = 0
                
                curr = match_data[match_data['rel_sec'] <= time_slice]
                fig = px.scatter(curr, x="px", y="py", color="event", symbol="is_bot", hover_name="user_id")
                
                # Minimap Overlay
                for ext in ['.png', '.jpg']:
                    m_path = f"minimaps/{selected_map}_Minimap{ext}"
                    if os.path.exists(m_path):
                        img = Image.open(m_path)
                        fig.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", opacity=0.7, layer="below"))
                        break
                
                fig.update_xaxes(range=[0, 1024], visible=False)
                fig.update_yaxes(range=[1024, 0], visible=False)
                st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader(f"Combat Intensity: {selected_map}")
            ev_filter = st.multiselect("Select Events", sorted(df['event'].unique()), default=['Kill', 'Killed'])
            h_df = map_df[map_df['event'].isin(ev_filter)]
            
            if not h_df.empty:
                fig_h = go.Figure()
                fig_h.add_trace(go.Histogram2dContour(
                    x=h_df['px'], y=h_df['py'],
                    colorscale=[[0, 'rgba(255,255,255,0)'], [0.1, 'rgba(255,255,255,0.7)'], [0.4, 'rgba(255,100,100,0.8)'], [1.0, 'rgba(139,0,0,1)']],
                    ncontours=30, contours=dict(coloring='heatmap', showlines=False),
                    nbinsx=50, nbinsy=50,
                    hovertemplate="<b>Kills in Area: %{z}</b><br>Location: %{x:.0f}, %{y:.0f}<extra></extra>"
                ))
                for ext in ['.png', '.jpg']:
                    m_path = f"minimaps/{selected_map}_Minimap{ext}"
                    if os.path.exists(m_path):
                        img = Image.open(m_path)
                        fig_h.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", opacity=1.0, layer="below"))
                        break
                fig_h.update_layout(margin=dict(l=0, r=0, t=40, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(range=[0, 1024], visible=False), yaxis=dict(range=[1024, 0], visible=False))
                st.plotly_chart(fig_h, use_container_width=True)
    else:
        st.info("No data matches your sidebar filters.")
else:
    st.error("Data not found. Please check your 'player_data' folder.")