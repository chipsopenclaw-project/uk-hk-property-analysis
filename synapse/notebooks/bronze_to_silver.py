# bronze_to_silver.py
# Reads raw Land Registry CSV from Bronze layer,
# cleans data, adds period flags, and writes Parquet to Silver layer.

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, to_date, lit, when, trim, upper,
    regexp_replace, substring
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType
)

# ── Spark Session ──────────────────────────────────────────
spark = SparkSession.builder.appName("bronze_to_silver").getOrCreate()

# ── Config ─────────────────────────────────────────────────
STORAGE_ACCOUNT = "stukhkpropdev"
BRONZE_PATH = f"abfss://bronze@{STORAGE_ACCOUNT}.dfs.core.windows.net/land-registry"
SILVER_PATH = f"abfss://silver@{STORAGE_ACCOUNT}.dfs.core.windows.net/land-registry"

# ── Schema (Land Registry CSV has no header) ───────────────
schema = StructType([
    StructField("transaction_id",  StringType(), True),
    StructField("price",           IntegerType(), True),
    StructField("transfer_date",   StringType(), True),
    StructField("postcode",        StringType(), True),
    StructField("property_type",   StringType(), True),
    StructField("old_new",         StringType(), True),
    StructField("duration",        StringType(), True),
    StructField("paon",            StringType(), True),
    StructField("saon",            StringType(), True),
    StructField("street",          StringType(), True),
    StructField("locality",        StringType(), True),
    StructField("town_city",       StringType(), True),
    StructField("district",        StringType(), True),
    StructField("county",          StringType(), True),
    StructField("ppd_type",        StringType(), True),
    StructField("record_status",   StringType(), True),
])

# ── Read Bronze ────────────────────────────────────────────
df = spark.read.csv(
    f"{BRONZE_PATH}/historical/",
    schema=schema,
    header=False,
    quote='"',
    escape='"'
)

# ── Basic Cleaning ─────────────────────────────────────────
df = df.filter(col("record_status") == "A")         # Keep active records only
df = df.filter(col("price") > 0)                    # Remove zero/negative prices
df = df.filter(col("postcode").isNotNull())          # Remove missing postcodes
df = df.withColumn("postcode", trim(upper(col("postcode"))))
df = df.withColumn("transfer_date", to_date(col("transfer_date"), "yyyy-MM-dd HH:mm"))
df = df.filter(col("transfer_date").isNotNull())

# ── Postcode District (first part of postcode e.g. SW1A) ──
df = df.withColumn(
    "postcode_district",
    regexp_replace(col("postcode"), " .*$", "")
)

# ── Period Flags (Method C - dual flags) ──────────────────
df = df.withColumn(
    "is_baseline",
    (col("transfer_date") >= "2017-01-01") &
    (col("transfer_date") < "2020-07-01")
)

df = df.withColumn(
    "is_lotr_active",
    (col("transfer_date") >= "2020-07-01") &
    (col("transfer_date") <= "2021-07-19")
)

df = df.withColumn(
    "is_bno_active",
    (col("transfer_date") >= "2021-01-31") &
    (col("transfer_date") <= "2022-12-31")
)

df = df.withColumn(
    "is_post_wave",
    col("transfer_date") >= "2023-01-01"
)

# ── Filter to analysis period (2017 onwards) ──────────────
df = df.filter(col("transfer_date") >= "2017-01-01")

# ── Outlier Removal (cap at 99.5th percentile per county) ─
price_cap = df.approxQuantile("price", [0.995], 0.01)[0]
df = df.filter(col("price") <= price_cap)

# ── Select Final Columns ───────────────────────────────────
df = df.select(
    "transaction_id",
    "price",
    "transfer_date",
    "postcode",
    "postcode_district",
    "property_type",
    "old_new",
    "duration",
    "street",
    "town_city",
    "district",
    "county",
    "ppd_type",
    "is_baseline",
    "is_lotr_active",
    "is_bno_active",
    "is_post_wave"
)

# ── Write Silver (Parquet, partitioned by year) ────────────
df.withColumn(
    "year", col("transfer_date").cast("string").substr(1, 4)
).write.partitionBy("year").mode("overwrite").parquet(SILVER_PATH)

print(f"Silver layer written: {df.count()} records")
spark.stop()
