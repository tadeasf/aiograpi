#!/bin/bash

podman-compose down --remove-orphans
podman-compose up -d --build
