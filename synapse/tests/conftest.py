# conftest.py
# Shared pytest fixtures for Synapse PySpark unit tests.

import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark():
    """Create a local SparkSession for testing."""
    spark = SparkSession.builder \
        .master("local[*]") \
        .appName("unit_tests") \
        .config("spark.sql.shuffle.partitions", "2") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    yield spark
    spark.stop()
