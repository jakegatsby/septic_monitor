SHELL:=/bin/bash

PICO_PRESSURE_IP=$(shell jq -r .network.ip pico_pressure_depth/config)

help:
	@echo init
	@echo thonny
	@echo docker-install
	@echo docker-config
	@echo fix-seccomp2
	@echo clean-db
	@echo clean-docker
	@echo build-base
	@echo push-base
	@echo mock
	@echo cp-index
	@echo rshell
	@echo flash-pico-pressure-depth
	@echo get-pico-pressure-depth


.PHONY: init
init:
	sudo apt update
	sudo apt -y install i2c-tools python3-venv python3-smbus python3-testresources python3-numpy python3-scipy postgresql-client-common postgresql-client-* libpq-dev
	python3 -m venv --clear --system-site-packages venv
	./venv/bin/python -m pip install pip "setuptools<71.0.0" setuptools-rust wheel --upgrade --no-cache-dir
	./venv/bin/python -m pip install --no-cache-dir -e .
	./venv/bin/python -m pip install --no-cache-dir ansible
	echo -e '\nsource .env' >> venv/bin/activate
	test -f .env || cp .env.sample .env


.PHONY: docker-install
docker-install:
	sudo apt update
	sudo apt-get -y install apt-transport-https ca-certificates curl gnupg lsb-release apache2-utils
	curl -sSL https://get.docker.com | sudo sh
	sudo usermod -aG docker ${USER}
	sudo systemctl enable docker
	@echo ==============================
	@echo = Please reboot your machine =
	@echo ==============================


.PHONY: docker-config
docker-config:
	sudo mkdir /etc/docker -p
	sudo cp daemon.json /etc/docker/daemon.json
	sudo systemctl restart docker


.PHONY: fix-seccomp2
fix-seccomp2:
	curl http://ftp.us.debian.org/debian/pool/main/libs/libseccomp/libseccomp2_2.5.1-1_armhf.deb --output libseccomp2_2.5.1-1_armhf.deb
	sudo dpkg -i libseccomp2_2.5.1-1_armhf.deb
	rm libseccomp2_2.5.1-1_armhf.deb -f


.PHONY: db-clean
db-clean:
	@echo WARNING - this will delete database data
	@echo -n "Are you sure? [y/N] " && read ans && [ $${ans:-N} == y ]
	sudo find septic_monitor -type f -name "*.pyc" -delete
	docker compose down
	docker container prune -f
	docker volume rm septic_monitor_pgdata; echo pgdata deleted
	sudo ./venv/bin/ansible-playbook ansible/fix-timescaledb-config.yml


.PHONY: docker-clean
docker-clean:
	@echo WARNING - this will delete database data
	@echo -n "Are you sure? [y/N] " && read ans && [ $${ans:-N} == y ]
	docker compose down
	docker container prune -f
	docker image prune -a -f
	docker volume prune -f
	docker system prune -a -f


.PHONY: docker-build
docker-build:
	docker build -t erniesprojects/sepmon .


.PHONY: docker-push
docker-push:
	docker push erniesprojects/sepmon

.PHONY: mock
mock:
	#	sudo apt -y install python3-numpy python3-scipy
	./venv/bin/python septic_monitor/mock.py


.PHONY: cp-index
cp-index:
	aws s3 cp ./dashboard/index.html s3://septic-monitor/index.html
	aws s3api put-object-acl --bucket septic-monitor --key index.html --acl public-read


.PHONY: fix-iptables
fix-iptables:
	sudo update-alternatives --set iptables /usr/sbin/iptables-legacy
	@echo reboot required


.PHONY: pipx
pipx:
	if ! which pipx; then sudo apt update && sudo apt-get -y install pipx && pipx ensurepath; fi

.PHONY: thonny
thonny: pipx
	sudo apt-get install python3-tk
	pipx upgrade thonny || pipx install thonny


.PHONY: support
support:
	# FROM Pi:  ssh ubuntu@<ec2-ip> -R 2222:localhost:22
	# FROM EC2: use sepsup keypair

.PHONY: jinja-cli
jinja-cli: pipx
	pipx upgrade jinja-cli || pipx install jinja-cli


.PHONY: docker-up
docker-up: jinja-cli
	@echo Pico pressure sensor IP: $(PICO_PRESSURE_IP)
	SEPMON_PICO_PRESSURE_IP=$(PICO_PRESSURE_IP) jinja -X 'SEPMON*' prometheus.yml.j2 > prometheus.yml
	docker compose up -d

# pipx fails to install rshell on the older rpi for
# some reason
.PHONY: rshell
rshell: pipx
	pipx upgrade rshell || pipx install rshell


.PHONY: flash-pico-pressure-depth-microdot
flash-pico-pressure-depth-microdot:
	rshell cp ./pico_pressure_depth/microdot.py /pyboard/
	rshell "repl ~ import machine ~ machine.soft_reset() ~"


.PHONY: flash-pico-pressure-depth
flash-pico-pressure-depth:
	rshell cp ./pico_pressure_depth/{main.py,config} /pyboard/
	rshell "repl ~ import machine ~ machine.soft_reset() ~"


.PHONY: get-pico-pressure-depth
get-pico-pressure-depth:
	@curl http://$(PICO_PRESSURE_IP):8080/metrics


.PHONY: ec2-start-sepmon
ec2-start-sepmon:
	aws ec2 start-instances --instance-ids $$(aws ec2 describe-instances --filters "Name=tag:Name,Values=sepmon" | jq -r '.Reservations[0].Instances[0].InstanceId')


.PHONY: ec2-stop-sepmon
ec2-stop-sepmon:
	aws ec2 stop-instances --instance-ids $$(aws ec2 describe-instances --filters "Name=tag:Name,Values=sepmon" | jq -r '.Reservations[0].Instances[0].InstanceId')

