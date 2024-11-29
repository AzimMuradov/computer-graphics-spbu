VENV = .venv
ifeq ($(OS),Windows_NT)
	VENV_BIN_DIR = $(VENV)/Scripts
else
	VENV_BIN_DIR = $(VENV)/bin
endif
ACTIVATE = $(VENV_BIN_DIR)/activate

PYTHON = $(VENV_BIN_DIR)/python
PIP = $(VENV_BIN_DIR)/pip

BLACK = $(VENV_BIN_DIR)/black
MYPY = $(VENV_BIN_DIR)/mypy

# Use GCC by default
CC = gcc

LIB_SRC = backend/library.c
LIB_OBJ = backend/library.o
LIB_TARGET = backend/libbackend.so


# TODO : create exec, install?, ...
# The main ones to use:
# run
# build
# check
# format
# clean
# clean-full


.PHONY: all
all: build


# Run application

.PHONY: run
run: run-app

.PHONY: run-app
run-app: install-reqs build-backend
	$(PYTHON) main.py


# Build application

.PHONY: build
build: build-app

.PHONY: build-app
build-app: install-reqs build-backend

.PHONY: install-reqs
install-reqs: $(ACTIVATE)

$(ACTIVATE): requirements.txt
	python -m venv $(VENV)
	$(PIP) install -r requirements.txt

# Build backend

.PHONY: build-backend
build-backend: $(LIB_TARGET)

$(LIB_TARGET): $(LIB_OBJ)
	$(CC) $(LIB_OBJ) -shared -o $(LIB_TARGET)

$(LIB_OBJ): $(LIB_SRC)
	$(CC) -c $(LIB_SRC) -Wall -pedantic -Wextra -Werror -O3 -fPIC -ffast-math -o $(LIB_OBJ)


# Check code

.PHONY: check
check: check-app-formatting lint-app test-backend

.PHONY: check-app-formatting
check-app-formatting: $(BLACK)
	$(BLACK) --check .

$(BLACK): install-reqs
	$(PIP) install black

.PHONY: lint-app
lint-app: $(MYPY)
	$(MYPY) .

$(MYPY): install-reqs
	$(PIP) install mypy

# TODO : test-backend
.PHONY: test-backend
test-backend:


# Format code

.PHONY: format
format: format-app

.PHONY: format-app
format-app: $(BLACK)
	$(BLACK) .


# Clean

.PHONY: clean
clean:
	rm -f frontend/*.c
	rm -f frontend/*.o
	rm -f frontend/*.so

	rm -f backend/*.o
	rm -f backend/*.so

.PHONY: clean-full
clean-full: clean
	rm -rf $(VENV)
