# curatr
This respository contains the open-source spectral library curation tool: Curatr.

It is written in python using the django web framework and is being developed by the [Alexandrov Team](http://www.embl.de/research/units/scb/alexandrov/) at EMBL Heidelberg.

## Requirements ##
* Ubuntu 14.04
* Python 2.7
* Django 1.9
* git 2.6
* RabbitMQ 3.6

## Installation ##
We recomment installing curatr and its python dependancies inside a virtual environment as follows,
Create a convenient directory, for example `curatr' and clone the repository there:
```
mkdir curatr
cd curatr
git clone https://github.com/alexandrovteam/curatr
```
Initialize and activate a 'curatr' environment with all python dependancies
```
pip install virtualenv
virtualenv venv
source venv/bin/activate
pip install --upgrade pip
pip install pip-tools
cd curatr
pip-sync
```
## Run Server in debug mode ##
### Django Settings ###
Make and edit a local copy of the django settings file
```
cd mcf_standard_browse/mcf_standard_browser/mcf_standard_browser/
cp settings_template.py settings.py
```
Open `settings.py` and edit the following fields
 * SECRET_KEY: replace the secret key with a securely generated key e.g. copy-and-paste from a python terminal
 
      ```
      python
      ```
      from the python terminal:
      ```python
      print ''.join([random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
      ```

### RabbitMQ Settings ###
<todo>

### Run Server ###
```
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```
Curatr should now be visible on  [localhost:8000](http://localhost:8000)

