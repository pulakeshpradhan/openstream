# Earth Engine Streamlit App (Native Auth)

A high-performance Streamlit application for Google Earth Engine (GEE) that avoids `geemap` and uses native `ee` + `folium` integration.

## 🚀 Setup Instructions

1.  **Google Cloud Project**:
    - Ensure you have a Google Cloud Project with the Earth Engine API enabled.
    - Generate a **Service Account JSON Key** (recommended for Streamlit deployment).

2.  **Streamlit Secrets**:
    - Open `.streamlit/secrets.toml`.
    - Fill in your `PROJECT_ID`.
    - Paste your service account JSON details into the `[gcp_service_account]` section.

3.  **Local Development**:
    - Ensure you have `gcloud` CLI installed and authenticated (`gcloud auth application-default login`) if you want to use your personal credentials.

## 🛠 Features

- **Auth Flexibility**: Supports Service Account JSON or ADC (for local dev).
- **Direct GEE API**: Uses the pure `ee` library logic for better control and performance over `geemap`.
- **Dynamic Mapping**: Interactive `folium` map integration via `streamlit-folium`.
- **Clean Architecture**: Placeholder-based management via Streamlit Secrets.

## ⚠️ Known Limitation

The built-in `st.login("google")` is currently restricted to **OIDC (Identity)** scopes (`openid`, `profile`, `email`) and cannot authorize the `earthengine` scope. For user-specific GEE logins, use a library like `streamlit-oauth` to request `https://www.googleapis.com/auth/earthengine`.
