VENV = .venv
ifeq ($(OS),Windows_NT)
	VENV_BIN_DIR = $(VENV)/Scripts
else
	VENV_BIN_DIR = $(VENV)/bin
endif
ACTIVATE = $(VENV_BIN_DIR)/activate

PYTHON = $(VENV_BIN_DIR)/python
PIP = $(VENV_BIN_DIR)/pip

PYINSTALLER = $(VENV_BIN_DIR)/pyinstaller

BLACK = $(VENV_BIN_DIR)/black
MYPY = $(VENV_BIN_DIR)/mypy

PY_SRCS = main.py $(wildcard frontend/*.py)

# Use GCC by default
CC = gcc

LIB_SRC = backend/library.c
LIB_HDR = backend/library.h
LIB_OBJ = backend/library.o
LIB_TARGET = backend/libbackend.so


.PHONY: all
all: build


# Run application

.PHONY: run
run: build $(PY_SRCS) $(LIB_HDR)
	$(PYTHON) main.py


# Build application

.PHONY: build
build: build-backend install-deps

.PHONY: build-backend
build-backend: $(LIB_TARGET)

$(LIB_TARGET): $(LIB_OBJ)
	$(CC) $(LIB_OBJ) -shared -o $(LIB_TARGET)

$(LIB_OBJ): $(LIB_SRC)
	$(CC) -c $(LIB_SRC) -Wall -pedantic -Wextra -Werror -O3 -fPIC -ffast-math -o $(LIB_OBJ)

.PHONY: install-deps
install-deps: $(ACTIVATE)

$(ACTIVATE): requirements.txt
	python -m venv $(VENV)
	$(PIP) install -r requirements.txt


# Bundle application

.PHONY: bundle
bundle: drunk-cats

drunk-cats: $(LIB_TARGET) $(PY_SRCS) $(LIB_HDR) $(PYINSTALLER)
	$(PYINSTALLER)                     \
	--name="drunk-cats" --windowed     \
	--add-data="$(LIB_HDR):backend"    \
	--add-data="$(LIB_TARGET):backend" \
	main.py

$(PYINSTALLER): $(ACTIVATE)
	$(PIP) install pyinstaller


# Check application

.PHONY: check
check: test-backend check-frontend-formatting check-frontend-linting

.PHONY: test-backend
test-backend:
	# TODO : add tests for backend

.PHONY: check-frontend-formatting
check-frontend-formatting: $(BLACK)
	$(BLACK) --check .

.PHONY: check-frontend-linting
check-frontend-linting: $(MYPY)
	$(MYPY) .


# Format application

.PHONY: format
format: $(BLACK)
	$(BLACK) .


# Install dependencies for check and format

$(BLACK): $(ACTIVATE)
	$(PIP) install black

$(MYPY): $(ACTIVATE)
	$(PIP) install mypy


# Clean

.PHONY: clean
clean:
	rm -f backend/*.o
	rm -f backend/*.so

	rm -rf ./**/__pycache__

	rm -rf .mypy_cache

	rm -rf build
	rm -f drunk-cats.spec
	rm -f dist

.PHONY: clean-full
clean-full: clean
	rm -rf $(VENV)
