import sys
import os
import json
import logging
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

logger = logging.getLogger('init_keyspace')
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

def getenv(name, fallback=None):
  value = os.getenv(name, default=fallback)
  if not value:
    raise Exception("The environment variable {0} is undefined".format(name))
  return str(value)

def create_table(keyspace, table_name, table_def):
  logger.info("Creating {}.{} table".format(keyspace, table_name))
  session.execute("CREATE TABLE IF NOT EXISTS {}.{}{}".format(keyspace, table_name, table_def))

def execute_query(keyspace, query):
  logger.info("Executing Query {}.{} table".format(keyspace, query))
  session.execute("{}".format(query))

def get_schema_version(keyspace):
  version = None
  rows = session.execute("select version from schemamanager.keyspace_versions where keyspace_name='{}'".format(keyspace))
  for row in rows:
    version = row.version
  return version

def insert_query(keyspace):
  logger.info("Initilizing keyspace {}".format(keyspace))
  session.execute("INSERT INTO schemamanager.keyspace_versions (keyspace_name, modified_date, version) VALUES ('{0}', unixTimestampOf(now()), 0)".format(keyspace))

def update_query(keyspace,version):
  logger.info("Updating keyspace {} to Schema Version:{}".format(keyspace, version))
  session.execute("UPDATE schemamanager.keyspace_versions set version={0} WHERE keyspace_name='{1}'".format(int(version), keyspace))

def create_keyspace(keyspace,replication):
  logger.info("Creating {}.{} Keyspace".format(keyspace, replication))
  session.execute("CREATE KEYSPACE IF NOT EXISTS {0} WITH REPLICATION = {1}".format(keyspace, replication))

def parse_schema_jsons():
  path_to_json = '/app/'
  json_files = [pos_json for pos_json in os.listdir(path_to_json) if pos_json.endswith('.json')]

  for index, js in enumerate(json_files):
      with open(os.path.join(path_to_json, js)) as json_file:
          json_text = json.load(json_file)

          for version ,queries in json_text['schemaversions'].items():
              keyspace = json_text['keyspacename']

              # Create KeySpace with replication
              create_keyspace(keyspace,replication)
              
              #get Schema Version from schemamanager keyspace versions table
              if get_schema_version(keyspace) == None:
                 insert_query(keyspace)
              
              current_version = get_schema_version(keyspace)
              if int(version) > int(current_version):
                #execute queries
                logger.info("Proceeding with Update Schema Version:{0} for Keyspace:{1} ".format(version,keyspace))
                for query in queries:
                  logger.info("Running Query:" + query)
                  execute_query(keyspace,query)
                  update_query(keyspace,version)
                logger.info("Schema Version:{0} for Keyspace:{1} Status: Updated".format(version,keyspace))
              else:
                logger.info("Schema Version:{0} for Keyspace:{1} Status: Skipped".format(version,keyspace))



logger.info("Running {}".format(sys.argv[0]))

contact_points = getenv("CONTACT_POINTS").split(",")
replication = getenv("REPLICATION")

logger.info("contact_points = %s", contact_points)
logger.info("replication = %s", replication)

username = getenv("USERNAME", fallback="cassandra")
password = getenv("PASSWORD", fallback="cassandra")

auth_provider = PlainTextAuthProvider(username=username, password=password)
cluster = Cluster(contact_points, auth_provider=auth_provider)
session = cluster.connect()

#create schemamanager keyspace and tables
create_keyspace("schemamanager",replication)

create_table("schemamanager","keyspace_versions","(keyspace_name text, version int, modified_date timestamp, PRIMARY KEY (keyspace_name))")

parse_schema_jsons()

