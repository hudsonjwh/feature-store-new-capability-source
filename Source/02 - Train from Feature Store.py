# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC 
# MAGIC <div style="text-align: center; line-height: 0; padding-top: 9px;">
# MAGIC   <img src="https://databricks.com/wp-content/uploads/2018/03/db-academy-rgb-1200px.png" alt="Databricks Learning" style="width: 600px">
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC # Reading from Feature Store
# MAGIC 
# MAGIC Now that we've created some features, we'd like to pick those up using the Python API Client. In this notebook, we'll go over reading from a table in the feature store. After we create a batch prediction, we'll write to feature store for online inference.
# MAGIC 
# MAGIC We can think of these as two of the main downstream tasks where our feature table will be used: model training and model inference.

# COMMAND ----------

from databricks import feature_store
import pyspark.sql.functions as F

# COMMAND ----------

fs = feature_store.FeatureStoreClient()

# COMMAND ----------

dropoff_df = fs.read_table(
  name="feature_store_taxi_example.trip_dropoff_features"
)
pickup_df = fs.read_table(
  name="feature_store_taxi_example.trip_pickup_features"
)

# COMMAND ----------

# MAGIC %md
# MAGIC Alternatively, we can use the FeatureLookup class

# COMMAND ----------

import math
from datetime import timedelta
from pyspark.sql.types import IntegerType
 
def rounded_unix_timestamp(dt, num_minutes=15):
    """
    Ceilings datetime dt to interval num_minutes, then returns the unix timestamp.
    """
    nsecs = dt.minute * 60 + dt.second + dt.microsecond * 1e-6
    delta = math.ceil(nsecs / (60 * num_minutes)) * (60 * num_minutes) - nsecs
    return int((dt + timedelta(seconds=delta)).timestamp())
 
 
rounded_unix_timestamp_udf = udf(rounded_unix_timestamp, IntegerType())
 
def rounded_taxi_data(taxi_data_df):
    # Round the taxi data timestamp to 15 and 30 minute intervals so we can join with the pickup and dropoff features
    # respectively.
    taxi_data_df = (
        taxi_data_df.withColumn(
            "rounded_pickup_datetime",
            rounded_unix_timestamp_udf(taxi_data_df["tpep_pickup_datetime"], F.lit(15)),
        )
        .withColumn(
            "rounded_dropoff_datetime",
            rounded_unix_timestamp_udf(taxi_data_df["tpep_dropoff_datetime"], F.lit(30)),
        )
        .drop("tpep_pickup_datetime")
        .drop("tpep_dropoff_datetime")
    )
    taxi_data_df.createOrReplaceTempView("taxi_data")
    return taxi_data_df
  
raw_data = spark.read.format("delta").load("/databricks-datasets/nyctaxi-with-zipcodes/subsampled")
taxi_data = rounded_taxi_data(raw_data)

# COMMAND ----------

from databricks.feature_store import FeatureLookup
import mlflow
 
pickup_features_table = "feature_store_taxi_example.trip_pickup_features"
dropoff_features_table = "feature_store_taxi_example.trip_dropoff_features"
 
pickup_feature_lookups = [
   FeatureLookup( 
     table_name = pickup_features_table,
     feature_names = ["mean_fare_window_1h_pickup_zip", "count_trips_window_1h_pickup_zip"],
     lookup_key = ["pickup_zip", "rounded_pickup_datetime"],
   ),
]
 
dropoff_feature_lookups = [
   FeatureLookup( 
     table_name = dropoff_features_table,
     feature_names = ["count_trips_window_30m_dropoff_zip", "dropoff_is_weekend"],
     lookup_key = ["dropoff_zip", "rounded_dropoff_datetime"],
   ),
]

# COMMAND ----------

# Since the rounded timestamp columns would likely cause the model to overfit the data 
# unless additional feature engineering was performed, exclude them to avoid training on them.
exclude_columns = ["rounded_pickup_datetime", "rounded_dropoff_datetime"]
 
# Create the training set that includes the raw input data merged with corresponding features from both feature tables
training_set = fs.create_training_set(
  taxi_data,
  feature_lookups = pickup_feature_lookups + dropoff_feature_lookups,
  label = "fare_amount",
  exclude_columns = exclude_columns
)
 
# Load the TrainingSet into a dataframe which can be passed into sklearn for training a model
training_df = training_set.load_df()

# COMMAND ----------

from sklearn.model_selection import train_test_split

features_and_label = training_df.columns
 
# Collect data into a Pandas array for training
data = training_df.toPandas()[features_and_label]
data.fillna(data.mean(), inplace=True)
train, test = train_test_split(data, random_state=123)
X_train = train.drop(["fare_amount"], axis=1)
X_test = test.drop(["fare_amount"], axis=1)
y_train = train.fare_amount
y_test = test.fare_amount

# COMMAND ----------

from sklearn.neighbors import KNeighborsRegressor
knn = KNeighborsRegressor(n_neighbors=5)

# COMMAND ----------

knn.fit(X_train, y_train)

# COMMAND ----------

knn.score(X_test, y_test)

# COMMAND ----------

# MAGIC %md
# MAGIC Now let's add our table to feature store for online inference.

# COMMAND ----------

feature_cols = ['trip_distance', 'pickup_zip', 'dropoff_zip', 'mean_fare_window_1h_pickup_zip', 
        'count_trips_window_1h_pickup_zip', 'count_trips_window_30m_dropoff_zip', 'dropoff_is_weekend']

# Create predictions array
predictions = knn.predict(data[feature_cols])

# Attach array to Pandas Dataframe
data['fare_predictions'] = predictions

# Back to Spark Dataframe
new_taxi_data_preds=spark.createDataFrame(data) 
display(new_taxi_data_preds)

# COMMAND ----------

fs.write_table(
  name="taxi_predictions", 
  df=new_taxi_data_preds
)
