import streamlit as st
import ee
import folium
from streamlit_folium import st_folium
from google.oauth2 import service_account
import json
from datetime import datetime, timedelta

# Set up page config
st.set_page_config(page_title="GEE Terrain & Analysis Template", layout="wide", page_icon="⛰️")

# Helper to add GEE layer to Folium
def add_ee_layer(self, ee_object, vis_params, name):
    try:
        if isinstance(ee_object, ee.ImageCollection):
            ee_object = ee_object.median()
        map_id_dict = ee.Image(ee_object).getMapId(vis_params)
        folium.raster_layers.TileLayer(
            tiles=map_id_dict['tile_fetcher'].url_format,
            attr='Map Data &copy; Google Earth Engine',
            name=name,
            overlay=True,
            control=True
        ).add_to(self)
    except Exception as e:
        st.error(f"Error adding EE layer '{name}': {e}")

folium.Map.add_ee_layer = add_ee_layer

st.title("🌋 GEE Template: Terrain & Custom Analysis")

# --- SIDEBAR: ONLY AUTHENTICATION ---
with st.sidebar:
    st.header("🔑 Connection & Auth")
    project_id = st.text_input("Project ID", value=st.session_state.get("project_id", ""), placeholder="GEE Project ID")
    uploaded_file = st.file_uploader("Service Account JSON", type=["json"])
    
    st.markdown("🔗 [Get Key](https://console.cloud.google.com/iam-admin/serviceaccounts)")
    st.markdown("📖 [Get read blog post on hwo to authenticate](https://medium.com/@pulakesh.geo/how-to-authenticate-google-earth-engine-with-streamlit-e62ca7091410)")

    if st.button("🚀 Connect to GEE"):
        if not project_id or uploaded_file is None:
            st.error("Missing Project ID or JSON file.")
        else:
            try:
                content = uploaded_file.read().decode("utf-8")
                sa_info = json.loads(content)
                if "private_key" in sa_info:
                    sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")
                
                SCOPES = ['https://www.googleapis.com/auth/earthengine']
                creds = service_account.Credentials.from_service_account_info(sa_info, scopes=SCOPES)
                ee.Initialize(creds, project=project_id)
                
                st.session_state["project_id"] = project_id
                st.session_state["ee_initialized"] = True
                st.success("Connected!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

# --- MAIN PANEL: ANALYSIS & CUSTOMIZATION ---
if st.session_state.get("ee_initialized"):
    # 1. ANALYSIS SETTINGS (Main Page)
    with st.container():
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.subheader("📅 Timeframe")
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365))
            end_date = st.date_input("End Date", datetime.now())
        
        with col2:
            st.subheader("📊 Dataset Selection")
            # Default to SRTM as requested
            dataset_choice = st.selectbox("Select Data", ["SRTM (Elevation)", "Sentinel-2 (Imagery)", "Landsat 8"])
        
        with col3:
            st.subheader("📍 Location Preview")
            lat = st.number_input("Lat", value=28.6, format="%.4f")
            lon = st.number_input("Lon", value=77.2, format="%.4f")
            zoom = st.slider("Zoom", 1, 18, 10)

    st.markdown("---")

    # 2. DATA PROCESSING
    try:
        # Define AOI
        aoi = ee.Geometry.Point([lon, lat]).buffer(15000)
        
        if dataset_choice == "SRTM (Elevation)":
            dataset = ee.Image("CGIAR/SRTM90_V4")
            elevation = dataset.select('elevation')
            slope = ee.Terrain.slope(elevation)
            
            vis_option = st.radio("Terrain Layer", ["Elevation", "Slope"], horizontal=True)
            
            if vis_option == "Elevation":
                img = elevation
                vis_params = {'min': 0, 'max': 3000, 'palette': ['blue', 'green', 'red']}
            else:
                img = slope
                vis_params = {'min': 0, 'max': 60, 'palette': ['white', 'black']}
                
        elif dataset_choice == "Sentinel-2 (Imagery)":
            col = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                .filterBounds(aoi) \
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            img = col.median()
            vis_params = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}
            st.info("Showing Median Composite for Sentinel-2.")
            
        else: # Landsat 8
            col = ee.ImageCollection("LANDSAT/LC08/C02/T1_TOA") \
                .filterBounds(aoi) \
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            img = col.median()
            vis_params = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 0.3}

        # 3. MAP DISPLAY
        m = folium.Map(location=[lat, lon], zoom_start=zoom, control_scale=True)
        m.add_ee_layer(img, vis_params, dataset_choice)
        folium.LayerControl().add_to(m)
        
        st_folium(m, width="100%", height=600)
        
    except Exception as e:
        st.error(f"Processing Error: {e}")

else:
    st.info("👋 Hello! Use the **Sidebar (Left Panel)** to connect your GEE account. All analysis controls will appear here once connected.")
    
    # Placeholder for Template Look
    st.image("https://img.icons8.com/clouds/256/empty-filter.png", width=100)
    st.write("Layout Template: [Sidebar = Auth] | [Main = Control & Map]")
