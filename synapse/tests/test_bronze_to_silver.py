# test_bronze_to_silver.py
# Unit tests for bronze_to_silver transformation logic.

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, trim, upper, regexp_replace, when, lit
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from datetime import date


# ── Helper: create sample bronze dataframe ─────────────────
def create_sample_bronze_df(spark):
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

    data = [
        # Active records - various periods
        ("{uuid-1}", 250000, "2017-06-01 00:00", "WA14 1AA", "D", "N", "F", "1", "", "HIGH ST", "", "ALTRINCHAM", "TRAFFORD", "GREATER MANCHESTER", "A", "A"),
        ("{uuid-2}", 380000, "2020-09-15 00:00", "SM1 1AA",  "S", "N", "F", "2", "", "MAIN RD",  "", "SUTTON",     "SUTTON",   "GREATER LONDON",     "A", "A"),
        ("{uuid-3}", 420000, "2021-05-20 00:00", "M33 1AA",  "D", "N", "F", "3", "", "OAK AVE",  "", "SALE",       "TRAFFORD", "GREATER MANCHESTER", "A", "A"),
        ("{uuid-4}", 310000, "2022-03-10 00:00", "KT1 1AA",  "T", "N", "F", "4", "", "KING ST",  "", "KINGSTON",   "KINGSTON UPON THAMES", "GREATER LONDON", "A", "A"),
        ("{uuid-5}", 290000, "2023-07-01 00:00", "B90 1AA",  "S", "N", "F", "5", "", "PARK RD",  "", "SOLIHULL",   "SOLIHULL", "WEST MIDLANDS",      "A", "A"),
        # Deleted record - should be filtered out
        ("{uuid-6}", 200000, "2021-01-01 00:00", "NG2 1AA",  "F", "N", "L", "6", "", "WEST ST",  "", "NOTTINGHAM", "RUSHCLIFFE", "NOTTINGHAMSHIRE",  "A", "D"),
        # Zero price - should be filtered out
        ("{uuid-7}", 0,      "2021-01-01 00:00", "RG1 1AA",  "F", "N", "L", "7", "", "READ ST",  "", "READING",    "READING",  "BERKSHIRE",          "A", "A"),
        # Before 2017 - should be filtered out
        ("{uuid-8}", 150000, "2015-01-01 00:00", "WA15 1AA", "D", "N", "F", "8", "", "OLD RD",   "", "ALTRINCHAM", "TRAFFORD", "GREATER MANCHESTER", "A", "A"),
    ]

    return spark.createDataFrame(data, schema)


# ── Test 1: Filter inactive records ───────────────────────
def test_filter_deleted_records(spark):
    df = create_sample_bronze_df(spark)
    df = df.filter(col("record_status") == "A")
    assert df.count() == 7, "Should remove deleted records"


# ── Test 2: Filter zero price ──────────────────────────────
def test_filter_zero_price(spark):
    df = create_sample_bronze_df(spark)
    df = df.filter(col("record_status") == "A")
    df = df.filter(col("price") > 0)
    assert df.count() == 6, "Should remove zero price records"


# ── Test 3: Filter to 2017 onwards ────────────────────────
def test_filter_analysis_period(spark):
    df = create_sample_bronze_df(spark)
    df = df.filter(col("record_status") == "A")
    df = df.filter(col("price") > 0)
    df = df.withColumn("transfer_date", to_date(col("transfer_date"), "yyyy-MM-dd HH:mm"))
    df = df.filter(col("transfer_date") >= "2017-01-01")
    assert df.count() == 5, "Should remove pre-2017 records"


# ── Test 4: Period flags - baseline ───────────────────────
def test_period_flag_baseline(spark):
    df = create_sample_bronze_df(spark)
    df = df.filter(col("record_status") == "A")
    df = df.filter(col("price") > 0)
    df = df.withColumn("transfer_date", to_date(col("transfer_date"), "yyyy-MM-dd HH:mm"))
    df = df.filter(col("transfer_date") >= "2017-01-01")
    df = df.withColumn(
        "is_baseline",
        (col("transfer_date") >= "2017-01-01") & (col("transfer_date") < "2020-07-01")
    )
    baseline_count = df.filter(col("is_baseline")).count()
    assert baseline_count == 1, "Only 2017 record should be baseline"


# ── Test 5: Period flags - LOTR active ────────────────────
def test_period_flag_lotr(spark):
    df = create_sample_bronze_df(spark)
    df = df.filter(col("record_status") == "A")
    df = df.filter(col("price") > 0)
    df = df.withColumn("transfer_date", to_date(col("transfer_date"), "yyyy-MM-dd HH:mm"))


# ── Test 6: Period flags - BNO active ─────────────────────
def test_period_flag_bno(spark):
    df = create_sample_bronze_df(spark)
    df = df.filter(col("record_status") == "A")
    df = df.filter(col("price") > 0)
    df = df.withColumn("transfer_date", to_date(col("transfer_date"), "yyyy-MM-dd HH:mm"))
    df = df.filter(col("transfer_date") >= "2017-01-01")
    df = df.withColumn(
        "is_bno_active",
        (col("transfer_date") >= "2021-01-31") & (col("transfer_date") <= "2022-12-31")
    )
    bno_count = df.filter(col("is_bno_active")).count()
    assert bno_count == 2, "2021-05 and 2022-03 records should be BNO active"


# ── Test 7: Postcode district extraction ──────────────────
def test_postcode_district_extraction(spark):
    df = create_sample_bronze_df(spark)
    df = df.filter(col("record_status") == "A")
    df = df.withColumn("postcode", trim(upper(col("postcode"))))
    df = df.withColumn(
        "postcode_district",
        regexp_replace(col("postcode"), " .*$", "")
    )
    districts = [row.postcode_district for row in df.select("postcode_district").collect()]
    assert "WA14" in districts, "Should extract WA14 from WA14 1AA"
    assert "SM1"  in districts, "Should extract SM1 from SM1 1AA"
    assert "M33"  in districts, "Should extract M33 from M33 1AA"
