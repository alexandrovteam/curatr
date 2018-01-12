#!/usr/bin/env bash
echo $HOME
git clone https://github.com/alexandrovteam/curatr
cd curatr
conda create -y -n venv python=3.6
source activate venv
pip install --upgrade pip
pip install pip-tools
conda install -y -c openbabel openbabel
pip install cython
pip install requests
pip install -r requirements.txt

cp /home/vagrant/curatr/mcf_standard_browser/mcf_standard_browser/settings_template.py /home/vagrant/curatr/mcf_standard_browser/mcf_standard_browser/settings.py
cd ~/curatr/mcf_standard_browser
python manage.py migrate
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'pass')" | python manage.py shell
python manage.py migrate djcelery

screen -dmS celery -L bash -c "source activate venv; python manage.py celeryd"
screen -dmS beat -L bash -c "source activate venv; python manage.py celerybeat"
screen -dmS curatr -L bash -c "source activate venv; python manage.py runserver [::]:8000"
