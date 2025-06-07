# Septic Monitor

### Initial Setup (only done once!)


```
cd ~
git clone git@github.com:jakegatsby/septic_monitor.git        # clone the git repo
cd septic_monitor                                             # we want to be in the root of the repo, where this README.md is
make init                                                     # only do this once!!!
```

### Docker

Do the following *once* to setup Docker

```
make docker-install
make docker-config
htpasswd -c web/.htpasswd ernie
```

Some images are built and pushed to [dockerhub](https://hub.docker.com/u/erniesprojects) to avoid building on the Pi.

NOTE: If when building images locally you see apt errors about invalid signatures, it could be due to a date/time bug on some Ubuntu images.  If so, you can run `make fix-seccomp2` to fix this.

You can bring up the docker services with:

```
docker compose up -d
```

Check that the containers are running with:

```
docker ps
```

You can bring down the docker containers with:

```
docker compose down
```

Pull the latest versions of images with:

```
docker compose pull
```

If you also want to delete the database files (after bringing the containers down) simply run:

```
make clean-db
```



### Ongoing Development

Most of the commands in the "Initial Setup" are only required once.  From now on, if you want to work on your project, simply open a terminal, `cd` into the base of the repo, and activate the `venv`:

```
cd septic_monitor
source venv/bin/activate
```

If you add additional dependencies in `setup.py`, simply run the `python3 -m pip install -e .` command again (while in the repobase directory)


### Thonny

If you want to work on your project with Thonny, simply launch it from the menu and open main.py.  You'll have to configure Thonny to use Python from the venv you created:

`Tools -> Options -> Interpreter Tab` then select `Alternative Python 3 interpreter or virtual environment` in the drop-down menu and press `Locate another python executable`.  Use the file browser to find the `venv/bin/python3` file from the root of your repository.  You'll only need to set this up once.



### Flash Pico Firmware


- launch thonny without pico plugged in
- ensure thonny is in regular view (switch on top right if not)
- attach USB cable to Pi (no pico attached yet)
- holding down white BOOTSEL button, attach pico to USB cable
- in thonny, lower right, select "Install MicroPython"
- select the target volume with RP2350 in the name
- select the RP2 family
- in variant, select Pico W or Pico 2 W depending on which board you have
- click Install and wait to for it to say done, then Close


### Replication

Local:

```
ssh -nNT -R 9999:172.18.0.1:6379 user@192.168.2.12  # FIXME - systemd service
```

Remote:

```
# sshd_config
AllowTcpForwarding yes
GatewayPorts yes

# redis.conf
replicaof 172.18.0.1 9999
replica-announce-ip 192.168.2.12
```


### Grafana

#### Prometheus Data Source

- browse to http://localhost:3000/connections/datasources and add new data source of type Prometheus
- enter http://prometheus:9090 as the server URL
- scroll to the bottom and "Save & test"


