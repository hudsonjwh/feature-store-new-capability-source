# Databricks notebook source
# MAGIC %md
# MAGIC # Validate & Update Repo

# COMMAND ----------

# DBTITLE 1,Common Configuration
# MAGIC %run ./Test-Config

# COMMAND ----------

# DBTITLE 1,Configure the Client
from dbacademy.dbtest import *
from dbacademy.dbrest import DBAcademyRestClient

client = DBAcademyRestClient()

source_home = dbgems.get_notebook_dir(offset=-2)
print(f"Source Home:  {source_home}")

student_home = source_home.replace("-source", "-STUDENT-COPY")
print(f"Student Home: {student_home}")

# COMMAND ----------

# DBTITLE 1,Define Utility Method
def update_and_validate(path):
  repo_id = response = client.workspace().get_status(path)["object_id"]

  repo = client.repos().get(repo_id)
  branch = repo["branch"]

  print("** Before **")
  print(f"""branch:         {repo["branch"]}""")
  print(f"""head_commit_id: {repo["head_commit_id"]}""")

  assert branch == "published", f"""Expected the branch to be "published", found "{branch}" """

  repo = client.repos().update(repo_id, "published")
  branch = repo["branch"]

  print("\n** After **")
  print(f"""branch:         {repo["branch"]}""")
  print(f"""head_commit_id: {repo["head_commit_id"]}""")
  
  assert branch == "published", f"""Expected the branch to be "published", found "{branch}" """

# COMMAND ----------

# DBTITLE 1,Validate the Source Branch
update_and_validate(source_home)

# COMMAND ----------

# DBTITLE 1,Validate the Published Branch
update_and_validate(student_home)
