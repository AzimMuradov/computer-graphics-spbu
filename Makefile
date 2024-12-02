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
PYTEST = $(VENV_BIN_DIR)/pytest

PY_SRCS = main.py $(wildcard frontend/*.py)

# Use GCC by default
CC = gcc

LIB_SRC = backend/library.c
LIB_HDR = backend/library.h
LIB_OBJ = backend/library.o
LIB_TARGET = backend/libbackend.so

LIB_OBJ_TEST = backend/library_test.o
LIB_TARGET_TEST = backend/libbackend_test.so

CFLAGS = -Wall -pedantic -Wextra -Werror -O3 -fPIC -ffast-math

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
	$(CC) -c $(LIB_SRC) $(CFLAGS) -o $(LIB_OBJ)

.PHONY: build-backend-test
build-backend-test: $(LIB_TARGET_TEST)

$(LIB_TARGET_TEST): $(LIB_OBJ_TEST)
        $(CC) $(LIB_OBJ_TEST) -shared -o $(LIB_TARGET_TEST)

$(LIB_OBJ_TEST): $(LIB_SRC)
        **$(CC) -c $(LIB_SRC) $(CFLAGS) -DTEST -o $(LIB_OBJ_TEST)**

.PHONY: install-deps
install-deps: $(ACTIVATE)

$(ACTIVATE): requirements.txt
	python -m venv $(VENV)
	$(PIP) install -r requirements.txt


# Check application

.PHONY: check
check: test-backend check-frontend-formatting check-frontend-linting

.PHONY: test-backend
test-backend: build-backend-test
	$(PYTEST) tests

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

.PHONY: clean-full
clean-full: clean
	rm -rf $(VENV)
