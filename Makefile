.PHONY: help up down restart ps logs logs-mt5 logs-traefik logs-backend logs-monitor \
	build shell-mt5 shell-django

help:
	@echo "Stack control:"
	@echo "  make up"
	@echo "  make down"
	@echo "  make restart"
	@echo "  make ps"
	@echo ""
	@echo "Logs:"
	@echo "  make logs"
	@echo "  make logs-mt5"
	@echo "  make logs-traefik"
	@echo "  make logs-backend"
	@echo "  make logs-monitor"
	@echo ""
	@echo "Shell access:"
	@echo "  make shell-mt5"
	@echo "  make shell-django"

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose down
	docker compose up -d

ps:
	docker compose ps

build:
	docker compose build

logs:
	docker compose logs -f

logs-mt5:
	docker compose logs -f mt5

logs-traefik:
	docker compose logs -f traefik

logs-backend:
	docker compose logs -f django celery celery-beat redis postgres

logs-monitor:
	docker compose logs -f grafana prometheus alertmanager loki promtail cadvisor node-exporter uncomplicated-alert-receiver

shell-mt5:
	docker compose exec mt5 bash

shell-django:
	docker compose exec django bash
