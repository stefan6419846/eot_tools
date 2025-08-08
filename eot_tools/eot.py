import struct
from enum import IntEnum
from pathlib import Path
from typing import cast, Union


class StructHelper:
    """
    Simple generic base container class for reading data of variable structure with the `struct`
    library in a sequential fashion.

    This follows section 3 of the specification to use little-endian values.
    """

    def __init__(self) -> None:
        self._data: bytes = b""
        self._offset: int = 0

    def _get(self, format_specifier: str, move: int) -> tuple[Union[bytes, int], ...]:
        result = struct.unpack_from(format_specifier, self._data, self._offset)
        self._offset += move
        return cast(tuple[Union[bytes, int]], result)

    def _get_unsigned_long(self) -> int:
        return cast(int, self._get("<L", 4)[0])

    def _get_unsigned_short(self) -> int:
        return cast(int, self._get("<H", 2)[0])

    def _get_bytes(self, length: int) -> bytes:
        return cast(bytes, self._get("<" + str(length) + "s", length)[0])

    @classmethod
    def _decode_utf16(cls, data: Union[tuple[bytes, ...], bytes]) -> str:
        if isinstance(data, tuple):
            data = b"".join(data)
        return data.decode("utf-16-le")


class Version(IntEnum):
    """
    Known EOT file versions according to section 3.
    """
    VERSION_0x00010000 = 0x00010000
    VERSION_0x00020001 = 0x00020001
    VERSION_0x00020002 = 0x00020002

    @classmethod
    def is_valid(cls, value: int) -> bool:
        # `__contains__` requires Python 3.12: https://docs.python.org/3/library/enum.html#enum.EnumType.__contains__
        return value in {cls.VERSION_0x00010000, cls.VERSION_0x00020001, cls.VERSION_0x00020002}


class FontEmbeddingLevel(IntEnum):
    """
    Known font embedding levels according to section 4.1.
    """

    INSTALLABLE = 0x0000
    RESTRICTED_LICENSE = 0x0002
    PREVIEW_PRINT = 0x0004
    EDITABLE = 0x0008
    NO_SUBSETTING = 0x0100
    BITMAP_ONLY = 0x0200


class ProcessingFlag(IntEnum):
    """
    Known processing flags according to section 4.2.
    """

    SUBSET = 0x00000001

    # https://www.w3.org/submissions/MTX/
    # Possibly patented.
    TT_COMPRESSED = 0x00000004

    FAIL_IF_VARIATION_SIMULATED = 0x00000010
    EMBED_EUDC = 0x00000020
    VALIDATION_TESTS = 0x00000040
    WEB_OBJECT = 0x00000080

    XOR_ENCRYPT_DATA = 0x10000000


# Magic number to use for data corruption checks according to section 3.
MAGIC_NUMBER = 0x504C

# XOR key used to calculate the root string checksum value (section 4.3.2).
ROOT_STRING_CHECKSUM_XOR_KEY = 0x50475342

# XOR key to decrypt the font data itself (section 4.4).
XOR_KEY = 0x50


class EOTFile(StructHelper):
    """
    Container for all EOT file data. The attributes will be populated as soon as the constructor is called.
    The attributes are not documented here, but (apart from the casing) they are identical to the tables in
    section 3 of the specification (column entry name).

    Specification: https://www.w3.org/submissions/EOT/
    """
    def __init__(self, data: Union[Path, bytes, str]):
        super().__init__()

        if isinstance(data, str):
            data = Path(data)
        if isinstance(data, Path):
            self._data = data.read_bytes()
        else:
            self._data = data

        self._populate()

        for flag in [self.flags, self.eudc_flags]:
            if flag & ProcessingFlag.TT_COMPRESSED == ProcessingFlag.TT_COMPRESSED:
                raise NotImplementedError("MicroType Express algorithm not implemented, as possibly patented.")
            if flag & ProcessingFlag.XOR_ENCRYPT_DATA == ProcessingFlag.XOR_ENCRYPT_DATA:
                raise NotImplementedError("XOR encryption not implemented due to the lack of examples.")

    def _skip_over_padding(self, i: int) -> None:
        padding: int = self._get_unsigned_short()
        if padding != 0x0000:
            raise ValueError(f"Unexpected padding{i} value {padding!r}")

    def _populate(self) -> None:
        self.eot_size: int = self._get_unsigned_long()
        font_data_size: int = self._get_unsigned_long()

        self.version: int = self._get_unsigned_long()
        if not Version.is_valid(self.version):
            raise ValueError(f"Unknown version {self.version!r}")

        self.flags: int = self._get_unsigned_long()
        self.font_panose: bytes = self._get_bytes(10)
        self.charset: int = self._get_bytes(1)[0]
        self.italic: int = self._get_bytes(1)[0]
        self.weight: int = self._get_unsigned_long()
        self.fs_type: int = self._get_unsigned_short()

        magic_number = self._get_unsigned_short()
        if magic_number != MAGIC_NUMBER:
            raise ValueError(f"Unexpected magic number {magic_number!r}")

        self.unicode_range1: int = self._get_unsigned_long()
        self.unicode_range2: int = self._get_unsigned_long()
        self.unicode_range3: int = self._get_unsigned_long()
        self.unicode_range4: int = self._get_unsigned_long()
        self.code_page_range1: int = self._get_unsigned_long()
        self.code_page_range2: int = self._get_unsigned_long()
        self.check_sum_adjustment: int = self._get_unsigned_long()

        for i in range(1, 5):
            reserved: int = self._get_unsigned_long()
            if reserved != 0:
                raise ValueError(f"Unexpected reserved value #{i}: {reserved!r}")

        self._skip_over_padding(1)
        family_name_size: int = self._get_unsigned_short()
        self.family_name: str = self._decode_utf16(self._get_bytes(family_name_size))
        self._skip_over_padding(2)
        style_name_size: int = self._get_unsigned_short()
        self.style_name: str = self._decode_utf16(self._get_bytes(style_name_size))
        self._skip_over_padding(3)
        version_name_size: int = self._get_unsigned_short()
        self.version_name: str = self._decode_utf16(self._get_bytes(version_name_size))
        self._skip_over_padding(4)
        full_name_size: int = self._get_unsigned_short()
        self.full_name: str = self._decode_utf16(self._get_bytes(full_name_size))

        self.root_string: list[str] = []
        self.root_string_checksum: int = -1
        self.eudc_code_page: int = -1
        self.signature: str = ""
        self.eudc_flags: int = 0
        self.eudc_font_data: bytes = b""

        if self.version > Version.VERSION_0x00010000:
            self._skip_over_padding(5)
            root_string_size = self._get_unsigned_short()
            # Section 4.3: "Multiple URLs, separated by NULL terminators, can be specified."
            self.root_string = self._decode_utf16(self._get_bytes(root_string_size)).split("\x00")
        if self.version > Version.VERSION_0x00020001:
            self.root_string_checksum = self._get_unsigned_long()
            self.eudc_code_page = self._get_unsigned_long()
            self._skip_over_padding(6)

            signature_size = self._get_unsigned_short()
            if signature_size != 0x0000:
                raise ValueError(f"Unexpected signature size {signature_size!r}")
            self.signature = self._decode_utf16(self._get_bytes(signature_size))

            self.eudc_flags = self._get_unsigned_long()
            eudc_font_size = self._get_unsigned_long()
            self.eudc_font_data = self._get_bytes(eudc_font_size)

        self.font_data: bytes = self._get_bytes(font_data_size)


# While there might be further functionality in this file, for now we only consider
# the main class as public API.
__all__ = [
    "EOTFile"
]
