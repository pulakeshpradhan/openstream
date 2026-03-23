import streamlit as st
import ee
import folium
from streamlit_folium import st_folium
from google.oauth2 import service_account
import json
import pandas as pd
from datetime import datetime, timedelta

# Set up page config
st.set_page_config(page_title="TerraClimate Analytics", layout="wide", page_icon="🌡️")

# Helper to add GEE layer to Folium
def add_ee_layer(self, ee_object, vis_params, name):
    try:
        if isinstance(ee_object, ee.ImageCollection):
            ee_object = ee_object.mean()
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

st.title("🌡️ TerraClimate: Global Climate Monitoring")

# --- SIDEBAR: ONLY AUTHENTICATION ---
with st.sidebar:
    st.header("🔑 Connection & Auth")
    project_id = st.text_input("Project ID", value=st.session_state.get("project_id", ""), placeholder="GEE Project ID")
    uploaded_file = st.file_uploader("Service Account JSON", type=["json"])
    
    st.markdown("🔗 [Get Key](https://console.cloud.google.com/iam-admin/serviceaccounts)")
    st.markdown("📺 [Watch the Tutorial](https://www.youtube.com/@SpatialGeography)")

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

# --- MAIN PANEL: CLIMATE ANALYSIS ---
if st.session_state.get("ee_initialized"):
    # 1. Compact Controls
    with st.container():
        c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.5, 1])
        
        with c1:
            start_date = st.date_input("Start", datetime(2017, 1, 1))
        with c2:
            end_date = st.date_input("End", datetime(2017, 12, 31))
        with c3:
            sub1, sub2 = st.columns(2)
            lat = sub1.number_input("Lat", value=28.61, format="%.2f")
            lon = sub2.number_input("Lon", value=77.23, format="%.2f")
        with c4:
            zoom = st.number_input("Zoom", 1, 18, 5)

    # 2. Variable Selection
    variables = {
        'tmmx': 'Max Temperature',
        'tmmn': 'Min Temperature',
        'pdsi': 'Palmer Drought Index',
        'pr': 'Precipitation',
        'soil': 'Soil Moisture',
        'aet': 'Evapotranspiration',
        'def': 'Climate Water Deficit',
        'pet': 'Ref Evapotranspiration',
        'ro': 'Runoff',
        'srad': 'Shortwave Radiation',
        'swe': 'Snow Water Equivalent',
        'vap': 'Vapor Pressure',
        'vpd': 'VPD',
        'vs': 'Wind Speed'
    }
    
    col_var, col_actions = st.columns([2, 1])
    with col_var:
        selected_var = st.selectbox("Select Climate Variable", options=list(variables.keys()), format_func=lambda x: variables[x])
    
    st.markdown("---")

    try:
        # Load TerraClimate Collection
        dataset = ee.ImageCollection('IDAHO_EPSCOR/TERRACLIMATE') \
            .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        
        # User defined palette for Max Temperature (and others)
        user_palette = ['1a3678', '2955bc', '5699ff', '8dbae9', 'acd1ff', 'caebff', 'e5f9ff', 'fdffb4', 'ffe6a2', 'ffc969', 'ffa12d', 'ff7c1f', 'ca531a', 'ff0000', 'ab0000']
        
        # Visualization logic
        img = dataset.select(selected_var).mean()
        
        if selected_var in ['tmmx', 'tmmn']:
            # TerraClimate temperatures are scaled by 0.1
            vis_params = {'min': -300.0, 'max': 300.0, 'palette': user_palette}
            st.info(f"Showing Mean {variables[selected_var]} (scaled by 0.1 °C)")
        else:
            vis_params = {'min': 0, 'max': 500, 'palette': ['white', 'blue']}
            st.info(f"Showing Mean {variables[selected_var]}")

        # --- MAP & TIMESERIES ---
        tab_map, tab_chart = st.tabs(["🗺️ Global Map", "📈 Time Series"])
        
        with tab_map:
            m = folium.Map(location=[lat, lon], zoom_start=zoom)
            m.add_ee_layer(img, vis_params, variables[selected_var])
            folium.LayerControl().add_to(m)
            st_folium(m, width="100%", height=600)
            
        with tab_chart:
            st.subheader(f"Temporal Trend: {variables[selected_var]}")
            if st.button("📊 Generate Time Series at Location"):
                with st.spinner("Extracting data..."):
                    point = ee.Geometry.Point([lon, lat])
                    
                    def extract_info(image):
                        date = image.date().format('YYYY-MM-DD')
                        value = image.reduceRegion(ee.Reducer.mean(), point, 1000).get(selected_var)
                        return ee.Feature(None, {'date': date, 'value': value})
                    
                    data_features = dataset.select(selected_var).map(extract_info).getInfo()['features']
                    
                    df = pd.DataFrame([f['properties'] for f in data_features])
                    if not df.empty:
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.set_index('date').sort_index()
                        st.line_chart(df['value'])
                        st.dataframe(df)
                    else:
                        st.warning("No data found for the selected time range/location.")

    except Exception as e:
        st.error(f"Error: {e}")

else:
    st.info("👋 Template Ready! Authenticate in the sidebar to visualize TerraClimate datasets.")
