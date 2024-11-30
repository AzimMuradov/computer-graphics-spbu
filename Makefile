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


# The main ones to use:
# run
# runi
# build
# check
# format
# clean
# clean-full


.PHONY: all
all: build


# Run application

.PHONY: run
run: build
	./drunk-cats

.PHONY: runi
runi: $(PY_SRCS) install-reqs $(LIB_HDR) build-backend
	$(PYTHON) main.py


# Build application

.PHONY: build
build: build-app

.PHONY: build-app
build-app: drunk-cats

drunk-cats: $(PY_SRCS) $(PYINSTALLER) $(LIB_HDR) $(LIB_TARGET)
	$(PYINSTALLER) \
		--name="drunk-cats" --distpath="." -F \
		--add-data="$(LIB_HDR):backend" \
		--add-data="$(LIB_TARGET):backend" \
		main.py

$(PYINSTALLER): $(ACTIVATE)
	$(PIP) install pyinstaller

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

$(BLACK): $(ACTIVATE)
	$(PIP) install black

.PHONY: lint-app
lint-app: $(MYPY)
	$(MYPY) .

$(MYPY): $(ACTIVATE)
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
	rm -f backend/*.o
	rm -f backend/*.so

	rm -rf ./**/__pycache__

	rm -rf .mypy_cache

	rm -rf build
	rm -f drunk-cats.spec
	rm -f drunk-cats

.PHONY: clean-full
clean-full: clean
	rm -rf $(VENV)
