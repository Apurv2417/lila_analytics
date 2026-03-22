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
    
    # Selective columns to prevent "Oh no!" memory crashes
    COLS = ['ts', 'x', 'z', 'event', 'map_id', 'match_id']
    
    for f in all_files:
        try:
            temp_df = pd.read_parquet(f, columns=COLS)
            temp_df['ts'] = pd.to_numeric(temp_df['ts'], errors='coerce')
            temp_df = temp_df.dropna(subset=['ts'])
            
            # Decode bytes
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

    # Detect Time Unit
    unit = 'ms' if full_df['ts'].max() > 10**11 else 's'
    full_df['ts_dt'] = pd.to_datetime(full_df['ts'], unit=unit, errors='coerce')
    return full_df.dropna(subset=['ts_dt'])

def apply_mapping(df):
    if df.empty: return df
    configs = {
        "AmbroseValley": {"scale": 900, "ox": -370, "oz": -473},
        "GrandRift": {"scale": 581, "ox": -290, "oz": -290},
        "Lockdown": {"scale": 1000, "ox": -500, "oz": -500}
    }
    def transform(row):
        c = configs.get(row['map_id'])
        if not c: return pd.Series([0, 0])
        px = ((row['x'] - c['ox']) / c['scale']) * 1024
        py = (1 - ((row['z'] - c['oz']) / c['scale'])) * 1024
        return pd.Series([px, py])

    df[['px', 'py']] = df.apply(transform, axis=1)
    return df

# --- APP START ---
st.title("🎮 LILA BLACK: Level Design Explorer")

with st.spinner("Processing Telemetry..."):
    df = load_all_data(DATA_INPUT_PATH)
    df = apply_mapping(df)

if df.empty:
    st.error("No valid data found.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.header("Global Filters")
sel_dates = st.sidebar.multiselect("Select Dates", sorted(df['date'].unique()), default=df['date'].unique())
show_h = st.sidebar.checkbox("Show Humans", value=True)
show_b = st.sidebar.checkbox("Show Bots", value=True)

f_df = df[df['date'].isin(sel_dates)]
if not show_h: f_df = f_df[f_df['is_bot'] == True]
if not show_b: f_df = f_df[f_df['is_bot'] == False]

if not f_df.empty:
    sel_map = st.sidebar.selectbox("Select Map", sorted(f_df['map_id'].unique()))
    map_df = f_df[f_df['map_id'] == sel_map]

    # Pre-calc durations
    match_stats = map_df.groupby('match_id')['ts_dt'].agg(['min', 'max'])
    match_stats['dur'] = (match_stats['max'] - match_stats['min']).dt.total_seconds().astype(int)
    sorted_m_ids = sorted(map_df['match_id'].unique(), key=lambda x: match_stats.loc[x, 'dur'], reverse=True)
    
    sel_match = st.sidebar.selectbox("Match Playback", sorted_m_ids, 
                                     format_func=lambda x: f"{x[:8]}... ({match_stats.loc[x, 'dur']}s)")
    
    match_data = map_df[map_df['match_id'] == sel_match].sort_values('ts_dt')

    t1, tab_heat = st.tabs(["🎥 Match Playback", "🔥 Combat Heatmap"])

    with t1:
        if not match_data.empty:
            match_data['rel'] = (match_data['ts_dt'] - match_data['ts_dt'].min()).dt.total_seconds().astype(int)
            max_r = int(match_data['rel'].max())
            scrub = st.slider("Time Slider", 0, max_r, max_r) if max_r > 0 else 0
            
            curr = match_data[match_data['rel'] <= scrub]
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

    with tab_heat:
        st.subheader(f"Combat Distribution: {sel_map}")
        ev_filter = st.multiselect("Select Events for Heatmap", sorted(df['event'].unique()), default=['Kill', 'Killed'])
        h_df = map_df[map_df['event'].isin(ev_filter)]
        
        if not h_df.empty:
            # --- RESTORED CIRCLE LOGIC ---
            fig_h = px.scatter(h_df, x="px", y="py", 
                               color="event", 
                               opacity=0.6,
                               size_max=15,
                               title=f"Event Concentration ({len(h_df)} events)")
            
            # Make the dots look like "heat" by increasing marker size
            fig_h.update_traces(marker=dict(size=12, line=dict(width=0)))

            for ext in ['.png', '.jpg']:
                m_path = f"minimaps/{sel_map}_Minimap{ext}"
                if os.path.exists(m_path):
                    img = Image.open(m_path)
                    fig_h.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", opacity=0.8, layer="below"))
                    break
            
            fig_h.update_xaxes(range=[0, 1024], visible=False)
            fig_h.update_yaxes(range=[1024, 0], visible=False)
            fig_h.update_layout(margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_h, use_container_width=True)
        else:
            st.info("Select events to view locations.")