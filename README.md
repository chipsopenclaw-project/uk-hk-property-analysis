# 🏠 UK HK Property Analysis

> Investigating whether the Hong Kong BNO migration wave (2020–2022) correlates with observable changes in UK residential property prices and transaction volumes.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/chipsopenclaw-project/uk-hk-property-analysis)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC?logo=terraform)](https://www.terraform.io/)
[![Azure](https://img.shields.io/badge/Cloud-Azure-0089D6?logo=microsoftazure)](https://azure.microsoft.com/)
[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=githubactions)](https://github.com/features/actions)

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Data Sources](#data-sources)
- [Analysis Framework](#analysis-framework)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Map Visualisation](#map-visualisation)
- [Getting Started](#getting-started)
- [CI/CD Pipeline](#cicd-pipeline)
- [Dashboard](#dashboard)

---

## 🎯 Project Overview

This project analyses **8.9 million Land Registry transactions** (2017–present) to investigate whether the arrival of Hong Kong BNO migrants correlates with property price changes in known HK community areas across England and Wales.

**Important caveat:** Land Registry Price Paid Data does not record buyer nationality. All findings represent time-period correlations, not causal evidence of direct impact.

### Key Questions

- Did property prices in known HK community areas rise faster than the national average during the BNO migration period?
- Did transaction volumes change in these areas?
- Which postcode districts show the strongest correlation?

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub + GitHub Actions                    │
│         Terraform CI/CD · ADF Deploy · Synapse Deploy        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Azure Data Factory                         │
│   Monthly Schedule Trigger → Download Land Registry CSV      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Azure Data Lake Storage Gen2                     │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  Bronze  │ →  │  Silver  │ →  │   Gold   │              │
│  │ Raw CSV  │    │  Parquet │    │  Tables  │              │
│  └──────────┘    └──────────┘    └──────────┘              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Azure Synapse Analytics                         │
│         PySpark · Bronze→Silver · Silver→Gold               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Streamlit Cloud                             │
│     Price Timeline · UK Maps · HK Community Analysis        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Sources

| Dataset | Source | Volume | Use |
|---------|--------|--------|-----|
| Price Paid Data (Historical) | HM Land Registry | 8.9M+ records (2017–2025) | Property prices & transaction volumes |
| Price Paid Data (Monthly) | HM Land Registry | ~16MB/month | Incremental monthly updates |

All data is publicly available under the **Open Government Licence v3.0**.

---

## 🔬 Analysis Framework

### Time Periods

Rather than hard-cutting periods, this project uses a **dual-flag approach (Method C)** to handle the LOTR/BNO policy overlap:

| Flag | Date Range | Description |
|------|-----------|-------------|
| `is_baseline` | Jan 2017 – Jun 2020 | Pre-migration baseline |
| `is_lotr_active` | Jul 2020 – Jul 2021 | LOTR transitional period |
| `is_bno_active` | Jan 2021 – Dec 2022 | BNO Visa formal launch |
| `is_post_wave` | Jan 2023 – present | Post-migration stabilisation |

This allows flexible analysis of the Jan–Jul 2021 overlap period where both policies were simultaneously active.

### HK Community Areas

25 postcode districts identified as having high or medium HK community concentration, across:

| Region | Key Postcodes | Concentration |
|--------|--------------|---------------|
| Manchester (Altrincham) | WA14, WA15 | High |
| Manchester (Sale) | M33 | High |
| London (Sutton) | SM1, SM2, SM3 | High |
| London (Kingston) | KT1, KT2 | High |
| London (Croydon) | CR0 | High |
| Birmingham (Solihull) | B90, B91 | High |
| Manchester (Worsley) | M28 | Medium |
| Manchester (Whitefield) | M45 | Medium |
| Manchester (Didsbury) | M20 | Medium |
| Warrington | WA4, WA5 | Medium |
| Reading | RG1, RG2, RG6 | Medium |
| ... | ... | ... |

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|-----------|
| **Cloud** | Microsoft Azure |
| **IaC** | Terraform |
| **Orchestration** | Azure Data Factory |
| **Storage** | Azure Data Lake Storage Gen2 |
| **Compute** | Azure Synapse Analytics (Spark 3.4) |
| **Transformation** | PySpark |
| **Dashboard** | Streamlit Cloud |
| **Mapping** | Folium + Plotly Scatter Mapbox |
| **CI/CD** | GitHub Actions |
| **Testing** | pytest + pyspark |
| **Secrets** | Azure Key Vault |
| **Container** | Azure Container Registry |

---

## 📁 Project Structure

```
uk-hk-property-analysis/
├── .github/
│   └── workflows/
│       ├── terraform.yml          # Terraform plan/apply on push
│       ├── adf-deploy.yml         # Deploy ADF linked services, datasets, pipelines
│       ├── synapse-deploy.yml     # Upload PySpark scripts to ADLS + run tests
│       └── streamlit-deploy.yml   # Build & deploy Streamlit Docker image
│
├── terraform/
│   ├── main.tf                    # Root module
│   ├── variables.tf
│   ├── outputs.tf
│   ├── locals.tf
│   ├── environments/
│   │   ├── dev.tfvars
│   │   └── dev.backend.hcl
│   └── modules/
│       ├── storage/               # ADLS Gen2 + Bronze/Silver/Gold filesystems
│       ├── adf/                   # Azure Data Factory + Linked Services
│       ├── synapse/               # Synapse Workspace + Spark Pool
│       ├── container/             # ACR + Container Apps
│       ├── keyvault/              # Key Vault
│       └── monitoring/            # Log Analytics + App Insights
│
├── adf/
│   ├── linked_services/           # ADF Linked Service JSON definitions
│   │   ├── ls_http_land_registry.json
│   │   ├── ls_http_land_registry_monthly.json
│   │   └── ls_synapse_dev.json
│   ├── datasets/                  # ADF Dataset JSON definitions
│   │   ├── ds_http_land_registry_monthly.json
│   │   └── ds_adls_bronze_land_registry.json
│   ├── pipelines/                 # ADF Pipeline JSON definitions
│   │   ├── pl_land_registry_historical.json
│   │   └── pl_land_registry_monthly.json
│   └── triggers/                  # ADF Schedule Trigger JSON definitions
│       └── tr_monthly_land_registry.json
│
├── synapse/
│   ├── notebooks/
│   │   ├── bronze_to_silver.py    # PySpark: clean + add period flags
│   │   └── silver_to_gold.py      # PySpark: aggregate + build Gold tables
│   └── tests/
│       ├── conftest.py            # Shared pytest fixtures (local SparkSession)
│       └── test_bronze_to_silver.py  # 7 unit tests for transformation logic
│
├── streamlit/
│   ├── app.py                     # Main Streamlit dashboard
│   ├── requirements.txt
│   ├── Dockerfile
│   └── data/
│       └── uk_districts.geojson   # UK Local Authority District boundaries
│
├── config/
│   └── hk_community_areas.json    # HK community postcode districts with coordinates
│
└── scripts/
    ├── deploy_adf_linked_services.py
    ├── deploy_adf_datasets.py
    └── deploy_adf_triggers.py
```

---

## ⚙️ How It Works

### 1. Data Ingestion (ADF)

**Historical load (one-time):**
```
ADF Pipeline: pl_land_registry_historical
└── Downloads pp-2017.csv through pp-2025.csv
└── Stores in: bronze/land-registry/historical/
```

**Monthly incremental (automated):**
```
Schedule Trigger: Every 1st of month at 06:00 UTC
└── ADF Pipeline: pl_land_registry_monthly
    ├── CopyMonthlyCSV → bronze/land-registry/monthly/YYYY-MM/
    ├── BronzeToSilver (Synapse Spark Job via Livy API)
    ├── WaitForBronzeToSilver
    └── SilverToGold (Synapse Spark Job via Livy API)
```

### 2. Bronze → Silver (PySpark)

```python
# Key transformations:
- Filter: record_status == "A" (active records only)
- Filter: price > 0, postcode not null
- Extract: postcode_district from postcode (e.g. "WA14" from "WA14 1AA")
- Add: is_baseline, is_lotr_active, is_bno_active, is_post_wave flags
- Remove: duplicates by transaction_id
- Cap: outliers at 99.5th percentile
- Write: Parquet partitioned by year
```

### 3. Silver → Gold (PySpark)

```python
# Gold tables produced:
- price_by_postcode_period    # Median price by postcode + period
- price_monthly_timeseries    # Monthly median price trends
- uplift_summary              # P0 vs P2 price uplift %
- hk_vs_national_comparison   # HK areas vs national average
```

---

## 🗺️ Map Visualisation

The dashboard includes two complementary maps:

### Plotly Scatter Mapbox — Price Uplift
Shows HK community postcode districts coloured by price uplift % (P0 Baseline vs P2 BNO period):
- 🟢 Green = positive uplift (prices rose more than baseline)
- 🔴 Red = negative uplift (prices fell relative to baseline)
- Circle size = transaction volume

Built using real postcode centroid coordinates stored in `config/hk_community_areas.json`.

### Folium Interactive Map — HK Community Areas
Shows all 25 HK community postcode districts with clickable popups:
- 🔴 Red markers = High HK concentration
- 🟠 Orange markers = Medium HK concentration
- Click any marker for postcode, town, and notes

Coordinates are loaded dynamically from ADLS config at runtime — no hardcoding.

---

## 🚀 Getting Started

### Prerequisites

```bash
# Install required tools
az --version        # Azure CLI >= 2.50
terraform --version # Terraform >= 1.6
gh --version        # GitHub CLI
```

### 1. Bootstrap Terraform State Storage

```bash
az group create --name rg-ukhkprop-tfstate --location uksouth
az storage account create --name stukhkproptfstate \
  --resource-group rg-ukhkprop-tfstate --location uksouth \
  --sku Standard_LRS --kind StorageV2
az storage container create --name tfstate \
  --account-name stukhkproptfstate
```

### 2. Create Service Principal

```bash
az ad sp create-for-rbac \
  --name "sp-ukhkprop-terraform" \
  --role Contributor \
  --scopes /subscriptions/<YOUR_SUBSCRIPTION_ID>
```

### 3. Set Environment Variables

```bash
export ARM_CLIENT_ID="..."
export ARM_CLIENT_SECRET="..."
export ARM_SUBSCRIPTION_ID="..."
export ARM_TENANT_ID="..."
```

### 4. Deploy Infrastructure

```bash
cd terraform
terraform init -backend-config=environments/dev.backend.hcl
terraform plan -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

### 5. Set GitHub Secrets

```bash
gh secret set ARM_CLIENT_ID --body "..."
gh secret set ARM_CLIENT_SECRET --body "..."
gh secret set ARM_SUBSCRIPTION_ID --body "..."
gh secret set ARM_TENANT_ID --body "..."
```

### 6. Run Historical Data Load

```bash
az datafactory pipeline create-run \
  --factory-name "adf-ukhkprop-dev" \
  --resource-group "rg-ukhkprop-dev" \
  --name "pl_land_registry_historical"
```

---

## 🔄 CI/CD Pipeline

| Workflow | Trigger | What it does |
|----------|---------|-------------|
| `terraform.yml` | Push to `terraform/**` | Plan on PR, Apply on merge to main |
| `adf-deploy.yml` | Push to `adf/**` | Deploy Linked Services, Datasets, Pipelines, Triggers |
| `synapse-deploy.yml` | Push to `synapse/**` | Run unit tests → Upload PySpark scripts to ADLS |
| `streamlit-deploy.yml` | Push to `streamlit/**` | Build Docker image → Push to ACR → Update Container App |

---

## 📈 Dashboard

The Streamlit dashboard includes 5 tabs:

| Tab | Content |
|-----|---------|
| 📈 Price Timeline | Monthly median price with LOTR + BNO period shading |
| 🗺️ UK Map | Price uplift scatter map + HK community Folium map |
| 🏘️ HK Community | HK areas vs national average by period |
| 📊 Uplift Analysis | Top districts by price uplift % and volume change |
| 📋 Raw Data | Filterable data table with CSV download |

---

## ⚠️ Limitations & Caveats

- **Buyer identity unknown** — Land Registry data records no nationality or ethnicity
- **Correlation only** — No causal inference can be drawn
- **Confounding factors** — Stamp Duty Holiday (Jul 2020–Sep 2021), WFH shift, low interest rates all overlap the analysis period
- **Registration lag** — Property transactions take 2–6 months to appear in the dataset
- **2025 data partial** — Recent year data is incomplete due to registration delays

---

## 📄 Licence

Data sourced from HM Land Registry © Crown copyright and database right 2024. Licensed under the [Open Government Licence v3.0](http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

Project code licensed under [MIT License](LICENSE).
