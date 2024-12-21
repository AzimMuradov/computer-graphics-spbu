import pytest
from typing import *
import os
import tempfile
import shutil
from frontend.core import Core, CustomError
from cffi import FFI
from pathlib import Path

backend_dir = Path(__file__).parent.parent / "backend"
shared_library_path = str(backend_dir / "libbackend.so")

def test_no_backend_library_built():
    with pytest.raises(CustomError):
        original_dir = os.path.dirname(shared_library_path)
        temp_dir = tempfile.mkdtemp()
        existed = False

        try:
            # move .so to temp dir
            if os.path.exists(shared_library_path):
                existed = True
                temp_file_path = os.path.join(temp_dir, os.path.basename(shared_library_path))
                shutil.move(shared_library_path, temp_file_path)

            try:
                Core()
            except OSError as err:
                # TODO: custom error expected with some proper message
                #       (eg. 'Shared library must be built before running application')
                raise AssertionError("Expected custom error class with proper message, but got ", err)
        finally:
            # move .so back to its dir
            if (existed):
                restored_file_path = os.path.join(original_dir, os.path.basename(shared_library_path))
                shutil.move(temp_file_path, restored_file_path)
            
            shutil.rmtree(temp_dir)


def test_passed_hiss_less_than_fight_range():
    with pytest.raises(CustomError):
        ffi = FFI()
        with open(backend_dir / "library.h", mode="r") as f:
            dec = ""
            for line in f:
                if line.startswith("#"):
                    continue
                dec += line
            ffi.cdef(dec)
        backend = ffi.dlopen(shared_library_path)

        hiss_radius = 10
        fight_radius = hiss_radius + 1
        
        # TODO: expected a check for `fight_radius < hiss_radius` which is stated in code comments, but no custom exception thrown
        backend.drunk_cats_configure(fight_radius, hiss_radius)