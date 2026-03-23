import streamlit as st
import ee
from streamlit_oauth import OAuth2Component
import requests
import folium
from streamlit_folium import folium_static

# 1. Provide your identifiers (these are placeholders - use st.secrets!)
CLIENT_ID = st.secrets.get("auth", {}).get("client_id", "YOUR_CLIENT_ID_HERE")
CLIENT_SECRET = st.secrets.get("auth", {}).get("client_secret", "YOUR_CLIENT_SECRET_HERE")
PROJECT_ID = st.secrets.get("gee", {}).get("project_id", "YOUR_PROJECT_ID_HERE")

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
# CRITICAL: This scope is required for Earth Engine
SCOPES = "openid profile email https://www.googleapis.com/auth/earthengine"

# Set up page config
st.set_page_config(page_title="GEE User Login (No Geemap)", layout="wide")

def app():
    st.title("🔐 Earth Engine (User-Specific Login)")
    st.markdown("### Using `streamlit-oauth` for GEE authorized login.")

    # Initialize OAuth component
    # For local testing, use http://localhost:8501
    oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, REVOKE_URL, REVOKE_URL)

    if "auth" not in st.session_state:
        # Show login button
        result = oauth2.authorize_button(
            name="Log in with Google (GEE)",
            redirect_uri="http://localhost:8501", # Should match GCloud Console
            scope=SCOPES,
            key="google_auth",
            extras_params={"prompt": "consent", "access_type": "offline"}
        )
        if result:
            st.session_state["auth"] = result
            st.rerun()
    else:
        # User is logged in
        token = st.session_state["auth"]["access_token"]
        
        # Logout button
        if st.button("Log out"):
            del st.session_state["auth"]
            st.rerun()

        # Initialize EE using the user's token
        try:
            from google.oauth2.credentials import Credentials
            creds = Credentials(token)
            ee.Initialize(creds, project=PROJECT_ID)
            st.success(f"Successfully authenticated as project: `{PROJECT_ID}`")
            
            # Simple GEE Logic: Landsat 8 Median
            l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_TOA") \
                .filterDate("2023-01-01", "2023-12-31") \
                .median()
            
            vis_params = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 0.3}
            m = folium.Map(location=[28.6139, 77.2090], zoom_start=10)
            
            # Custom EE layer helper
            def add_ee_layer(self, ee_object, vis_params, name):
                map_id_dict = ee.Image(ee_object).getMapId(vis_params)
                folium.raster_layers.TileLayer(
                    tiles=map_id_dict['tile_fetcher'].url_format,
                    attr='Map Data &copy; Google Earth Engine',
                    name=name,
                    overlay=True,
                    control=True
                ).add_to(self)
            
            add_ee_layer(m, l8, vis_params, 'Landsat 8 (2023)')
            folium_static(m, width=1200)

        except Exception as e:
            st.error(f"Failed to initialize Earth Engine: {e}")

if __name__ == "__main__":
    app()
