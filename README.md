# curatr
This respository contains the open-source spectral library curation tool: Curatr.

It is written in python using the django web framework and is being developed by the [Alexandrov Team](http://www.embl.de/research/units/scb/alexandrov/) at EMBL Heidelberg.

## Requirements ##
* Ubuntu 14.04
* Python 2.7
* Django 1.9
* git 2.6
* RabbitMQ 3.6
* OpenBabel ```conda install -c clyde_fare openbabel=2.3.2'''

## Installation ##
We recommend installing curatr and its python dependencies inside a virtual environment as follows:

1. Create a convenient directory, for example `curatr` and clone the repository there:
    ```
    mkdir curatr
    cd curatr
    git clone https://github.com/alexandrovteam/curatr
    ```
2. Initialize and activate a 'curatr' environment with all python dependencies
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
 * CELERYD_CONCURRENCY: set this number to the desired amount of workers (degree of parallelism) or remove the line to use all CPUs  

### Initialize the DB ###
```
python manage.py migrate
```

### Create an admin user ##
```
python manage.py createsuperuser
'''

### Set up a message broker (example: RabbitMQ) ##
1. [Install RabbitMQ] (https://www.rabbitmq.com/download.html)
2. (Optional) Configure a user
    ```
    # RabbitMQ installs with a default username / password of guest / guest
    # you can change that by creating a new user
    rabbitmqctl add_user myuser mypassword
    rabbitmqctl add_vhost myvhost
    rabbitmqctl set_permissions -p myvhost myuser ".*" ".*" ".*"
    ```
    
    And adjust the URL in settings.py: `BROKER_URL = "amqp://myuser:mypassword@localhost:5672/myvhost"`.
    Find more details [here] (http://www.rabbitmq.com/man/rabbitmqctl.1.man.html)
3. Sync your DB: `python manage.py migrate djcelery`

### Run Server ###
1. Start RabbitMQ: `sudo service rabbitmq-server start` (on Ubuntu)
2. Start Celery: `python manage.py celeryd`. Useful parameters:
    - `--verbosity=2`
    - `--loglevel=DEBUG`
3. Start the server: `python manage.py runserver`

Curatr should now be visible on  [localhost:8000](http://localhost:8000)

### Getting Going ###
We have provided an example molecular library and data in the [media](https://github.com/alexandrovteam/curatr/mcf_standard_browser/media) directory 
1. Add standards to library
    * Single
        1. Add molecule
            #todo
        2. Add standard
            #todo
    * Batch
        1. From the "Curate" menu select "Add Standard"
        2. Click 'Add Batch'
        3. Select a properly formatted .tsv file containing the standards to add
            *this method will silently overwrite existing files allowing batch updating*
        4. The task runs asynchronously so after a few seconds hit refresh
2. Add adducts.
    Curate -> Add Adduct
    [nM+X]^(y)
    * NM = n (number of metabolite molecules)
    * Delta formula = X (e.g. "-H2O+H")
    * Charge = y 
3. Add data
    #todo
4. Curate data
    #todo
    
### Advanced ###
* Further users can be configured from http://localhost:8000/admin

### Deployment ###
It is a bad idea to run the django development server in a production environment. It's probably OK to run behind a corporate/university firewall but should not be exposed to the internet. 
There are excellent detail guides available for various deployment platforms [e.g. from mozilla on deploying to Heroku ](https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Deployment)
## Licence
The source code in this repository is distributed under [the Apache 2.0 licence](http://www.apache.org/licenses/LICENSE-2.0).
