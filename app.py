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
# Set to False for GitHub/Streamlit Cloud deployment
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
            
            # Extract Date from folder structure
            path_parts = f.split(os.sep)
            df['date'] = path_parts[-2] if len(path_parts) >= 2 else "Unknown"

            # Decode byte-string events
            df['event'] = df['event'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
            
            # Identify bots vs humans
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
        # World X/Z to 1024x1024 Pixel Space
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
    st.sidebar.header("Data Filters")
    
    # 1. Date Filter
    all_dates = sorted(df['date'].unique())
    selected_dates = st.sidebar.multiselect("Select Dates", all_dates, default=all_dates)
    date_filtered_df = df[df['date'].isin(selected_dates)]
    
    if not date_filtered_df.empty:
        # 2. Map Filter
        available_maps = sorted(date_filtered_df['map_id'].unique())
        selected_map = st.sidebar.selectbox("Select Map", available_maps)
        map_df = date_filtered_df[date_filtered_df['map_id'] == selected_map]

        # 3. Match Filter
        match_list = sorted(map_df['match_id'].unique())
        selected_match = st.sidebar.selectbox("Select Match ID", match_list)
        match_data = map_df[map_df['match_id'] == selected_match].sort_values('ts')

        # --- TABBED VIEW ---
        tab1, tab2 = st.tabs(["🎥 Match Playback", "🔥 Map Heatmaps"])

        with tab1:
            if not match_data.empty:
                match_data['seconds'] = (match_data['ts'] - match_data['ts'].min()).dt.total_seconds().astype(int)
                max_sec = int(match_data['seconds'].max())
                
                if max_sec > 0:
                    time_slice = st.slider("Match Timeline (Seconds)", 0, max_sec, max_sec)
                else:
                    st.info("⏱️ This match has a single time-stamp. Showing all events.")
                    time_slice = 0
                
                current_data = match_data[match_data['seconds'] <= time_slice]
                fig = px.scatter(current_data, x="px", y="py", color="event", symbol="is_bot",
                                 hover_name="user_id", title=f"Match Replay: {selected_match}")
                
                for ext in ['.png', '.jpg']:
                    img_path = f"minimaps/{selected_map}_Minimap{ext}"
                    if os.path.exists(img_path):
                        img = Image.open(img_path)
                        fig.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", opacity=0.7, layer="below"))
                        break
                        
                fig.update_xaxes(range=[0, 1024], visible=False)
                fig.update_yaxes(range=[1024, 0], visible=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data found for this match.")

        with tab2:
            st.subheader(f"Global Heatmap: {selected_map}")
            event_filter = st.multiselect("Select Events", sorted(df['event'].unique()), default=['Kill', 'Killed'])
            heat_df = map_df[map_df['event'].isin(event_filter)]
            
            if not heat_df.empty:
                fig_heat = px.density_heatmap(
                    heat_df, x="px", y="py", 
                    nbinsx=50, nbinsy=50, 
                    range_x=[0, 1024], range_y=[1024, 0],
                    color_continuous_scale="Reds", 
                    title=f"Combat Density: {selected_map}"
                )
                
                for ext in ['.png', '.jpg']:
                    img_path = f"minimaps/{selected_map}_Minimap{ext}"
                    if os.path.exists(img_path):
                        img = Image.open(img_path)
                        fig_heat.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", opacity=0.8, layer="below"))
                        break

                fig_heat.update_xaxes(visible=False)
                fig_heat.update_yaxes(visible=False)
                fig_heat.update_layout(margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.info("Select events to generate a heatmap.")
    else:
        st.info("Please select at least one date in the sidebar.")
else:
    st.error("No data could be loaded. Check your 'player_data' folder.")s