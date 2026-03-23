import streamlit as st
import ee
import folium
from streamlit_folium import folium_static
from google.oauth2 import service_account
import json

# Set up page config
st.set_page_config(page_title="Earth Engine Viewer (Native)", layout="wide")

# 1. Define Placeholders/Constants
# These should ideally come from st.secrets in local dev or Streamlit Cloud
PROJECT_ID = st.secrets.get("gee", {}).get("project_id", "YOUR_PROJECT_ID_HERE")

def initialize_ee():
    """Initializes Earth Engine using service account or ADC."""
    if "ee_initialized" not in st.session_state:
        try:
            # Check if Service Account credentials are provided in st.secrets
            if "gcp_service_account" in st.secrets:
                sa_info = dict(st.secrets["gcp_service_account"])
                # Handle potential key formatting issues in secrets
                if "\\n" in sa_info["private_key"]:
                    sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")
                
                creds = service_account.Credentials.from_service_account_info(sa_info)
                ee.Initialize(creds, project=PROJECT_ID)
            else:
                # Fallback to Application Default Credentials (ADC)
                # Useful for local dev if 'gcloud auth application-default login' was run
                ee.Initialize(project=PROJECT_ID)
            
            st.session_state["ee_initialized"] = True
            return True
        except Exception as e:
            st.error(f"Earth Engine Initialization Failed: {e}")
            return False
    return True

# Helper to add EE layer to folium
def add_ee_layer(self, ee_object, vis_params, name):
    """Function to add GEE data as a folium layer."""
    map_id_dict = ee.Image(ee_object).getMapId(vis_params)
    folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
        name=name,
        overlay=True,
        control=True
    ).add_to(self)

# Register the helper to Folium
folium.Map.add_ee_layer = add_ee_layer

# App Main UI
st.title("🌍 Google Earth Engine (Direct API)")
st.markdown("### Simple Viewer (No `geemap`)")

if initialize_ee():
    st.success(f"Connected to Earth Engine Project: `{PROJECT_ID}`")
    
    # Sidebar for controls
    st.sidebar.header("Map Controls")
    year = st.sidebar.slider("Select Year (Landsat 8 Top of Atmosphere)", 2013, 2023, 2023)
    
    # Simple GEE Logic: Landsat 8 Median
    try:
        # Load Landsat 8 TOA collection
        l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_TOA") \
            .filterDate(f"{year}-01-01", f"{year}-12-31") \
            .median()
        
        # Visualization parameters
        vis_params = {
            'bands': ['B4', 'B3', 'B2'],
            'min': 0,
            'max': 0.3,
            'gamma': 1.4,
        }
        
        # Create Folium Map
        m = folium.Map(location=[28.6139, 77.2090], zoom_start=10, control_scale=True)
        
        # Add GEE Layer
        m.add_ee_layer(l8, vis_params, f'Landsat 8 ({year})')
        
        # Add Layer Control
        folium.LayerControl().add_to(m)
        
        # Display the map
        folium_static(m, width=1200)
        
    except Exception as e:
        st.error(f"Error loading GEE layer: {e}")

else:
    st.warning("Please configure your credentials in `.streamlit/secrets.toml` or via Environment Variables.")
    st.code("""
[gee]
project_id = "your-project-id"

[gcp_service_account]
type = "service_account"
... (Full JSON contents)
    """, language="toml")
