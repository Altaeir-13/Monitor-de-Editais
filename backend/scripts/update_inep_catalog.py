"""Build the canonical public-institution catalog from INEP Census 2024.

The preferred reproducible input is the official IES CSV supplied with
``microdados_censo_da_educacao_superior_2024.zip``.  Passing ``--csv`` uses an
already extracted copy.  Without ``--csv`` this script reads only the ZIP
central directory and the compressed IES member through HTTP byte ranges; it
never downloads the complete (roughly 435 MB) archive.

The MD5 manifest published in the archive calls the file
``MICRODADOS_CADASTRO_IES_2024.csv`` while the ZIP member is named
``MICRODADOS_ED_SUP_IES_2024.CSV``.  The expected MD5 below is the manifest
value and was verified byte-for-byte against the actual member.
"""

from __future__ import annotations

import argparse
import binascii
import csv
import hashlib
import io
import json
import re
import struct
import sys
import time
import urllib.error
import urllib.request
import zlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Iterable


SOURCE_URL = (
    "https://download.inep.gov.br/microdados/"
    "microdados_censo_da_educacao_superior_2024.zip"
)
SOURCE_MEMBER = (
    "microdados_censo_da_educacao_superior_2024/dados/"
    "MICRODADOS_ED_SUP_IES_2024.CSV"
)
SOURCE_MEMBER_BASENAME = "MICRODADOS_ED_SUP_IES_2024.CSV"
OFFICIAL_MD5_MANIFEST_NAME = "MICRODADOS_CADASTRO_IES_2024.csv"
EXPECTED_SHA256 = "aaa37fb9433d005686616bb9e48c5d7083526fdcc171973e787eed35a2ee349d"
EXPECTED_MD5 = "dbe25e67857aa68b12beaeffa194f53f"
REFERENCE_DATE = "2024-12-31"
EXPECTED_RAW_TOTAL = 317
USER_AGENT = (
    "Monitor-de-Editais/1.0 "
    "(+https://github.com/Altaeir-13/Monitor-de-Editais; INEP catalog update)"
)
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_RETRIES = 2
MAX_CENTRAL_DIRECTORY_BYTES = 16 * 1024 * 1024
MAX_COMPRESSED_MEMBER_BYTES = 64 * 1024 * 1024
MAX_UNCOMPRESSED_MEMBER_BYTES = 64 * 1024 * 1024

ADMINISTRATIVE_CATEGORIES = {
    1: "Pública Federal",
    2: "Pública Estadual",
    3: "Pública Municipal",
    7: "Especial",
}

ACADEMIC_ORGANIZATIONS = {
    1: "Universidade",
    2: "Centro Universitário",
    3: "Faculdade",
    4: "Instituto Federal",
    5: "Centro Federal de Educação Tecnológica",
}

REGION_BY_STATE = {
    "AC": "Norte",
    "AL": "Nordeste",
    "AM": "Norte",
    "AP": "Norte",
    "BA": "Nordeste",
    "CE": "Nordeste",
    "DF": "Centro-Oeste",
    "ES": "Sudeste",
    "GO": "Centro-Oeste",
    "MA": "Nordeste",
    "MG": "Sudeste",
    "MS": "Centro-Oeste",
    "MT": "Centro-Oeste",
    "PA": "Norte",
    "PB": "Nordeste",
    "PE": "Nordeste",
    "PI": "Nordeste",
    "PR": "Sul",
    "RJ": "Sudeste",
    "RN": "Nordeste",
    "RO": "Norte",
    "RR": "Norte",
    "RS": "Sul",
    "SC": "Sul",
    "SE": "Nordeste",
    "SP": "Sudeste",
    "TO": "Norte",
}

EXPECTED_REGION_COUNTS = {
    "Norte": 24,
    "Nordeste": 66,
    "Centro-Oeste": 27,
    "Sudeste": 166,
    "Sul": 34,
}

EXPECTED_STATE_COUNTS = {
    "AC": 2,
    "AL": 4,
    "AM": 3,
    "AP": 3,
    "BA": 10,
    "CE": 7,
    "DF": 5,
    "ES": 5,
    "GO": 14,
    "MA": 4,
    "MG": 22,
    "MS": 4,
    "MT": 4,
    "PA": 6,
    "PB": 4,
    "PE": 26,
    "PI": 4,
    "PR": 14,
    "RJ": 29,
    "RN": 5,
    "RO": 2,
    "RR": 3,
    "RS": 11,
    "SC": 9,
    "SE": 2,
    "SP": 110,
    "TO": 5,
}

EXPECTED_CATEGORY_COUNTS = {1: 122, 2: 139, 3: 28, 7: 28}
EXPECTED_ORGANIZATION_COUNTS = {1: 116, 2: 8, 3: 152, 4: 39, 5: 2}
EXPECTED_FALLBACK_CODES = {
    "5633",
    "15680",
    "21713",
    "23438",
    "23459",
    "23700",
    "23705",
    "24672",
}

REQUIRED_COLUMNS = {
    "NU_ANO_CENSO",
    "NO_REGIAO_IES",
    "SG_UF_IES",
    "NO_MUNICIPIO_IES",
    "CO_MUNICIPIO_IES",
    "TP_ORGANIZACAO_ACADEMICA",
    "TP_CATEGORIA_ADMINISTRATIVA",
    "TP_REDE",
    "CO_IES",
    "NO_IES",
    "SG_IES",
}


class CatalogError(RuntimeError):
    """Raised when the source cannot produce the pinned canonical catalog."""


class RangeNotSupportedError(CatalogError):
    """Raised before a full response body is read when HTTP Range is ignored."""


@dataclass(frozen=True)
class ZipMember:
    """The subset of central-directory metadata required for extraction."""

    name: str
    compression_method: int
    flags: int
    crc32: int
    compressed_size: int
    uncompressed_size: int
    local_header_offset: int


def _clean_text(value: str | None) -> str:
    """Trim INEP text and collapse layout-only whitespace deterministically."""

    return " ".join((value or "").strip().split())


def _digest_bytes(data: bytes) -> dict[str, str]:
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "md5": hashlib.md5(data).hexdigest(),  # noqa: S324 - provenance checksum
    }


def _validate_hashes(hashes: dict[str, str]) -> None:
    expected = {"sha256": EXPECTED_SHA256, "md5": EXPECTED_MD5}
    mismatches = [
        f"{name}: expected {expected[name]}, got {hashes.get(name)}"
        for name in expected
        if hashes.get(name) != expected[name]
    ]
    if mismatches:
        raise CatalogError("INEP CSV checksum mismatch (" + "; ".join(mismatches) + ")")


def _parse_content_range(value: str | None) -> tuple[int, int, int]:
    match = re.fullmatch(r"bytes\s+(\d+)-(\d+)/(\d+)", value or "")
    if not match:
        raise CatalogError(f"invalid or missing Content-Range header: {value!r}")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def _range_get(
    url: str,
    start: int,
    end: int,
    *,
    timeout: float,
    retries: int,
    expected_total: int | None = None,
) -> tuple[bytes, int]:
    """Fetch one exact inclusive range and reject servers returning the full ZIP."""

    if start < 0 or end < start:
        raise CatalogError(f"invalid byte range {start}-{end}")

    last_error: BaseException | None = None
    for attempt in range(retries + 1):
        request = urllib.request.Request(
            url,
            headers={
                "Accept-Encoding": "identity",
                "Range": f"bytes={start}-{end}",
                "User-Agent": USER_AGENT,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status = response.getcode()
                if status != 206:
                    raise RangeNotSupportedError(
                        f"server returned HTTP {status} for Range bytes={start}-{end}; "
                        "refusing to download the complete archive"
                    )
                if response.headers.get("Content-Encoding", "identity").lower() not in {
                    "",
                    "identity",
                }:
                    raise CatalogError("range response used an unsupported content encoding")
                actual_start, actual_end, total = _parse_content_range(
                    response.headers.get("Content-Range")
                )
                if (actual_start, actual_end) != (start, end):
                    raise CatalogError(
                        "range response does not match request: "
                        f"requested {start}-{end}, received {actual_start}-{actual_end}"
                    )
                if expected_total is not None and total != expected_total:
                    raise CatalogError(
                        f"archive size changed between requests: {expected_total} -> {total}"
                    )
                expected_length = end - start + 1
                data = response.read(expected_length + 1)
                if len(data) != expected_length:
                    raise CatalogError(
                        f"short/long range body: expected {expected_length}, got {len(data)}"
                    )
                return data, total
        except RangeNotSupportedError:
            raise
        except CatalogError:
            raise
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            OSError,
        ) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))

    raise CatalogError(
        f"failed to fetch Range bytes={start}-{end} after {retries + 1} attempts: "
        f"{last_error}"
    )


def _archive_size(url: str, *, timeout: float, retries: int) -> int:
    _, total = _range_get(url, 0, 0, timeout=timeout, retries=retries)
    if total < 22:
        raise CatalogError(f"remote object is too small to be a ZIP archive ({total} bytes)")
    return total


def _read_central_directory(
    url: str, *, timeout: float, retries: int
) -> tuple[bytes, int]:
    total = _archive_size(url, timeout=timeout, retries=retries)
    tail_size = min(total, 65_557)  # 22-byte EOCD plus maximum 65,535-byte comment.
    tail_start = total - tail_size
    tail, _ = _range_get(
        url,
        tail_start,
        total - 1,
        timeout=timeout,
        retries=retries,
        expected_total=total,
    )
    eocd_index = tail.rfind(b"PK\x05\x06")
    if eocd_index < 0 or eocd_index + 22 > len(tail):
        raise CatalogError("ZIP end-of-central-directory record was not found")

    (
        signature,
        disk_number,
        central_disk,
        entries_on_disk,
        entries_total,
        central_size,
        central_offset,
        comment_length,
    ) = struct.unpack_from("<4s4H2LH", tail, eocd_index)
    if signature != b"PK\x05\x06":
        raise CatalogError("invalid ZIP end-of-central-directory signature")
    if eocd_index + 22 + comment_length > len(tail):
        raise CatalogError("truncated ZIP end-of-central-directory comment")
    if disk_number or central_disk or entries_on_disk != entries_total:
        raise CatalogError("multi-disk ZIP archives are not supported")
    if entries_total == 0xFFFF or central_size == 0xFFFFFFFF or central_offset == 0xFFFFFFFF:
        raise CatalogError("ZIP64 archives are not supported by the selective downloader")
    if central_size <= 0 or central_size > MAX_CENTRAL_DIRECTORY_BYTES:
        raise CatalogError(f"unsafe ZIP central-directory size: {central_size} bytes")
    if central_offset + central_size > total:
        raise CatalogError("ZIP central directory points outside the remote object")

    central, _ = _range_get(
        url,
        central_offset,
        central_offset + central_size - 1,
        timeout=timeout,
        retries=retries,
        expected_total=total,
    )
    return central, entries_total


def _decode_zip_name(raw_name: bytes, flags: int) -> str:
    encoding = "utf-8" if flags & 0x800 else "cp437"
    try:
        return raw_name.decode(encoding)
    except UnicodeDecodeError as exc:
        raise CatalogError(f"cannot decode ZIP member name as {encoding}") from exc


def _find_member(central: bytes, entries_total: int) -> ZipMember:
    position = 0
    matches: list[ZipMember] = []
    parsed_entries = 0
    header_struct = struct.Struct("<4s6H3L5H2L")

    while position < len(central):
        if position + header_struct.size > len(central):
            raise CatalogError("truncated ZIP central-directory header")
        fields = header_struct.unpack_from(central, position)
        if fields[0] != b"PK\x01\x02":
            raise CatalogError(f"invalid central-directory signature at byte {position}")

        (
            _,
            _version_made,
            _version_needed,
            flags,
            compression_method,
            _modified_time,
            _modified_date,
            crc32,
            compressed_size,
            uncompressed_size,
            name_length,
            extra_length,
            comment_length,
            disk_start,
            _internal_attributes,
            _external_attributes,
            local_header_offset,
        ) = fields
        record_end = (
            position
            + header_struct.size
            + name_length
            + extra_length
            + comment_length
        )
        if record_end > len(central):
            raise CatalogError("truncated ZIP central-directory record")
        raw_name = central[
            position + header_struct.size : position + header_struct.size + name_length
        ]
        name = _decode_zip_name(raw_name, flags).replace("\\", "/")
        basename = PurePosixPath(name).name

        if basename.casefold() == SOURCE_MEMBER_BASENAME.casefold():
            if disk_start != 0:
                raise CatalogError("target member belongs to an unsupported ZIP disk")
            if compressed_size == 0xFFFFFFFF or uncompressed_size == 0xFFFFFFFF:
                raise CatalogError("ZIP64 target members are not supported")
            matches.append(
                ZipMember(
                    name=name,
                    compression_method=compression_method,
                    flags=flags,
                    crc32=crc32,
                    compressed_size=compressed_size,
                    uncompressed_size=uncompressed_size,
                    local_header_offset=local_header_offset,
                )
            )

        parsed_entries += 1
        position = record_end

    if parsed_entries != entries_total:
        raise CatalogError(
            f"central-directory entry count mismatch: expected {entries_total}, "
            f"parsed {parsed_entries}"
        )
    if len(matches) != 1:
        raise CatalogError(
            f"expected one ZIP member named {SOURCE_MEMBER_BASENAME}, found {len(matches)}"
        )
    member = matches[0]
    if member.name != SOURCE_MEMBER:
        raise CatalogError(
            f"unexpected ZIP member path: expected {SOURCE_MEMBER!r}, got {member.name!r}"
        )
    return member


def _extract_remote_member(
    url: str, *, timeout: float, retries: int
) -> tuple[bytes, ZipMember]:
    central, entry_count = _read_central_directory(
        url, timeout=timeout, retries=retries
    )
    member = _find_member(central, entry_count)
    if member.flags & 0x1:
        raise CatalogError("encrypted ZIP members are not supported")
    if member.compression_method not in {0, 8}:
        raise CatalogError(
            f"unsupported ZIP compression method {member.compression_method}"
        )
    if not 0 < member.compressed_size <= MAX_COMPRESSED_MEMBER_BYTES:
        raise CatalogError(
            f"unsafe compressed member size: {member.compressed_size} bytes"
        )
    if not 0 < member.uncompressed_size <= MAX_UNCOMPRESSED_MEMBER_BYTES:
        raise CatalogError(
            f"unsafe uncompressed member size: {member.uncompressed_size} bytes"
        )

    local_header, total = _range_get(
        url,
        member.local_header_offset,
        member.local_header_offset + 29,
        timeout=timeout,
        retries=retries,
    )
    (
        signature,
        _version_needed,
        local_flags,
        local_method,
        _modified_time,
        _modified_date,
        _crc32,
        _compressed_size,
        _uncompressed_size,
        name_length,
        extra_length,
    ) = struct.unpack("<4s5H3L2H", local_header)
    if signature != b"PK\x03\x04":
        raise CatalogError("invalid ZIP local-file-header signature")
    if local_flags != member.flags or local_method != member.compression_method:
        raise CatalogError("ZIP local header conflicts with central-directory metadata")

    data_start = member.local_header_offset + 30 + name_length + extra_length
    data_end = data_start + member.compressed_size - 1
    compressed, _ = _range_get(
        url,
        data_start,
        data_end,
        timeout=timeout,
        retries=retries,
        expected_total=total,
    )
    try:
        if member.compression_method == 0:
            data = compressed
        else:
            decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
            data = decompressor.decompress(
                compressed, MAX_UNCOMPRESSED_MEMBER_BYTES + 1
            )
            data += decompressor.flush()
            if not decompressor.eof or decompressor.unused_data:
                raise CatalogError("deflated ZIP member did not end cleanly")
    except zlib.error as exc:
        raise CatalogError("failed to decompress the INEP CSV member") from exc

    if len(data) != member.uncompressed_size:
        raise CatalogError(
            f"ZIP member size mismatch: expected {member.uncompressed_size}, got {len(data)}"
        )
    if (binascii.crc32(data) & 0xFFFFFFFF) != member.crc32:
        raise CatalogError("ZIP member CRC32 mismatch")
    return data, member


def _read_local_csv(path: Path) -> bytes:
    if not path.is_file():
        raise CatalogError(f"INEP CSV not found: {path}")
    size = path.stat().st_size
    if not 0 < size <= MAX_UNCOMPRESSED_MEMBER_BYTES:
        raise CatalogError(f"unsafe local CSV size: {size} bytes")
    return path.read_bytes()


def _required_int(row: dict[str, str], column: str, row_number: int) -> int:
    value = _clean_text(row.get(column))
    if not value.isdigit():
        raise CatalogError(f"row {row_number}: {column} must be numeric, got {value!r}")
    return int(value)


def _institution_from_row(row: dict[str, str], row_number: int) -> dict[str, object]:
    official_code = _clean_text(row.get("CO_IES"))
    if not official_code.isdigit():
        raise CatalogError(
            f"row {row_number}: CO_IES must be numeric, got {official_code!r}"
        )
    official_name = _clean_text(row.get("NO_IES"))
    if not official_name:
        raise CatalogError(f"row {row_number}: NO_IES is empty")

    state = _clean_text(row.get("SG_UF_IES")).upper()
    if state not in REGION_BY_STATE:
        raise CatalogError(f"row {row_number}: invalid SG_UF_IES {state!r}")
    region = _clean_text(row.get("NO_REGIAO_IES"))
    expected_region = REGION_BY_STATE[state]
    if region != expected_region:
        raise CatalogError(
            f"row {row_number}: {state} belongs to {expected_region}, got {region!r}"
        )

    municipality_code = _clean_text(row.get("CO_MUNICIPIO_IES"))
    if not municipality_code.isdigit():
        raise CatalogError(
            f"row {row_number}: CO_MUNICIPIO_IES must be numeric, "
            f"got {municipality_code!r}"
        )
    headquarters_city = _clean_text(row.get("NO_MUNICIPIO_IES"))
    if not headquarters_city:
        raise CatalogError(f"row {row_number}: NO_MUNICIPIO_IES is empty")

    category_code = _required_int(
        row, "TP_CATEGORIA_ADMINISTRATIVA", row_number
    )
    if category_code not in ADMINISTRATIVE_CATEGORIES:
        raise CatalogError(
            f"row {row_number}: unsupported public administrative category "
            f"{category_code}"
        )
    organization_code = _required_int(row, "TP_ORGANIZACAO_ACADEMICA", row_number)
    if organization_code not in ACADEMIC_ORGANIZATIONS:
        raise CatalogError(
            f"row {row_number}: unsupported academic organization {organization_code}"
        )

    official_initials = _clean_text(row.get("SG_IES")) or None
    initials = official_initials or f"IES-{official_code}"
    initials_origin = "official" if official_initials else "generated_fallback"

    return {
        "official_code": official_code,
        "official_name": official_name,
        "official_initials": official_initials,
        "initials": initials,
        "initials_origin": initials_origin,
        "region": region,
        "state": state,
        "headquarters_city": headquarters_city,
        "municipality_code": municipality_code,
        "administrative_category_code": category_code,
        "administrative_category_label": ADMINISTRATIVE_CATEGORIES[category_code],
        "academic_organization_code": organization_code,
        "academic_organization_label": ACADEMIC_ORGANIZATIONS[organization_code],
        "census_situation": "included_in_census_2024",
        "current_situation": "manual_review",
        "eligibility_status": "included",
        "eligibility_reason": None,
        "official_site_url": None,
        "inventory_source_url": SOURCE_URL,
        "inventory_reference_date": REFERENCE_DATE,
    }


def _assert_distribution(
    label: str, actual: Counter[object], expected: dict[object, int]
) -> None:
    if dict(actual) != expected:
        raise CatalogError(
            f"unexpected {label} distribution: expected {expected}, got {dict(actual)}"
        )


def _validate_institutions(institutions: list[dict[str, object]]) -> None:
    if len(institutions) != EXPECTED_RAW_TOTAL:
        raise CatalogError(
            f"expected {EXPECTED_RAW_TOTAL} public institutions, got {len(institutions)}"
        )
    codes = [str(item["official_code"]) for item in institutions]
    if len(set(codes)) != len(codes):
        duplicates = sorted(code for code, count in Counter(codes).items() if count > 1)
        raise CatalogError(f"duplicate CO_IES values: {duplicates}")

    _assert_distribution(
        "region",
        Counter(item["region"] for item in institutions),
        EXPECTED_REGION_COUNTS,
    )
    _assert_distribution(
        "state",
        Counter(item["state"] for item in institutions),
        EXPECTED_STATE_COUNTS,
    )
    _assert_distribution(
        "administrative category",
        Counter(item["administrative_category_code"] for item in institutions),
        EXPECTED_CATEGORY_COUNTS,
    )
    _assert_distribution(
        "academic organization",
        Counter(item["academic_organization_code"] for item in institutions),
        EXPECTED_ORGANIZATION_COUNTS,
    )
    fallback_codes = {
        str(item["official_code"])
        for item in institutions
        if item["initials_origin"] == "generated_fallback"
    }
    if fallback_codes != EXPECTED_FALLBACK_CODES:
        raise CatalogError(
            "unexpected institutions without official initials: "
            f"expected {sorted(EXPECTED_FALLBACK_CODES, key=int)}, "
            f"got {sorted(fallback_codes, key=int)}"
        )


def _parse_csv(data: bytes) -> list[dict[str, object]]:
    binary_stream: BinaryIO = io.BytesIO(data)
    with io.TextIOWrapper(binary_stream, encoding="cp1252", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";")
        fieldnames = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - fieldnames)
        if missing:
            raise CatalogError(f"INEP CSV is missing required columns: {missing}")

        institutions: list[dict[str, object]] = []
        for row_number, row in enumerate(reader, start=2):
            year = _clean_text(row.get("NU_ANO_CENSO"))
            network = _clean_text(row.get("TP_REDE"))
            if year == "2024" and network == "1":
                institutions.append(_institution_from_row(row, row_number))

    institutions.sort(key=lambda item: int(str(item["official_code"])))
    _validate_institutions(institutions)
    return institutions


def build_catalog(data: bytes) -> dict[str, object]:
    """Validate the pinned CSV and return the deterministic normalized catalog."""

    hashes = _digest_bytes(data)
    _validate_hashes(hashes)
    institutions = _parse_csv(data)
    return {
        "schema_version": 1,
        "metadata": {
            "url": SOURCE_URL,
            "member": SOURCE_MEMBER,
            "hashes": hashes,
            "official_md5_manifest_name": OFFICIAL_MD5_MANIFEST_NAME,
            "hash_note": (
                "The official MD5 manifest uses MICRODADOS_CADASTRO_IES_2024.csv; "
                "the ZIP member is MICRODADOS_ED_SUP_IES_2024.CSV and matches that "
                "MD5 byte-for-byte."
            ),
            "reference_date": REFERENCE_DATE,
            "filter": {"NU_ANO_CENSO": 2024, "TP_REDE": 1},
            "raw_total": EXPECTED_RAW_TOTAL,
        },
        "institutions": institutions,
    }


def _write_catalog(catalog: dict[str, object], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"
    temporary = output.with_name(f".{output.name}.tmp")
    temporary.write_text(serialized, encoding="utf-8", newline="\n")
    temporary.replace(output)


def _default_output() -> Path:
    return Path(__file__).resolve().parents[1] / "app" / "catalog" / "institutions_2024.json"


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Regenerate the normalized INEP 2024 public-institution catalog."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help="already extracted MICRODADOS_ED_SUP_IES_2024.CSV (no network)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_default_output(),
        help="output JSON path (defaults to app/catalog/institutions_2024.json)",
    )
    parser.add_argument(
        "--source-url",
        default=SOURCE_URL,
        help="official ZIP URL used only when --csv is omitted",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"per-request timeout in seconds (default: {DEFAULT_TIMEOUT_SECONDS:g})",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help=f"retries per HTTP range (default: {DEFAULT_RETRIES})",
    )
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    if not 0 <= args.retries <= 2:
        parser.error("--retries must be between 0 and 2")
    return args


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.csv:
            data = _read_local_csv(args.csv)
            source_description = str(args.csv)
        else:
            data, member = _extract_remote_member(
                args.source_url,
                timeout=args.timeout,
                retries=args.retries,
            )
            source_description = f"{args.source_url}!/{member.name}"
        catalog = build_catalog(data)
        _write_catalog(catalog, args.output)
    except CatalogError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(
        f"Wrote {len(catalog['institutions'])} institutions to {args.output} "
        f"from {source_description}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
