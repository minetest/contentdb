#!/bin/bash

set -e

docker_compose_version=$(docker-compose --version --short)
docker_compose_major=${docker_compose_version:0:1}

if [[ $docker_compose_major == "2" ]]; then
	sep="-"
else
	sep="_"
fi

container() {
	echo "contentdb${sep}$1${sep}1"
}
