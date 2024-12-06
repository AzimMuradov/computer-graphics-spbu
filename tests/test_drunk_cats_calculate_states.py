import pytest
from typing import *
import numpy as np
from cffi import FFI

window_width = 20
window_height = 20
scale = 1.0

ffi = FFI()

from pathlib import Path

backend_dir = Path(__file__).parent.parent / "backend"

with open(backend_dir / "library.h", mode="r") as f:
    dec = ""
    for line in f:
        if line.startswith("#"):
            continue
        dec += line
    ffi.cdef(dec)
lib = ffi.dlopen(str(backend_dir / "libbackend_test.so"))


@pytest.fixture
def backend():
    lib.drunk_cats_configure(3.0, 5.0)

    return lib


def create_positions(positions):
    return ffi.cast("OpenGlPosition *", ffi.from_buffer(np.array(positions)))


def test_single_cat(backend):
    positions = create_positions([(0.0, 0.0)])
    states = backend.drunk_cats_calculate_states(
        1, positions, window_width, window_height, scale
    )

    assert [states[i] for i in range(1)] == [0]
    backend.drunk_cats_free_states(states)


def test_two_cats_no_interactions(backend):
    positions = create_positions([(0.0, 0.0), (0.0, 0.8)])
    states = backend.drunk_cats_calculate_states(
        2, positions, window_width, window_height, scale
    )

    assert [states[i] for i in range(2)] == [0, 0]
    backend.drunk_cats_free_states(states)


def test_two_cats_both_hiss(backend):
    positions = create_positions([(0.0, 0.0), (0.0, 0.4)])
    states = backend.drunk_cats_calculate_states(
        2, positions, window_width, window_height, scale
    )

    assert [states[i] for i in range(2)] == [1, 1]
    backend.drunk_cats_free_states(states)


def test_two_cats_both_fight(backend):
    positions = create_positions([(0.0, 0.0), (0.0, 0.2)])
    states = backend.drunk_cats_calculate_states(
        2, positions, window_width, window_height, scale
    )

    assert [states[i] for i in range(2)] == [2, 2]
    backend.drunk_cats_free_states(states)


def test_three_cats_two_fight_one_hiss(backend):
    positions = create_positions([(0.0, 0.0), (0.0, 0.2), (0.0, 0.6)])
    states = backend.drunk_cats_calculate_states(
        3, positions, window_width, window_height, scale
    )

    assert [states[i] for i in range(3)] == [2, 2, 1]
    backend.drunk_cats_free_states(states)


def test_four_cats_all_fighting(backend):
    positions = create_positions([(0.0, 0.0), (0.0, 0.2), (0.0, 0.6), (0.0, 0.61)])
    states = backend.drunk_cats_calculate_states(
        4, positions, window_width, window_height, scale
    )

    assert [states[i] for i in range(4)] == [2, 2, 2, 2]
    backend.drunk_cats_free_states(states)
