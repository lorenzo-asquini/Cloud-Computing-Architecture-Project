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
sudo taskset -a -cp 0,1 $MEMCACHED_PID  # Start with 2 cores

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

# Install python
sudo NEEDRESTART_MODE=a apt-get install python3.10 -y

# Install poetry
sudo curl -sSL https://install.python-poetry.org | python3 - --version 1.8.2
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Reload bashrc
source ~/.bashrc