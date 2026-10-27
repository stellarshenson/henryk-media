.PHONY: clean data lint format requirements upgrade build install help sync_data_up sync_data_down sync_models_up sync_models_down test docs docs_serve create_environment remove_environment register_environment increment_version_number preflight

#################################################################################
# GLOBALS                                                                       #
#################################################################################

# running bare `make` prints the help screen
.DEFAULT_GOAL := help

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME = henryk-media
MODULE_NAME = henryk_media
PYTHON_VERSION = 3.13
PYTHON_INTERPRETER = python

# Set to true to make `make install` increment the patch version too
# By default only `make build` increments it
VERSION_INCREMENT_ON_INSTALL = false

# AWS S3 configuration
S3_BUCKET = general-purpose/henryk-media
AWS_PROFILE = stellars-tech
AWS_OPTS =

#################################################################################
# STYLES                                                                        #
#################################################################################

MSG_PREFIX = \033[1m\033[36m>>>\033[0m
WARN_PREFIX = \033[33m>>>\033[0m
ERR_PREFIX = \033[31m>>>\033[0m
WARN_STYLE = \033[33m
ERR_STYLE = \033[31m
HIGHLIGHT_STYLE = \033[1m\033[94m
OK_STYLE = \033[92m
NO_STYLE = \033[0m

#################################################################################
# ENVIRONMENT CONFIGURATION                                                     #
#################################################################################

# unified environment name for all managers
ENV_NAME = henryk-media
# uv configuration
VENV_PATH = $(PROJECT_DIR)/.venv
UV_OPTS =

#################################################################################
# COMMANDS                                                                      #
#################################################################################
## Install Python dependencies
.PHONY: requirements
requirements:
	@echo "$(MSG_PREFIX) installing requirements with uv"
	uv $(UV_OPTS) sync --python $(PROJECT_DIR)/.venv --extra dev
## Upgrade Python dependencies to latest versions
.PHONY: upgrade
upgrade:
	@echo "$(MSG_PREFIX) upgrading packages with uv"
	uv $(UV_OPTS) sync --python $(PROJECT_DIR)/.venv --extra dev --upgrade

## Delete all compiled Python files
clean:
	@echo "$(MSG_PREFIX) removing cache and compiled files"
	@find . -type f -name "*.py[co]" -delete
	@find . -type d -name '__pycache__' -exec rm -r {} +
	@find . -type d -name '*.egg-info' -exec rm -r {} +
	@find . -type d -name '.ipynb_checkpoints' -exec rm -r {} +
	@find . -type d -name '.pytest_cache' -exec rm -r {} +
	@echo "$(MSG_PREFIX) removing dist and build directory"
	@rm -rf build dist
	@echo "$(MSG_PREFIX) removing logs and tmp directories"
	@rm -rf logs tmp

## Restore .env from encrypted .env.enc (or create empty)
.env:
	@if [ -f ".env.enc" ]; then \
		echo "$(MSG_PREFIX) decrypting .env.enc"; \
		openssl enc -d -aes-256-cbc -pbkdf2 -in .env.enc -out .env || { rm -f .env; echo "$(ERR_PREFIX) $(ERR_STYLE)decryption failed$(NO_STYLE)"; exit 1; }; \
	else \
		echo "$(MSG_PREFIX) creating empty .env"; \
		touch .env; \
	fi

## Encrypt .env to .env.enc (AES-256)
.env.enc: .env
	@echo "$(MSG_PREFIX) encrypting .env"
	@openssl enc -aes-256-cbc -pbkdf2 -in .env -out .env.enc
	@echo "$(OK_STYLE)>>> .env.enc file successfully created$(NO_STYLE)"

## Lint using ruff (use `make format` to do formatting)
lint:
	@echo "$(MSG_PREFIX) linting the sourcecode"
	uvx ruff format --check
	uvx ruff check

## Format source code with ruff
format:
	@echo "$(MSG_PREFIX) formatting the sourcecode"
	uvx ruff check --fix
	uvx ruff format
## Run tests
test:
	@echo "$(MSG_PREFIX) checking for tests"
	@$(PROJECT_DIR)/.venv/bin/pytest --collect-only ./tests > /dev/null 2>&1; RESULT="$$?"; \
	if [ "$$RESULT" != "5" ]; then \
		echo "$(MSG_PREFIX) executing python tests"; \
		$(PROJECT_DIR)/.venv/bin/pytest --cov -v ./tests; \
	else \
		echo "$(WARN_PREFIX) $(WARN_STYLE)WARNING: no tests present$(NO_STYLE)"; \
	fi
## Download data from storage system
sync_data_down:
	@echo "$(MSG_PREFIX) downloading data from storage"
	aws s3 sync s3://$(S3_BUCKET)/data/ data/ --profile $(AWS_PROFILE) --exclude "*.ipynb_checkpoints/*" --exclude "*.gitkeep" --exclude "*.gitattributes" --exclude "*.gitignore" $(AWS_OPTS)

## Upload data to storage system
sync_data_up:
	@echo "$(MSG_PREFIX) uploading data to storage"
	aws s3 sync data/ s3://$(S3_BUCKET)/data/ --profile $(AWS_PROFILE) --exclude "*.ipynb_checkpoints/*" --exclude "*.gitkeep" --exclude "*.gitattributes" --exclude "*.gitignore" $(AWS_OPTS)

## Download models from storage system
sync_models_down:
	@echo "$(MSG_PREFIX) downloading models from storage"
	aws s3 sync s3://$(S3_BUCKET)/models/ models/ --profile $(AWS_PROFILE) --exclude "*.ipynb_checkpoints/*" --exclude "*.gitkeep" --exclude "*.gitattributes" --exclude "*.gitignore" $(AWS_OPTS)

## Upload models to storage system
sync_models_up:
	@echo "$(MSG_PREFIX) uploading models to storage"
	aws s3 sync models/ s3://$(S3_BUCKET)/models/ --profile $(AWS_PROFILE) --exclude "*.ipynb_checkpoints/*" --exclude "*.gitkeep" --exclude "*.gitattributes" --exclude "*.gitignore" $(AWS_OPTS)
#################################################################################
# UV ENVIRONMENT MANAGEMENT                                                     #
#################################################################################

## Preflight check for required tools
preflight:
	@if ! command -v $(PYTHON_INTERPRETER) >/dev/null 2>&1; then \
		echo "$(ERR_PREFIX) $(ERR_STYLE)ERROR: $(PYTHON_INTERPRETER) not found$(NO_STYLE)"; \
		echo "$(ERR_PREFIX) $(ERR_STYLE)install Python from https://www.python.org/downloads/$(NO_STYLE)"; \
		exit 1; \
	fi
	@if ! command -v aws >/dev/null 2>&1; then \
		echo "$(WARN_PREFIX) $(WARN_STYLE)WARNING: aws CLI not found - sync commands will fail$(NO_STYLE)"; \
	fi

## Set up Python interpreter environment
create_environment: preflight
	@if [ -d "$(PROJECT_DIR)/.venv" ]; then \
		echo "$(MSG_PREFIX) virtual environment already exists at $(HIGHLIGHT_STYLE).venv$(NO_STYLE). Skipping creation."; \
	else \
		if ! command -v uv >/dev/null 2>&1; then \
			echo "$(MSG_PREFIX) installing uv"; \
			pip install -q uv; \
		fi; \
		echo "$(MSG_PREFIX) creating uv virtual environment"; \
		uv $(UV_OPTS) venv -q --python $(PYTHON_VERSION); \
		echo "$(MSG_PREFIX) new uv virtual environment created. Activate with:"; \
		echo "$(MSG_PREFIX) Windows: $(HIGHLIGHT_STYLE).\\\.venv\\\Scripts\\\activate$(NO_STYLE)"; \
		echo "$(MSG_PREFIX) Unix/macOS: $(HIGHLIGHT_STYLE)source ./.venv/bin/activate$(NO_STYLE)"; \
		echo "$(MSG_PREFIX) installing dependencies"; \
		uv $(UV_OPTS) pip install -q --python $(PROJECT_DIR)/.venv -e ".[dev]"; \
		if command -v nb_venv_kernels >/dev/null 2>&1; then \
			echo "$(MSG_PREFIX) registering Jupyter kernel for $(HIGHLIGHT_STYLE)$(ENV_NAME)$(NO_STYLE)"; \
			nb_venv_kernels register --name $(ENV_NAME) $(PROJECT_DIR)/.venv >/dev/null 2>&1; \
			echo "$(OK_STYLE)>>> Kernel registered successfully$(NO_STYLE)"; \
		else \
			echo "$(MSG_PREFIX) registering Jupyter kernel with ipykernel"; \
			$(PROJECT_DIR)/.venv/bin/python -m ipykernel install --user --name=$(ENV_NAME) --display-name "Python [uv env:$(ENV_NAME)]"; \
			echo "$(OK_STYLE)>>> Kernel registered as $(ENV_NAME)$(NO_STYLE)"; \
		fi; \
	fi

## Remove previously created environment
remove_environment:
	@echo "$(MSG_PREFIX) removing uv virtual environment at $(HIGHLIGHT_STYLE).venv$(NO_STYLE)"
	@echo "$(MSG_PREFIX) unregistering Jupyter kernel $(HIGHLIGHT_STYLE)$(ENV_NAME)$(NO_STYLE)"
	@if command -v nb_venv_kernels >/dev/null 2>&1; then \
		nb_venv_kernels unregister $(PROJECT_DIR)/.venv >/dev/null 2>&1 || true; \
	else \
		jupyter kernelspec uninstall -y $(ENV_NAME) >/dev/null 2>&1 || true; \
	fi
	@-rm -rf ~/.local/share/jupyter/kernels/$(ENV_NAME) 2>/dev/null || true
	@rm -rf $(PROJECT_DIR)/.venv
	@echo "$(OK_STYLE)>>> Environment removed$(NO_STYLE)"
## Register Jupyter kernel for the environment
register_environment:
	@if [ ! -d "$(PROJECT_DIR)/.venv" ]; then \
		echo "$(ERR_PREFIX) $(ERR_STYLE)ERROR: uv virtual environment not found at .venv. Run 'make create_environment' first$(NO_STYLE)"; \
		exit 1; \
	fi
	@if command -v nb_venv_kernels >/dev/null 2>&1; then \
		echo "$(MSG_PREFIX) registering Jupyter kernel for $(HIGHLIGHT_STYLE)$(ENV_NAME)$(NO_STYLE)"; \
		nb_venv_kernels register --name $(ENV_NAME) $(PROJECT_DIR)/.venv >/dev/null 2>&1; \
		echo "$(OK_STYLE)>>> Kernel registered successfully$(NO_STYLE)"; \
	else \
		echo "$(MSG_PREFIX) registering Jupyter kernel with ipykernel"; \
		$(PROJECT_DIR)/.venv/bin/python -m ipykernel install --user --name=$(ENV_NAME) --display-name "Python [uv env:$(ENV_NAME)]"; \
		echo "$(OK_STYLE)>>> Kernel registered as $(ENV_NAME)$(NO_STYLE)"; \
	fi

## Install src modules (editable)
install: create_environment requirements clean $(if $(filter true,$(VERSION_INCREMENT_ON_INSTALL)),increment_version_number) .env

	@echo "$(MSG_PREFIX) installing $(MODULE_NAME) in editable mode"
	@uv $(UV_OPTS) pip install -q --python $(PROJECT_DIR)/.venv -e .
	@echo "$(OK_STYLE)>>> $(MODULE_NAME) installed$(NO_STYLE)"

## Build package
build: clean install increment_version_number test
	@echo "$(MSG_PREFIX) building $(MODULE_NAME)"
	$(PROJECT_DIR)/.venv/bin/python -m build --wheel

## Increment build number
increment_version_number:
	@echo "$(MSG_PREFIX) incrementing build number"
	$(PROJECT_DIR)/.venv/bin/python -c "import re; c=open('pyproject.toml').read(); m=re.search(r'version = \"(\\d+)\\.(\\d+)\\.(\\d+)\"',c); v=f'{m[1]}.{m[2]}.{int(m[3])+1}'; c=re.sub(r'version = \"\\d+\\.\\d+\\.\\d+\"',f'version = \"{v}\"',c,count=1); open('pyproject.toml','w').write(c); print('New version:',v)"

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################
## Make dataset
data: requirements
	@echo "$(MSG_PREFIX) generating dataset"
	$(PROJECT_DIR)/.venv/bin/python src/henryk_media/dataset.py

COMFYUI_DIR = $(PROJECT_DIR)/models/photo-animation/ComfyUI
COMFYUI_VENV = $(COMFYUI_DIR)/.venv
TORCH_INDEX_URL = https://download.pytorch.org/whl/cu130

FRAME_INTERPOLATION_WEIGHT = $(COMFYUI_DIR)/models/frame_interpolation/film_net_fp16.safetensors
FRAME_INTERPOLATION_REV = 219da3c9d8c357ceaf457fc1d5932c6e861b8dee
FRAME_INTERPOLATION_SHA256 = f226e51375dc839d4b40e5c3d63da560dd1ea1c962364ec78f5adf2d05db05c0

.PHONY: comfyui_frame_interpolation
## Download the FILM weights ComfyUI's core frame-interpolation nodes load to reach 30 fps
comfyui_frame_interpolation:
	@echo "$(MSG_PREFIX) downloading FILM weights into $(HIGHLIGHT_STYLE)$(COMFYUI_DIR)/models/frame_interpolation$(NO_STYLE)"
	@if ! echo "$(FRAME_INTERPOLATION_SHA256)  $(FRAME_INTERPOLATION_WEIGHT)" | sha256sum -c --status - 2>/dev/null; then \
		hf download Comfy-Org/Frame-Interpolation --revision $(FRAME_INTERPOLATION_REV) \
			--local-dir $(COMFYUI_DIR)/models frame_interpolation/film_net_fp16.safetensors; \
		echo "$(FRAME_INTERPOLATION_SHA256)  $(FRAME_INTERPOLATION_WEIGHT)" | sha256sum -c -; \
	fi
	@echo "$(OK_STYLE)>>> FILM weights ready$(NO_STYLE)"

.PHONY: comfyui_environment
## Create the ComfyUI environment with CUDA 13.0 torch and the node pack requirements
comfyui_environment:
	@echo "$(MSG_PREFIX) creating uv virtual environment at $(HIGHLIGHT_STYLE)$(COMFYUI_VENV)$(NO_STYLE)"
	uv $(UV_OPTS) venv -q --allow-existing --python $(PYTHON_VERSION) $(COMFYUI_VENV)
	@echo "$(MSG_PREFIX) installing torch, torchvision and torchaudio from $(TORCH_INDEX_URL)"
	uv $(UV_OPTS) pip install --python $(COMFYUI_VENV) --index-url $(TORCH_INDEX_URL) torch torchvision torchaudio
	@echo "$(MSG_PREFIX) installing ComfyUI and node pack requirements"
	uv $(UV_OPTS) pip install --python $(COMFYUI_VENV) \
		-r $(COMFYUI_DIR)/requirements.txt \
		-r $(COMFYUI_DIR)/custom_nodes/ComfyUI-AdvancedLivePortrait/requirements.txt \
		-r $(COMFYUI_DIR)/custom_nodes/ComfyUI-VideoHelperSuite/requirements.txt
	@echo "$(MSG_PREFIX) turning off ultralytics usage events"
	$(COMFYUI_VENV)/bin/yolo settings sync=False
	@echo "$(OK_STYLE)>>> ComfyUI environment ready$(NO_STYLE)"

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys; \
lines = sys.stdin.read(); \
matches = re.findall(r'\n## ([^\n]+)\n(?!\.PHONY)([a-zA-Z_.][a-zA-Z0-9_.-]*):', lines); \
matches = sorted(matches, key=lambda x: x[1].lower()); \
print('\nAvailable rules:\n'); \
print('\n'.join(['\033[36m{:25}\033[0m{}'.format(*reversed(match)) for match in matches])); \
print()
endef
export PRINT_HELP_PYSCRIPT

## Print the list of available commands
help:
	@$(PYTHON_INTERPRETER) -c "$${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)

# EOF
