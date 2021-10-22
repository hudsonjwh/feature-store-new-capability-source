# Databricks notebook source
# MAGIC %pip install git+https://github.com/databricks-academy/dbacademy

# COMMAND ----------

import os
from dbacademy import dbgems
from dbacademy.dbtest import TestConfig

# Multiple references throug test code
course_name = "Example Course"

# Use the "runner's" runtime as the default for the tests
java_tags = dbutils.entry_point.getDbutils().notebook().getContext().tags()
spark_version = sc._jvm.scala.collection.JavaConversions.mapAsJavaMap(java_tags)["sparkVersion"]
assert spark_version, "DBR not yet defined, please try again."
  
cluster_pool = os.environ.get('SMOKE_TEST_CLUSTER_POOL')
assert cluster_pool, "The cluster pool was not specified."

test_config = TestConfig(
  course_name,                  # The name of the course
  spark_version,                # Current version
  workers = 0,                  # Test in local mode
  libraries = [],               # Libraries to attache to the cluster
  cloud = dbgems.get_cloud(),   # The cloud this test is running in
  instance_pool = cluster_pool, # AWS, GCP or MSA instance pool
)

print("Test Configuration")
test_config.print()
