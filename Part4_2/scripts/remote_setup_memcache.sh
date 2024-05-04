#!/bin/bash

sudo NEEDRESTART_MODE=a apt-get update
sudo NEEDRESTART_MODE=a apt-get install -y memcached libmemcached-tools

# Necessary to expose the service now. The ip is given as argument to the script
memcache_configuration="
-d
logfile /var/log/memcached.log
-m 1024
-p 11211
-u memcache
-l $1
-P /var/run/memcached/memcached.pid
-t 1
"
echo "$memcache_configuration" | sudo tee /etc/memcached.conf  
sudo systemctl restart memcached

MEMCACHED_PID=$(cat /var/run/memcached/memcached.pid | tr -d '\r')
sudo taskset -a -cp 0 $MEMCACHED_PID