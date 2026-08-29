# Prérequis : uv (https://docs.astral.sh/uv/)
UV ?= uv

setup:
	$(UV) sync --locked --all-extras

test:             ## 15 tests synthétiques, sans réseau : NS exact, forwards plats, prix fermés, chocs
	$(UV) run pytest

lint:
	$(UV) run ruff check src tests

all:              ## fetch + factors + forecast + recession + alm (exige le réseau ; ~2 min)
	$(UV) run ycc fetch
	$(UV) run ycc factors
	$(UV) run ycc forecast
	$(UV) run ycc recession
	$(UV) run ycc alm
