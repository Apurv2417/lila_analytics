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
DATA_INPUT_PATH = "player_data" if not RUNNING_LOCALLY else r"E:\lila_analytics\player_data"
# ==========================================

st.set_page_config(page_title="LILA BLACK Analytics", layout="wide")

# --- DATA ENGINE (MEMORY OPTIMIZED) ---
@st.cache_data
def load_all_data(base_path):
    search_pattern = os.path.join(base_path, "**", "*.nakama-0*")
    all_files = glob.glob(search_pattern, recursive=True)
    frames = []
    
    # Define only the columns we need to save memory
    COLS = ['ts', 'x', 'z', 'event', 'map_id', 'match_id']
    
    for f in all_files:
        try:
            # Only read necessary columns to prevent "Oh no!" memory crashes
            temp_df = pd.read_parquet(f, columns=COLS)
            
            # Clean timestamps
            temp_df['ts'] = pd.to_numeric(temp_df['ts'], errors='coerce')
            temp_df = temp_df.dropna(subset=['ts'])
            
            # Decode events
            temp_df['event'] = temp_df['event'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else str(x))
            
            # Metadata
            path_parts = f.split(os.sep)
            temp_df['date'] = path_parts[-2] if len(path_parts) >= 2 else "Unknown"
            uid = os.path.basename(f).split('_')[0]
            temp_df['is_bot'] = uid.isdigit()
            
            frames.append(temp_df)
        except:
            continue
            
    if not frames: return pd.DataFrame()
    
    full_df = pd.concat(frames, ignore_index=True)

    # --- AUTO-DETECT TIME UNIT ---
    # If the max value is small, it's seconds. If huge, it's milliseconds.
    max_ts = full_df['ts'].max()
    unit = 'ms' if max_ts > 10**11 else 's'
    
    full_df['ts_dt'] = pd.to_datetime(full_df['ts'], unit=unit, errors='coerce')
    return full_df.dropna(subset=['ts_dt'])

def apply_mapping(df):
    if df.empty: return df
    configs = {
        "AmbroseValley": {"scale": 900, "ox": -370, "oz": -473},
        "GrandRift": {"scale": 581, "ox": -290, "oz": -290},
        "Lockdown": {"scale": 1000, "ox": -500, "oz": -500}
    }
    def transform_coords(row):
        c = configs.get(row['map_id'])
        if not c: return pd.Series([0, 0])
        px = ((row['x'] - c['ox']) / c['scale']) * 1024
        py = (1 - ((row['z'] - c['oz']) / c['scale'])) * 1024
        return pd.Series([px, py])

    df[['px', 'py']] = df.apply(transform_coords, axis=1)
    return df

# --- APP START ---
st.title("🎮 LILA BLACK: Level Design Explorer")

with st.spinner("Crunching telemetry data..."):
    df = load_all_data(DATA_INPUT_PATH)
    df = apply_mapping(df)

if df.empty:
    st.error("No valid data found.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.header("Data Selection")
all_dates = sorted(df['date'].unique())
sel_dates = st.sidebar.multiselect("Select Dates", all_dates, default=all_dates)

st.sidebar.subheader("Player Type")
show_h = st.sidebar.checkbox("Show Humans", value=True)
show_b = st.sidebar.checkbox("Show Bots", value=True)

# Filter
f_df = df[df['date'].isin(sel_dates)]
if not show_h: f_df = f_df[f_df['is_bot'] == True]
if not show_b: f_df = f_df[f_df['is_bot'] == False]

if not f_df.empty:
    sel_map = st.sidebar.selectbox("Select Map", sorted(f_df['map_id'].unique()))
    map_df = f_df[f_df['map_id'] == sel_map]

    # Pre-calculate durations for the sidebar
    match_durations = map_df.groupby('match_id')['ts_dt'].agg(lambda x: int((x.max() - x.min()).total_seconds()))
    m_ids = sorted(map_df['match_id'].unique(), key=lambda x: match_durations[x], reverse=True)
    
    sel_match = st.sidebar.selectbox("Select Match ID", m_ids, 
                                     format_func=lambda x: f"{x[:8]}... ({match_durations[x]}s)")
    
    match_data = map_df[map_df['match_id'] == sel_match].sort_values('ts_dt')

    t1, t2 = st.tabs(["🎥 Match Playback", "🔥 Combat Glow Map"])

    with t1:
        if not match_data.empty:
            match_data['rel_sec'] = (match_data['ts_dt'] - match_data['ts_dt'].min()).dt.total_seconds().astype(int)
            max_s = int(match_data['rel_sec'].max())
            
            scrub = st.slider("Timeline (Seconds)", 0, max_s, max_s) if max_s > 0 else 0
            if max_s == 0: st.info("Static 0s match.")

            curr = match_data[match_data['rel_sec'] <= scrub]
            fig = px.scatter(curr, x="px", y="py", color="event", symbol="is_bot", title=f"Replay: {sel_match}")
            
            for ext in ['.png', '.jpg']:
                m_path = f"minimaps/{sel_map}_Minimap{ext}"
                if os.path.exists(m_path):
                    img = Image.open(m_path)
                    fig.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", opacity=0.7, layer="below"))
                    break
            
            fig.update_xaxes(range=[0, 1024], visible=False)
            fig.update_yaxes(range=[1024, 0], visible=False)
            st.plotly_chart(fig, use_container_width=True)

    with t2:
        st.subheader(f"Combat Intensity: {sel_map}")
        ev_filter = st.multiselect("Filter Events", sorted(df['event'].unique()), default=['Kill', 'Killed'])
        h_df = map_df[map_df['event'].isin(ev_filter)]
        
        if not h_df.empty:
            fig_h = go.Figure(go.Histogram2dContour(
                x=h_df['px'], y=h_df['py'],
                colorscale=[[0, 'rgba(255,255,255,0)'], [0.1, 'rgba(255,255,255,0.7)'], [0.4, 'rgba(255,100,100,0.8)'], [1.0, 'rgba(139,0,0,1)']],
                ncontours=30, contours=dict(coloring='heatmap', showlines=False),
                hovertemplate="<b>Kills: %{z}</b><br>X: %{x:.0f}, Y: %{y:.0f}<extra></extra>"
            ))
            
            for ext in ['.png', '.jpg']:
                m_path = f"minimaps/{sel_map}_Minimap{ext}"
                if os.path.exists(m_path):
                    img = Image.open(m_path)
                    fig_h.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", opacity=1.0, layer="below"))
                    break
            
            fig_h.update_layout(margin=dict(l=0, r=0, t=40, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(range=[0, 1024], visible=False), yaxis=dict(range=[1024, 0], visible=False))
            st.plotly_chart(fig_h, use_container_width=True)