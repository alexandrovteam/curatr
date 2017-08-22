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
source $HOMEPATH/.bashrc

git clone https://github.com/alexandrovteam/curatr
cd curatr
conda create -y -n venv python=2.7
source activate venv
pip install --upgrade pip
pip install pip-tools
conda install -y -c clyde_fare openbabel=2.3.2
pip-sync

apt-get install -y --force-yes rabbitmq-server

cp /home/vagrant/curatr/mcf_standard_browser/mcf_standard_browser/settings_template.py /home/vagrant/curatr/mcf_standard_browser/mcf_standard_browser/settings.py

chown -R vagrant:vagrant $HOMEPATH
sudo -i -u vagrant

cd /$HOMEPATH/curatr/mcf_standard_browser
python manage.py migrate
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'pass')" | python manage.py shell
python manage.py migrate djcelery
service rabbitmq-server start

screen -dmS celery -L bash -c "source activate venv; python manage.py celeryd"
screen -dmS curatr -L bash -c "source activate venv; python manage.py runserver [::]:8000"
