#!/bin/bash

# build the application image
docker build -t team_mgmt_sys .

# create the network
docker network create team_management_system

# start postgres container
docker run -d --name postgres --net team_management_system -p 5432:5432 -e POSTGRES_USER=mansij -e POSTGRES_PASSWORD=password -e POSTGRES_DB=team_management_system postgres

# start the django app container
docker run -d --net team_management_system -p 8000:8000 team_mgmt_sys
