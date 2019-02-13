SHELL := /bin/bash
VERSION ?= latest

# The directory of this file
DIR := $(shell echo $(shell cd "$(shell  dirname "${BASH_SOURCE[0]}" )" && pwd ))

IMAGE_NAME ?= schutzwerk/canalyzat0r
CONTAINER_NAME ?= canalyzat0r

# Build the container
build: ## Build the image
	docker build --rm -t $(IMAGE_NAME):$(VERSION) .

build-local: ## Build the image using a local version of CANalyzat0r
	docker build -t $(IMAGE_NAME) -f Dockerfile.local .

build-nc: ## Build the container without caching
	docker build --rm --no-cache -t $(IMAGE_NAME) .

run: ## Run container
	touch $(DIR)/database.db && \
	xhost +local:root && \
	docker run \
		-it \
		--name $(CONTAINER_NAME) \
		-e DISPLAY=$$DISPLAY \
		--net=host \
		--privileged \
		--cap-add=CAP_SYS_MODULE \
		--device /dev/snd \
		-v /tmp/.X11-unix:/tmp/.X11-unix:ro \
		-v /lib/modules:/lib/modules \
		-v $(DIR)/database.db:/opt/CANalyzat0r/data/database.db \
		-v $(DIR)/sharedFolder:/root/sharedFolder \
		$(IMAGE_NAME):$(VERSION)

stop: ## Stop a running container
	docker stop $(CONTAINER_NAME)

remove: ## Remove a (running) container
	docker rm -f $(CONTAINER_NAME)

restart: ## Restart the container
	make remove; \
	make run

remove-image-force: ## Remove the latest image (forced)
	docker rmi -f $(IMAGE_NAME):$(VERSION)

# This will output the help for each task
.PHONY: help

help: ## This help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help
