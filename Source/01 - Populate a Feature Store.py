# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC 
# MAGIC <div style="text-align: center; line-height: 0; padding-top: 9px;">
# MAGIC   <img src="https://databricks.com/wp-content/uploads/2018/03/db-academy-rgb-1200px.png" alt="Databricks Learning" style="width: 600px">
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC # Create Feaures in Feature Store
# MAGIC 
# MAGIC In this notebook, we're going to populate a feaure store using the Python Client API.
# MAGIC 
# MAGIC We're going to be doing this with a dataset from the NYC Taxi Service. Let's start by reading in the raw dataset from the default Databricks dataset.

# COMMAND ----------

from databricks import feature_store
import pyspark.sql.functions as F 
from pyspark.sql.types import FloatType, IntegerType, StringType
from pytz import timezone
 
# Grabbing username and doing a little clean up of the string
username = spark.sql("SELECT current_user()").collect()[0][0]
if '@' in  username:
  username = username.split('@')[0]
if '.' in username:
  username = username.replace(".", "")

# COMMAND ----------

raw_data = spark.read.format("delta").load("/databricks-datasets/nyctaxi-with-zipcodes/subsampled")
display(raw_data)

# COMMAND ----------

# MAGIC %md
# MAGIC Next, we want to create some helper functions to transform our data. 

# COMMAND ----------

@udf(returnType=IntegerType())
def is_weekend(dt):
    tz = "America/New_York"
    return int(dt.astimezone(timezone(tz)).weekday() >= 5)  # 5 = Saturday, 6 = Sunday
  
@udf(returnType=StringType())  
def partition_id(dt):
    # datetime -> "YYYY-MM"
    return f"{dt.year:04d}-{dt.month:02d}"
 
 
def filter_df_by_ts(df, ts_column, start_date, end_date):
    if ts_column and start_date:
        df = df.filter(F.col(ts_column) >= start_date)
    if ts_column and end_date:
        df = df.filter(F.col(ts_column) < end_date)
    return df

# COMMAND ----------

# MAGIC %md
# MAGIC Now let's create some wrapper functions for both the pickup and dropoff features.

# COMMAND ----------

def pickup_features_fn(df, ts_column, start_date, end_date):
    """
    Computes the pickup_features feature group.
    To restrict features to a time range, pass in ts_column, start_date, and/or end_date as kwargs.
    """
    df = filter_df_by_ts(
        df, ts_column, start_date, end_date
    )
    pickupzip_features = (
        df.groupBy(
            "pickup_zip", F.window("tpep_pickup_datetime", "1 hour", "15 minutes")
        )  # 1 hour window, sliding every 15 minutes
        .agg(
            F.mean("fare_amount").alias("mean_fare_window_1h_pickup_zip"),
            F.count("*").alias("count_trips_window_1h_pickup_zip"),
        )
        .select(
            F.col("pickup_zip").alias("zip"),
            F.unix_timestamp(F.col("window.end")).alias("ts").cast(IntegerType()),
            partition_id(F.to_timestamp(F.col("window.end"))).alias("yyyy_mm"),
            F.col("mean_fare_window_1h_pickup_zip").cast(FloatType()),
            F.col("count_trips_window_1h_pickup_zip").cast(IntegerType()),
        )
    )
    return pickupzip_features
  
def dropoff_features_fn(df, ts_column, start_date, end_date):
    """
    Computes the dropoff_features feature group.
    To restrict features to a time range, pass in ts_column, start_date, and/or end_date as kwargs.
    """
    df = filter_df_by_ts(
        df,  ts_column, start_date, end_date
    )
    dropoffzip_features = (
        df.groupBy("dropoff_zip", F.window("tpep_dropoff_datetime", "30 minute"))
        .agg(F.count("*").alias("count_trips_window_30m_dropoff_zip"))
        .select(
            F.col("dropoff_zip").alias("zip"),
            F.unix_timestamp(F.col("window.end")).alias("ts").cast(IntegerType()),
            partition_id(F.to_timestamp(F.col("window.end"))).alias("yyyy_mm"),
            F.col("count_trips_window_30m_dropoff_zip").cast(IntegerType()),
            is_weekend(F.col("window.end")).alias("dropoff_is_weekend"),
        )
    )
    return dropoffzip_features  

# COMMAND ----------

# MAGIC %md
# MAGIC Creating a pick up dataframe and a drop off feature dataframe.

# COMMAND ----------

from datetime import datetime
 
pickup_features = pickup_features_fn(
    raw_data, ts_column="tpep_pickup_datetime", start_date=datetime(2016, 1, 1), end_date=datetime(2016, 1, 31)
)
dropoff_features = dropoff_features_fn(
    raw_data, ts_column="tpep_dropoff_datetime", start_date=datetime(2016, 1, 1), end_date=datetime(2016, 1, 31)
)

# COMMAND ----------

# MAGIC %md
# MAGIC Make sure that we've got our Hive Metastore set up.

# COMMAND ----------

# MAGIC %sql 
# MAGIC CREATE DATABASE IF NOT EXISTS feature_store_taxi_example;

# COMMAND ----------

# MAGIC %md
# MAGIC Now let's import the Feature Store Client and write to a table!

# COMMAND ----------

fs = feature_store.FeatureStoreClient()

# COMMAND ----------

spark.conf.set("spark.sql.shuffle.partitions", "5")
 
fs.create_feature_table(
    name=f"feature_store_taxi_example.{username}_trip_pickup_features",
    keys=["zip", "ts"],
    features_df=pickup_features,
    partition_columns="yyyy_mm",
    description="Taxi Fares. Pickup Features",
)
fs.create_feature_table(
    name=f"feature_store_taxi_example.{username}_trip_dropoff_features",
    keys=["zip", "ts"],
    features_df=dropoff_features,
    partition_columns="yyyy_mm",
    description="Taxi Fares. Dropoff Features",
)

# COMMAND ----------

# Compute the pickup_features feature group.
pickup_features_df = pickup_features_fn(
  df=raw_data,
  ts_column="tpep_pickup_datetime",
  start_date=datetime(2016, 2, 1),
  end_date=datetime(2016, 2, 29),
)
 
# Write the pickup features DataFrame to the feature store table
fs.write_table(
  name=f"feature_store_taxi_example.{username}_trip_pickup_features",
  df=pickup_features_df,
  mode="merge",
)
 
# Compute the dropoff_features feature group.
dropoff_features_df = dropoff_features_fn(
  df=raw_data,
  ts_column="tpep_dropoff_datetime",
  start_date=datetime(2016, 2, 1),
  end_date=datetime(2016, 2, 29),
)
 
# Write the dropoff features DataFrame to the feature store table
fs.write_table(
  name=f"feature_store_taxi_example.{username}_trip_dropoff_features",
  df=dropoff_features_df,
  mode="merge",
)

# COMMAND ----------


