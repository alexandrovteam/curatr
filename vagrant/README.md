# Vagrant 
This will start up a virtual machine running curatr with some default settings inside a virtual box running the Django server. It should take about 10 minutes depending on the speed of your internet connection.

Dependancies:
1. [Vagrant](vagrantup.com)
2. [Virtualbox](https://www.virtualbox.org/wiki/Downloads)

Steps to get curatr running inside a virtual machine using vagrant.
1. Clone or [download](https://github.com/alexandrovteam/curatr/archive/master.zip) the curatr repository
2. Find this directory `cd ./curatr/vagrant`
3. Edit start.sh and change the password on line 31 (optionally also change the username)
4. Run `vagrant up`

Curatr should now be visible at [localhost:8080/](http://localhost:8080/).


To change curatr settings:
1. From the vagrant folder: `vagrant ssh`
2. `nano mcf_standard_browser/mcf_standard_browser/settings.py`

To check curatr status / errors
1. `vagrant ssh`
2. `screen -r curatr`

To check celery status / errors
1. `vagrant ssh`
2. `screen -r celery`
