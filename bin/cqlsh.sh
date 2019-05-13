#!/bin/bash

if [ -z $1 ]; then
  node_num=1
else
  node_num=$1
fi

set -x

docker run -it --name cassandra-cqlsh --network cassandra_onet --rm cassandra:3.11.4 cqlsh c0${node_num}