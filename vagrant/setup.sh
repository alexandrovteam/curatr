#!/usr/bin/env bash
echo $HOME
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
cd curatr/mcf_standard_browser
python manage.py migrate
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'pass')" | python manage.py shell
python manage.py migrate djcelery
service rabbitmq-server start

screen -dmS celery -L bash -c "source activate venv; python manage.py celeryd"
screen -dmS curatr -L bash -c "source activate venv; python manage.py runserver [::]:8000"
