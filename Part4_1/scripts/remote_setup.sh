#!/bin/bash

sudo sh -c "echo deb-src http://europe-west3.gce.archive.ubuntu.com/ubuntu/ jammy main restricted >> /etc/apt/sources.list"
sudo sudo NEEDRESTART_MODE=a apt-get update
sudo sudo NEEDRESTART_MODE=a apt-get install libevent-dev libzmq3-dev git make g++ --yes
sudo sudo NEEDRESTART_MODE=a apt-get build-dep memcached --yes
git clone https://github.com/eth-easl/memcache-perf-dynamic.git
cd memcache-perf-dynamic
make