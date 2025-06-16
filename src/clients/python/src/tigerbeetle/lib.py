import ctypes
import platform
import sys
from pathlib import Path
from typing import Any
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


class NativeError(Exception):
    pass


class IntegerOverflowError(ValueError):
    pass


def _load_tbclient() -> ctypes.CDLL:
    prefix = ""
    arch = ""
    system = ""
    linux_libc = ""
    suffix = ""

    platform_machine = platform.machine().lower()

    if platform_machine == "x86_64" or platform_machine == "amd64":
        arch = "x86_64"
    elif platform_machine == "aarch64" or platform_machine == "arm64":
        arch = "aarch64"
    else:
        raise NativeError("Unsupported machine: " + platform.machine())

    if platform.system() == "Linux":
        prefix = "lib"
        system = "linux"
        suffix = ".so"
        libc = platform.libc_ver()[0]
        if libc == "glibc":
            linux_libc = "-gnu.2.27"
        elif libc == "musl":
            linux_libc = "-musl"
        else:
            raise NativeError("Unsupported libc: " + libc)
    elif platform.system() == "Darwin":
        prefix = "lib"
        system = "macos"
        suffix = ".dylib"
    elif platform.system() == "Windows":
        system = "windows"
        suffix = ".dll"
    else:
        raise NativeError("Unsupported system: " + platform.system())

    source_path = Path(__file__)
    source_dir = source_path.parent
    library_path = (
        source_dir / "lib" / f"{arch}-{system}{linux_libc}" / f"{prefix}tb_client{suffix}"
    )
    return ctypes.CDLL(str(library_path))


def validate_uint(*, bits: int, name: str, number: int) -> None:
    if number > 2**bits - 1:
        raise IntegerOverflowError(f"{name}=={number} is too large to fit in {bits} bits")
    if number < 0:
        raise IntegerOverflowError(f"{name}=={number} cannot be negative")


class c_uint128(ctypes.Structure):  # noqa: N801
    _fields_ = [("_low", ctypes.c_uint64), ("_high", ctypes.c_uint64)]  # noqa: RUF012

    @classmethod
    def from_param(cls, obj: int) -> Self:
        return cls(_high=obj >> 64, _low=obj & 0xFFFFFFFFFFFFFFFF)

    def to_python(self) -> int:
        return int(self._high << 64 | self._low)

def tb_assert(value: Any) -> None:
    """
    Python's built-in assert can be silently disabled if Python is run with -O.
    """
    if not value:
        raise AssertionError()


tbclient = _load_tbclient()
