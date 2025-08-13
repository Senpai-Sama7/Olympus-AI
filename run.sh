#!/usr/bin/env bash
set -e
npm --prefix server install
npm --prefix client install
docker-compose up --build
