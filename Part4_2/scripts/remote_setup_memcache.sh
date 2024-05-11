#!/bin/bash

sudo NEEDRESTART_MODE=a apt-get update
sudo NEEDRESTART_MODE=a apt-get install -y memcached libmemcached-tools

# Install python dependencies
sudo NEEDRESTART_MODE=a apt-get install -y python3-pip
sudo pip3 install psutil
sudo pip3 install docker

# Install docker
sudo NEEDRESTART_MODE=a apt-get install ca-certificates curl -y
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo NEEDRESTART_MODE=a apt-get update -y
sudo NEEDRESTART_MODE=a apt-get install docker-ce docker-ce-cli docker-buildx-plugin docker-compose-plugin -y
sudo usermod -a -G docker ubuntu

# Necessary to expose the service now. The ip is given as argument to the script
# Run with 2 threads
memcache_configuration="
-d
logfile /var/log/memcached.log
-m 1024
-p 11211
-u memcache
-l $1
-P /var/run/memcached/memcached.pid
-t 2
"
echo "$memcache_configuration" | sudo tee /etc/memcached.conf  
sudo systemctl restart memcached

# Pull all required docker images
docker pull anakli/cca:parsec_blackscholes
docker pull anakli/cca:parsec_canneal
docker pull anakli/cca:parsec_dedup
docker pull anakli/cca:parsec_ferret
docker pull anakli/cca:parsec_freqmine
docker pull anakli/cca:splash2x_radix
docker pull anakli/cca:parsec_vips