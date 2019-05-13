#!/usr/bin/env python

import csv
import logging
import traceback

from jinja2 import Environment, FileSystemLoader, Template

from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.policies import WhiteListRoundRobinPolicy
from contextlib import ExitStack

log = logging.getLogger(__name__)


class ClusterOperations:
  def __init__(self, config):
    """Args:
         [Dict] config: Cassandra connection configuration details
    """
    self.config = config
    for config_attribute, value in config.items():
      setattr(self, config_attribute, value)

    # WhiteListRoundRobinPolicy is used 
    # because only one docker service has port exposed 
    self.cluster = Cluster(self.contact_points,
                   load_balancing_policy=WhiteListRoundRobinPolicy(self.contact_points),
                   max_schema_agreement_wait=self.max_schema_agreement_wait,
                   port=self.port)
        
    self.session = self.cluster.connect()
    default_cl = getattr(ConsistencyLevel, self.default_consistency_level)
    self.session.default_consistency_level = default_cl

  def create_keyspace(self, keyspace_name, replication):    
    ddl_template = """CREATE KEYSPACE {{ keyspace_name }}
    WITH REPLICATION = {{ '{' }}
    {% if replication is mapping -%}
      'class': 'NetworkTopologyStrategy',
      {% for datacenter, replication_factor in replication.items() -%} 
        '{{- datacenter }}': {{ replication_factor }} {{ "," if not loop.last }}
      {%- endfor -%} 
    {% else -%}
      'class': 'SimpleStrategy',
      'replication_factor': {{ replication }}
    {%- endif %} 
    {{ '}' -}}
    """

    ddl = self.render_template(ddl_template, 
      dict(keyspace_name = keyspace_name, 
      replication = replication)
    )
    
    log.debug(ddl)

    try:
      if keyspace_name not in self.cluster.metadata.keyspaces.keys():
        log.info("Creating '{}' keyspace in '{}' cluster".format(keyspace_name, 
                                                          self.cluster.metadata.cluster_name))
        self.session.execute(ddl, timeout=self.timeout)
      else:
        log.info("Keyspace '{}' is already in '{}' cluster, skipping creation".format(keyspace_name, 
                                                                self.cluster.metadata.cluster_name))
    except Exception as e:
      log.exception(traceback.format_exc())

  def create_table(self, keyspace_name, table_name, table_columns, 
  primary_key, clustering_order_by=False):
    ddl_template = """CREATE TABLE {{ keyspace_name }}.{{ table_name }} (
    {% for column_name, data_type in table_columns.items() -%}
    {{ column_name }} {{ data_type }},
    {% endfor -%}
    PRIMARY KEY({{ primary_key }}))
    {% if clustering_order_by -%}
    WITH CLUSTERING ORDER BY ({{ clustering_order_by }})
    {% endif -%};"""
    # To Do:  try inline {{ value if value else 'No value' }}    
    ddl = self.render_template(ddl_template, 
      dict(keyspace_name = keyspace_name,
        table_name = table_name,
        table_columns = table_columns,
        primary_key = primary_key,
        clustering_order_by = clustering_order_by)
    )
    
    log.debug(ddl)

    try:
      self.cluster.refresh_schema_metadata()
      if table_name not in self.cluster.metadata.keyspaces[keyspace_name].tables.keys():
        log.info("Creating '{}' table in '{}' keyspace".format(table_name, keyspace_name))
        self.session.execute(ddl, timeout=self.timeout)
      else:
        log.info("Table '{}' is already in '{}' keyspace, skipping creation".format(table_name, 
                                                                                keyspace_name))
    except Exception as e:
      log.exception(traceback.format_exc())

  def render_template(self, string_template, variables):
    string_template = Template(string_template)
    env = Environment(trim_blocks=True, lstrip_blocks=True)
    template = env.get_template(string_template)
    
    return template.render(variables)
