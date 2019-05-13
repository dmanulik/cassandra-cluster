#!/usr/bin/env python

import json
import logging
import multiprocessing
import os
from cluster import ClusterOperations
from csvmultiprocessing import CSVMultiprocessing

#import cProfile

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
log = logging.getLogger(__name__)

def main():
  with open(os.path.join(__location__, 'cluster_config.json'), 'r') as f:
    cluster_config = json.load(f)

  cassandra = ClusterOperations(cluster_config['connection_config'])

  with open(os.path.join(__location__, 'meta/keyspaces.json'), 'r') as f:
    keyspaces_metadata = json.load(f)

  keyspaces = {}
  for keyspace, replication in keyspaces_metadata.items():
    cassandra.create_keyspace(keyspace, replication)
    keyspaces[keyspace] = None

  for keyspace in keyspaces.keys():
    with open(os.path.join(__location__, 'meta/{}.json'.format(keyspace)), 'r') as f:
      keyspaces[keyspace] = json.load(f)

  for keyspace, table_file in keyspaces.items():
    for tablename, table_metadata in table_file.items():
      cassandra.create_table(keyspace, tablename, table_metadata['columns'], 
                  table_metadata['primary_key'], table_metadata['clustering_order_by'])
  
  for dataset in cluster_config['data']['datasets']:
    log.info("Staring to process {} file...".format(dataset))
    dataset_location = '/'.join([cluster_config['data']['datasets_location'], dataset])
    CSVMultiprocessing(cluster_config['connection_config'], 
                      multiprocessing.cpu_count(), 
                      dataset_location,
                      cluster_config['data']['datasets'][dataset]['delimeter'], 
                      keyspaces, 
                      cluster_config['data']['datasets'][dataset]['keyspace_column'])
  
if __name__ == "__main__":
    main()