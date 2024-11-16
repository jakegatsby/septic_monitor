# Septic Monitor

### Initial Setup (only done once!)


```
git clone git@github.com:ErniesProjects/septic_monitor.git    # clone the git repo
cd septic_monitor                                             # we want to be in the root of the repo, where this README.md is
make init                                                     # only do this once!!!
```

Cloning the repo and creating the venv only need to be done once.  Now, every time you want to work on the project, simply cd into the repository directory (with the README.md file) and activate the venv:

```
cd septic_monitor                # if you're not already in this directory
source venv/bin/activate
```

You'll see a `(venv)` to the left of your prompt in the terminal, to let you know the venv is active.

If you modify `setup.py` and add new dependencies, they can be installed using pip.  Make sure you always do this with the venv activated!

```
python3 -m pip install -e .
```


### Docker

Do the following *once* to setup Docker

```
make docker-install
htpasswd -c web/.htpasswd ernie
```

Some images are built and pushed to [dockerhub](https://hub.docker.com/u/erniesprojects) to avoid building on the Pi.

NOTE: If when building images locally you see apt errors about invalid signatures, it could be due to a date/time bug on some Ubuntu images.  If so, you can run `make fix-seccomp2` to fix this.

You can bring up the docker services with:

```
docker-compose up -d
```

Check that the containers are running with:

```
docker ps
```

You can bring down the docker containers with:

```
docker-compose down
```

Pull the latest versions of images with:

```
docker-compose pull
```

If you also want to delete the database files (after bringing the containers down) simply run:

```
make clean
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
