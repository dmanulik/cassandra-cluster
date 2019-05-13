#!/bin/bash

current_user=$(whoami)
export CASSANDRA_HOME="/home/${current_user}/cassandra_docker"
datasets_dir="/opt/datasets"
config_dir='../config'

for dir in $CASSANDRA_HOME $datasets_dir
do
  if [ ! -d $dir ]; then
    sudo mkdir $dir
    sudo chown -R ${current_user}.${current_user} $dir
  fi
done

for i in {1..6}
do
  mkdir -p ${CASSANDRA_HOME}/c0${i}/{etc,varlib}
  cp ${config_dir}/c0${i}_cassandra.yaml ${CASSANDRA_HOME}/c0${i}/etc/
  cp ${config_dir}/c0${i}_cassandra-rackdc.properties ${CASSANDRA_HOME}/c0${i}/etc/
  cp ${config_dir}/c0${i}_jvm.options ${CASSANDRA_HOME}/c0${i}/etc/
  cp ${config_dir}/c0${i}_cassandra-env.sh ${CASSANDRA_HOME}/c0${i}/etc/
done

set -x

docker stack deploy --compose-file ../docker-compose.yaml cassandra
