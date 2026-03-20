import streamlit as st
import pandas as pd
import os
import glob
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

# ==========================================
# ⚙️ CONFIGURATION (CHANGE THIS PART)
# ==========================================
# Set to True to test on your computer. Set to False before uploading to GitHub.
RUNNING_LOCALLY = False 

if RUNNING_LOCALLY:
    # Your specific Windows path
    DATA_INPUT_PATH = r"E:\lila_analytics\player_data"
else:
    # The path Streamlit Cloud will use
    DATA_INPUT_PATH = "player_data"
# ==========================================

st.set_page_config(page_title="LILA BLACK Analytics", layout="wide")
st.title("🎮 LILA BLACK: Level Design Explorer")

# --- DATA ENGINE ---
@st.cache_data
def load_all_data(base_path):
    # Searches for all gameplay files in subfolders
    search_pattern = os.path.join(base_path, "**", "*.nakama-0*")
    all_files = glob.glob(search_pattern, recursive=True)
    frames = []
    
    if not all_files:
        st.error(f"No files found in {base_path}. Please check your folder path!")
        return pd.DataFrame()

    for f in all_files:
        try:
            df = pd.read_parquet(f)
            # Decode byte events to strings
            df['event'] = df['event'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
            # Identify Human vs Bot from filename
            uid = os.path.basename(f).split('_')[0]
            df['is_bot'] = uid.isdigit()
            frames.append(df)
        except: 
            continue
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
        # World to UV to Pixel math
        u = (row['x'] - c['ox']) / c['scale']
        v = (row['z'] - c['oz']) / c['scale']
        return pd.Series([u * 1024, (1 - v) * 1024])
    
    df[['px', 'py']] = df.apply(transform, axis=1)
    return df

# --- LOADING ---
with st.spinner("Processing gameplay data..."):
    raw_df = load_all_data(DATA_INPUT_PATH) 
    df = map_coords(raw_df)

if not df.empty:
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Filter Map & Match")
    selected_map = st.sidebar.selectbox("Select Map", df['map_id'].unique())
    map_df = df[df['map_id'] == selected_map]

    match_list = map_df['match_id'].unique()
    selected_match = st.sidebar.selectbox("Select Match ID", match_list)
    match_data = map_df[map_df['match_id'] == selected_match].sort_values('ts')

    # --- TABBED VIEW ---
    tab1, tab2 = st.tabs(["Match Playback", "Map Heatmaps"])

    with tab1:
        # Playback Slider Logic
        match_data['seconds'] = (match_data['ts'] - match_data['ts'].min()).dt.total_seconds().astype(int)
        max_sec = int(match_data['seconds'].max())
        time_slice = st.slider("Match Timeline (Seconds)", 0, max_sec, max_sec)
        
        current_data = match_data[match_data['seconds'] <= time_slice]
        
        fig = px.scatter(current_data, x="px", y="py", color="event", symbol="is_bot",
                         hover_name="user_id", title=f"Match Replay: {selected_match}")
        
        # Robust Background Image Loader (PNG/JPG Fix)
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
        st.subheader(f"Global Heatmap: {selected_map}")
        event_filter = st.multiselect("Select Events for Heatmap", df['event'].unique(), default=['Kill', 'Killed'])
        heat_df = map_df[map_df['event'].isin(event_filter)]
        
        fig_heat = px.density_heatmap(heat_df, x="px", y="py", nbinsx=50, nbinsy=50, 
                                      color_continuous_scale="Reds", title="Combat Density Map")
        
        # Add background image to heatmap too
        for ext in ['.png', '.jpg']:
            img_path = f"minimaps/{selected_map}_Minimap{ext}"
            if os.path.exists(img_path):
                img = Image.open(img_path)
                fig_heat.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", opacity=0.8, layer="below"))
                break

        fig_heat.update_xaxes(range=[0, 1024], visible=False)
        fig_heat.update_yaxes(range=[1024, 0], visible=False)
        st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.warning("No data loaded. Check your path configuration at the top of the file.")