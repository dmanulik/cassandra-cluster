#!/bin/bash

if [ -z $1 ]; then
  node_num=1
else
  node_num=$1
fi

service_ext=$(docker service ps -f "name=cassandra_c0${node_num}.1" cassandra_c0${node_num} -q --no-trunc | head -n1)

set -x
docker exec -ti cassandra_c0${node_num}.1.${service_ext} /bin/bash
