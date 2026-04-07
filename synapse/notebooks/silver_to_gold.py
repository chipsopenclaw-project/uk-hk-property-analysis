# silver_to_gold.py
# Reads cleaned Parquet from Silver layer,
# aggregates data and writes analysis-ready tables to Gold layer.
# HK community areas loaded from ADLS config (no hardcoding).

import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, median, count, round, avg,
    when, lit, concat_ws
)

# ── Spark Session ──────────────────────────────────────────
spark = SparkSession.builder.appName("silver_to_gold").getOrCreate()

# ── Config ─────────────────────────────────────────────────
STORAGE_ACCOUNT = "stukhkpropdev"
SILVER_PATH = f"abfss://silver@{STORAGE_ACCOUNT}.dfs.core.windows.net/land-registry"
GOLD_PATH   = f"abfss://gold@{STORAGE_ACCOUNT}.dfs.core.windows.net/land-registry"
CONFIG_PATH = f"abfss://config@{STORAGE_ACCOUNT}.dfs.core.windows.net/hk_community_areas.json"

# ── Load HK Community Areas from ADLS Config ──────────────
config_raw = spark.sparkContext.wholeTextFiles(CONFIG_PATH).values().first()
config = json.loads(config_raw)
areas = config["areas"]

# Build postcode lookup: postcode_district -> hk_concentration
hk_high    = [p for a in areas if a["hk_concentration"] == "high"   for p in a["postcodes"]]
hk_medium  = [p for a in areas if a["hk_concentration"] == "medium" for p in a["postcodes"]]

print(f"Loaded {len(areas)} HK community areas from config")
print(f"High concentration postcodes:   {hk_high}")
print(f"Medium concentration postcodes: {hk_medium}")

# ── Read Silver ────────────────────────────────────────────
df = spark.read.parquet(SILVER_PATH)

# ── Add HK concentration flag by postcode district ────────
df = df.withColumn(
    "hk_concentration",
    when(col("postcode_district").isin(hk_high),   lit("high"))
    .when(col("postcode_district").isin(hk_medium), lit("medium"))
    .otherwise(lit("none"))
)

df = df.withColumn(
    "is_hk_community",
    col("hk_concentration").isin("high", "medium")
)

# ── Add period label ───────────────────────────────────────
df = df.withColumn(
    "period",
    when(col("is_baseline"),   lit("P0_baseline"))
    .when(
        col("is_lotr_active") & ~col("is_bno_active"),
        lit("P1_lotr_only")
    )
    .when(
        col("is_lotr_active") & col("is_bno_active"),
        lit("P1P2_overlap")
    )
    .when(
        ~col("is_lotr_active") & col("is_bno_active"),
        lit("P2_bno_only")
    )
    .when(col("is_post_wave"), lit("P3_post_wave"))
    .otherwise(lit("other"))
)

# ── Table 1: price_by_postcode_period ─────────────────────
# Granular analysis at postcode district level
price_by_postcode = df.groupBy(
    "postcode_district", "county", "period", "hk_concentration", "is_hk_community"
).agg(
    median("price").alias("median_price"),
    count("transaction_id").alias("txn_volume"),
    round(avg("price"), 2).alias("avg_price")
)

price_by_postcode.write.mode("overwrite").parquet(
    f"{GOLD_PATH}/price_by_postcode_period"
)
print("Written: price_by_postcode_period")

# ── Table 2: price_monthly_timeseries ─────────────────────
price_monthly = df.withColumn(
    "year_month",
    concat_ws("-",
        col("transfer_date").cast("string").substr(1, 4),
        col("transfer_date").cast("string").substr(6, 2)
    )
).groupBy(
    "postcode_district", "county", "year_month",
    "hk_concentration", "is_hk_community", "period"
).agg(
    median("price").alias("median_price"),
    count("transaction_id").alias("txn_count")
)

price_monthly.write.mode("overwrite").parquet(
    f"{GOLD_PATH}/price_monthly_timeseries"
)
print("Written: price_monthly_timeseries")

# ── Table 3: uplift_summary ───────────────────────────────
baseline = df.filter(col("period") == "P0_baseline").groupBy(
    "postcode_district", "county", "hk_concentration"
).agg(
    median("price").alias("baseline_median_price"),
    count("transaction_id").alias("baseline_txn_volume")
)

bno_period = df.filter(col("period") == "P2_bno_only").groupBy(
    "postcode_district", "county", "hk_concentration"
).agg(
    median("price").alias("bno_median_price"),
    count("transaction_id").alias("bno_txn_volume")
)

uplift = baseline.join(bno_period, ["postcode_district", "county", "hk_concentration"], "inner")\
    .withColumn(
        "price_uplift_pct",
        round(
            (col("bno_median_price") - col("baseline_median_price"))
            / col("baseline_median_price") * 100, 2
        )
    ).withColumn(
        "volume_change_pct",
        round(
            (col("bno_txn_volume") - col("baseline_txn_volume"))
            / col("baseline_txn_volume") * 100, 2
        )
    )

uplift.write.mode("overwrite").parquet(
    f"{GOLD_PATH}/uplift_summary"
)
print("Written: uplift_summary")

# ── Table 4: hk_vs_national_comparison ────────────────────
national_avg = df.groupBy("period").agg(
    median("price").alias("national_median_price")
)

hk_avg = df.filter(col("is_hk_community")).groupBy("period", "hk_concentration").agg(
    median("price").alias("hk_median_price")
)

hk_vs_national = hk_avg.join(national_avg, "period").withColumn(
    "premium_pct",
    round(
        (col("hk_median_price") - col("national_median_price"))
        / col("national_median_price") * 100, 2
    )
)

hk_vs_national.write.mode("overwrite").parquet(
    f"{GOLD_PATH}/hk_vs_national_comparison"
)
print("Written: hk_vs_national_comparison")

print("Gold layer complete!")
spark.stop()
