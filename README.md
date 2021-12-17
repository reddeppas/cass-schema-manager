# cassandra-schema-manager
This is a  Python script that manages cassandra schema. Also Sample helm chart is given in Charts directory. Helm Chart deploys a  Cron Job in Kubernetes . This job parses Config Maps and executes the python script. Helm Chart requires certain format of Config Maps should follow below format

#### Config Map should have following style -


```
    test_schema.json: |-
        {
            "keyspacename": "test",
            "schemaversions": {
                "1": [
                    "CREATE TABLE IF NOT EXISTS test.schema_migration (applied_successful boolean, version int, script_name varchar, script text, executed_at timestamp, PRIMARY KEY (applied_successful, version))"
                    ],
                "2": [
                    "CREATE TABLE IF NOT EXISTS test.schema_migration_leader (keyspace_name text, leader uuid, took_lead_at timestamp, leader_hostname text, PRIMARY KEY (keyspace_name))"
                    ]
            }
        }
```

First time when the job executes it  creates a table keyspace_versions in schemamanager keyspace. and It parses the configmaps and executes the CQL queries . For further updates the versions in keyspace_versions table updated byt ehs script. If there is a new version is avilable in the configmap cronjob will run the script and upgrades schema version for the given keyspace in configmap.


The script requires below environment variables to be set:


CONTACT_POINTS

A list of node hostnames or IP addresses with which to create initial connections. In Kubernetes the headless service for the Cassandra statefulset can be used instead.

REPLICATION The replication settings, e.g.,

{'class': 'NetworkTopologyStrategy', 'dc1': 1}

