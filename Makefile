SHELL:=/bin/bash


.PHONY: init docker-install docker-config fix-seccomp2 mock clean build-base push-base

help:
	@echo init
	@echo docker-install
	@echo docker-config
	@echo fix-seccomp2
	@echo clean-db
	@echo clean-docker
	@echo build-base
	@echo push-base
	@echo mock
	@echo cp-index


init:
	sudo apt update
	sudo apt -y install i2c-tools python3-venv python3-smbus python3-testresources python3-numpy python3-scipy postgresql-client-common postgresql-client-* libpq-dev
	python3 -m venv --clear --system-site-packages venv
	./venv/bin/python -m pip install pip "setuptools<71.0.0" setuptools-rust wheel --upgrade --no-cache-dir
	./venv/bin/python -m pip install --no-cache-dir -e .
	./venv/bin/python -m pip install --no-cache-dir ansible
	echo -e '\nsource .env' >> venv/bin/activate
	test -f .env || cp .env.sample .env

docker-install:
	sudo apt update
	sudo apt-get -y install apt-transport-https ca-certificates curl gnupg lsb-release apache2-utils
	curl -sSL https://get.docker.com | sudo sh
	sudo usermod -aG docker ${USER}
	sudo systemctl enable docker
	@echo =================================
	@echo = Please reboot your machine!!! =
	@echo =================================


docker-config:
	sudo mkdir /etc/docker -p
	sudo cp daemon.json /etc/docker/daemon.json
	sudo systemctl restart docker


fix-seccomp2:
	curl http://ftp.us.debian.org/debian/pool/main/libs/libseccomp/libseccomp2_2.5.1-1_armhf.deb --output libseccomp2_2.5.1-1_armhf.deb
	sudo dpkg -i libseccomp2_2.5.1-1_armhf.deb
	rm libseccomp2_2.5.1-1_armhf.deb -f


clean-db:
	@echo WARNING - this will delete database data
	@echo -n "Are you sure? [y/N] " && read ans && [ $${ans:-N} == y ]
	sudo find septic_monitor -type f -name "*.pyc" -delete
	docker compose down
	docker container prune -f
	docker volume rm septic_monitor_pgdata; echo pgdata deleted
	sudo ./venv/bin/ansible-playbook ansible/fix-timescaledb-config.yml


.PHONY: clean-docker
clean-docker:
	@echo WARNING - this will delete database data
	@echo -n "Are you sure? [y/N] " && read ans && [ $${ans:-N} == y ]
	docker compose down
	docker container prune -f
	docker image prune -a -f
	docker volume prune -f
	docker system prune -a -f

.PHONY: build-base
build-base:
	docker build -t erniesprojects/sepmon_base -f Dockerfile.base .


.PHONY: push-base
push-base:
	docker push erniesprojects/sepmon_base


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
	

