#!/usr/bin/env bash

HOMEPATH="/home/vagrant"
echo "deb http://www.rabbitmq.com/debian/ testing main" >> /etc/apt/sources.list
curl http://www.rabbitmq.com/rabbitmq-signing-key-public.asc | sudo apt-key add -
apt-get update
apt-get -y install git
sudo apt-get -y install build-essential
apt-get install -y --force-yes rabbitmq-server
service rabbitmq-server start

wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh
bash Miniconda2-latest-Linux-x86_64.sh -b -p $HOMEPATH/miniconda

ln -s $HOMEPATH/miniconda/bin/conda /usr/local/bin/conda
ln -s $HOMEPATH/miniconda/bin/activate /usr/local/bin/activate
ln -s $HOMEPATH/miniconda/bin/deactivate /usr/local/bin/deactivate

chown -R vagrant:vagrant $HOMEPATH
