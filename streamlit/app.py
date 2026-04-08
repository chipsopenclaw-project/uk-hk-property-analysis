# app.py
# UK HK Property Analysis - Streamlit Dashboard
# Reads Gold layer from ADLS and visualises price trends,
# HK community comparisons, and geographic distributions.

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import json
import os
from azure.storage.blob import BlobServiceClient

# ── Page Config ────────────────────────────────────────────
st.set_page_config(
    page_title="UK HK Property Analysis",
    page_icon="🏠",
    layout="wide"
)

# ── Constants ──────────────────────────────────────────────
STORAGE_ACCOUNT = os.environ.get("STORAGE_ACCOUNT", "stukhkpropdev")
GOLD_CONTAINER  = "gold"

AZURE_CLIENT_ID     = st.secrets.get("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET = st.secrets.get("AZURE_CLIENT_SECRET", "")
AZURE_TENANT_ID     = st.secrets.get("AZURE_TENANT_ID", "")

PERIOD_LABELS = {
    "P0_baseline":   "P0 Baseline (2017-2020)",
    "P1_lotr_only":  "P1 LOTR Only (Jul-Jan 2021)",
    "P1P2_overlap":  "P1+P2 Overlap (Jan-Jul 2021)",
    "P2_bno_only":   "P2 BNO Only (Jul 2021-Dec 2022)",
    "P3_post_wave":  "P3 Post-wave (2023+)",
}

HK_CONCENTRATION_COLORS = {
    "high":   "#FF4B4B",
    "medium": "#FFA500",
    "none":   "#AAAAAA",
}

# ── Data Loading ───────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_parquet_from_adls(container: str, blob_prefix: str) -> pd.DataFrame:
    """Load Parquet files from ADLS Gold layer into Pandas DataFrame."""
    try:
        from azure.identity import ClientSecretCredential
        credential = ClientSecretCredential(
            tenant_id=AZURE_TENANT_ID,
            client_id=AZURE_CLIENT_ID,
            client_secret=AZURE_CLIENT_SECRET
        )
        account_url = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net"
        client = BlobServiceClient(account_url=account_url, credential=credential)
        container_client = client.get_container_client(container)
        blobs = [b.name for b in container_client.list_blobs(name_starts_with=blob_prefix)
                 if b.name.endswith(".parquet")]
        if not blobs:
            return pd.DataFrame()
        dfs = []
        for blob_name in blobs:
            blob_client = container_client.get_blob_client(blob_name)
            data = blob_client.download_blob().readall()
            import io
            dfs.append(pd.read_parquet(io.BytesIO(data)))
        return pd.concat(dfs, ignore_index=True)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_geojson():
    """Load UK district GeoJSON for map visualisation."""
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    geojson_path = os.path.join(base_dir, "data", "uk_districts.geojson")
    with open(geojson_path) as f:
        return json.load(f)

# ── Sidebar ────────────────────────────────────────────────
st.sidebar.title("🏠 UK HK Property Analysis")
st.sidebar.markdown("---")

selected_periods = st.sidebar.multiselect(
    "Select periods",
    options=list(PERIOD_LABELS.keys()),
    default=["P0_baseline", "P2_bno_only"],
    format_func=lambda x: PERIOD_LABELS[x]
)

selected_concentration = st.sidebar.multiselect(
    "HK concentration",
    options=["high", "medium", "none"],
    default=["high", "medium"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Data source:** HM Land Registry Price Paid")
st.sidebar.markdown("**Analysis period:** 2017 – present")

# ── Main Title ─────────────────────────────────────────────
st.title("🏠 HK BNO Migration vs UK Property Prices")
st.markdown("Analysing correlation between BNO migration wave and UK residential property price changes.")
st.markdown("---")

# ── Load Data ──────────────────────────────────────────────
with st.spinner("Loading data from Azure..."):
    df_timeseries = load_parquet_from_adls(GOLD_CONTAINER, "land-registry/price_monthly_timeseries")
    df_uplift     = load_parquet_from_adls(GOLD_CONTAINER, "land-registry/uplift_summary")
    df_hk_nat     = load_parquet_from_adls(GOLD_CONTAINER, "land-registry/hk_vs_national_comparison")
    df_postcode   = load_parquet_from_adls(GOLD_CONTAINER, "land-registry/price_by_postcode_period")
    geojson       = load_geojson()

# ── Check if data is available ─────────────────────────────
data_available = not df_timeseries.empty

if not data_available:
    st.warning("No data available yet. Please run the ADF pipeline to load Land Registry data.")
    st.info("Once data is loaded, this dashboard will show price trends and HK community analysis.")
    st.stop()

# ── Tab Layout ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Price Timeline",
    "🗺️ UK Map",
    "🏘️ HK Community",
    "📊 Uplift Analysis",
    "📋 Raw Data"
])

# ── Tab 1: Price Timeline ──────────────────────────────────
with tab1:
    st.subheader("Monthly Median Price Timeline")

    if not df_timeseries.empty:
        # Filter by selected concentration
        df_filtered = df_timeseries[
            df_timeseries["hk_concentration"].isin(selected_concentration)
        ]

        # Add period shading
        fig = go.Figure()

        # Add LOTR period shading
        fig.add_vrect(
            x0="2020-07", x1="2021-07",
            fillcolor="lightblue", opacity=0.2,
            layer="below", line_width=0,
            annotation_text="LOTR", annotation_position="top left"
        )

        # Add BNO period shading
        fig.add_vrect(
            x0="2021-01", x1="2022-12",
            fillcolor="lightyellow", opacity=0.2,
            layer="below", line_width=0,
            annotation_text="BNO Visa", annotation_position="top right"
        )

        # Plot top HK community areas
        top_areas = df_filtered[df_filtered["hk_concentration"] == "high"]["postcode_district"].unique()[:6]
        for area in top_areas:
            area_df = df_filtered[df_filtered["postcode_district"] == area].sort_values("year_month")
            fig.add_trace(go.Scatter(
                x=area_df["year_month"],
                y=area_df["median_price"],
                mode="lines",
                name=area,
                line=dict(width=2)
            ))

        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Median Price (£)",
            hovermode="x unified",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

# ── Tab 2: UK Map ──────────────────────────────────────────
with tab2:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Price Uplift Choropleth (Plotly)")
        if not df_uplift.empty:
            fig_map = px.choropleth(
                df_uplift,
                geojson=geojson,
                locations="county",
                featureidkey="properties.LAD13NM",
                color="price_uplift_pct",
                color_continuous_scale="RdYlGn",
                range_color=[-10, 30],
                labels={"price_uplift_pct": "Price Uplift (%)"},
                title="P0 vs P2 Price Uplift by District"
            )
            fig_map.update_geos(
                fitbounds="locations",
                visible=False
            )
            fig_map.update_layout(height=500)
            st.plotly_chart(fig_map, use_container_width=True)

    with col2:
        st.subheader("HK Community Areas (Folium)")
        m = folium.Map(location=[52.5, -1.5], zoom_start=6)

        if not df_postcode.empty:
            hk_areas = df_postcode[
                df_postcode["hk_concentration"].isin(["high", "medium"])
            ].drop_duplicates("postcode_district")

            for _, row in hk_areas.iterrows():
                color = HK_CONCENTRATION_COLORS.get(row["hk_concentration"], "gray")
                folium.CircleMarker(
                    location=[51.5, -0.1],  # placeholder - replace with postcode centroid
                    radius=8,
                    color=color,
                    fill=True,
                    popup=f"{row['postcode_district']}: {row['hk_concentration']} concentration"
                ).add_to(m)

        st_folium(m, height=500, use_container_width=True)

# ── Tab 3: HK Community vs National ───────────────────────
with tab3:
    st.subheader("HK Community Areas vs National Average")

    if not df_hk_nat.empty:
        df_hk_filtered = df_hk_nat[df_hk_nat["period"].isin(selected_periods)]

        fig_compare = go.Figure()
        fig_compare.add_trace(go.Bar(
            x=df_hk_filtered["period"].map(PERIOD_LABELS),
            y=df_hk_filtered["hk_median_price"],
            name="HK Community Areas",
            marker_color="#FF4B4B"
        ))
        fig_compare.add_trace(go.Bar(
            x=df_hk_filtered["period"].map(PERIOD_LABELS),
            y=df_hk_filtered["national_median_price"],
            name="National Average",
            marker_color="#4B4BFF"
        ))
        fig_compare.update_layout(
            barmode="group",
            xaxis_title="Period",
            yaxis_title="Median Price (£)",
            height=450
        )
        st.plotly_chart(fig_compare, use_container_width=True)

        # Premium % table
        st.subheader("HK Community Price Premium vs National")
        st.dataframe(
            df_hk_filtered[["period", "hk_concentration", "hk_median_price",
                            "national_median_price", "premium_pct"]]
            .rename(columns={
                "period": "Period",
                "hk_concentration": "HK Concentration",
                "hk_median_price": "HK Median (£)",
                "national_median_price": "National Median (£)",
                "premium_pct": "Premium (%)"
            }),
            use_container_width=True
        )

# ── Tab 4: Uplift Analysis ─────────────────────────────────
with tab4:
    st.subheader("Price Uplift: Baseline vs BNO Period")

    if not df_uplift.empty:
        df_uplift_sorted = df_uplift.sort_values("price_uplift_pct", ascending=False)

        # Top 15 districts by uplift
        fig_uplift = px.bar(
            df_uplift_sorted.head(15),
            x="postcode_district",
            y="price_uplift_pct",
            color="hk_concentration",
            color_discrete_map=HK_CONCENTRATION_COLORS,
            labels={
                "postcode_district": "Postcode District",
                "price_uplift_pct": "Price Uplift (%)",
                "hk_concentration": "HK Concentration"
            },
            title="Top 15 Districts by Price Uplift (P0 vs P2)"
        )
        fig_uplift.update_layout(height=450)
        st.plotly_chart(fig_uplift, use_container_width=True)

        # Volume change
        fig_volume = px.bar(
            df_uplift_sorted.head(15),
            x="postcode_district",
            y="volume_change_pct",
            color="hk_concentration",
            color_discrete_map=HK_CONCENTRATION_COLORS,
            labels={
                "postcode_district": "Postcode District",
                "volume_change_pct": "Volume Change (%)",
                "hk_concentration": "HK Concentration"
            },
            title="Transaction Volume Change (P0 vs P2)"
        )
        fig_volume.update_layout(height=450)
        st.plotly_chart(fig_volume, use_container_width=True)

# ── Tab 5: Raw Data ────────────────────────────────────────
with tab5:
    st.subheader("Raw Data Explorer")

    dataset = st.selectbox(
        "Select dataset",
        ["Price by Postcode & Period", "Monthly Timeseries",
         "Uplift Summary", "HK vs National"]
    )

    df_map = {
        "Price by Postcode & Period": df_postcode,
        "Monthly Timeseries": df_timeseries,
        "Uplift Summary": df_uplift,
        "HK vs National": df_hk_nat
    }

    selected_df = df_map[dataset]
    st.dataframe(selected_df, use_container_width=True)
    st.download_button(
        label="Download CSV",
        data=selected_df.to_csv(index=False),
        file_name=f"{dataset.lower().replace(' ', '_')}.csv",
        mime="text/csv"
    )
