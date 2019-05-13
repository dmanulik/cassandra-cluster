#!/bin/bash

set -x
docker stack rm cassandra
set +x

current_user=$(whoami)
cassandra_home="/home/${current_user}/cassandra_docker"

if [[ $1 != "-s" ]]; then
  sudo rm -rf $cassandra_home
fi

docker rm -f $(docker ps -a --filter="name=cassandra*" --format "{{.ID}}")