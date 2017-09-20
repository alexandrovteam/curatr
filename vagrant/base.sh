#!/usr/bin/env bash

HOMEPATH="/home/vagrant"
echo "deb http://www.rabbitmq.com/debian/ testing main" >> /etc/apt/sources.list
curl http://www.rabbitmq.com/rabbitmq-signing-key-public.asc | sudo apt-key add -
apt-get update
apt-get -y install git
echo "export PATH=$HOMEPATH/miniconda/bin:\$PATH" >> $HOMEPATH/.bashrc
export PATH=$HOMEPATH/miniconda/bin:$PATH

wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh
bash Miniconda2-latest-Linux-x86_64.sh -b -p $HOMEPATH/miniconda

chown -R vagrant:vagrant $HOMEPATH
