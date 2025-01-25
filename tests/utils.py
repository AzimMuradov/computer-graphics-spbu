from pathlib import Path
from cffi import FFI


def get_backend(ffi: FFI):
    backend_dir = Path(__file__).parent.parent / "backend"

    with open(backend_dir / "library.h", mode="r") as f:
        dec = ""
        for line in f:
            if line.startswith("#"):
                continue
            dec += line
        ffi.cdef(dec)
    lib = ffi.dlopen(str(backend_dir / "libbackend_test.so"))

    return lib
