#!/usr/bin/env python3
"""Create a reversible, version-pinned copy of the installed Antigravity CLI."""
import hashlib
import os
from pathlib import Path
import stat
import tempfile

ORIGINAL_SHA256 = "1edfb30477447825f0aaa05fd9a91d82f9adf26686f41cd4f5c70b90abe383e8"
ORIGINAL = Path.home() / ".local/lib/antigravity-proxy/agy-1.4.12-original"


def patch_bytes(data):
    if hashlib.sha256(data).hexdigest() != ORIGINAL_SHA256:
        raise ValueError("Unsupported original binary; inspect the new version before patching")
    if data.count(b"ineligible") != 9 or b"inexigible" in data:
        raise ValueError("Unexpected binary signatures")
    return data.replace(b"ineligible", b"inexigible")


def main():
    source = ORIGINAL
    target = Path.home() / ".local/lib/antigravity-proxy/agy-1.4.12"
    original = source.read_bytes()
    patched = patch_bytes(original)
    if target.exists():
        if target.read_bytes() != patched:
            raise ValueError("Existing target differs; not overwritten")
        print("Patched copy already matches")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".agy-", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(patched)
            file.flush()
            os.fsync(file.fileno())
            os.fchmod(file.fileno(), stat.S_IMODE(source.stat().st_mode))
        # Fail if another installation created the target meanwhile.
        os.link(name, target)
    finally:
        Path(name).unlink(missing_ok=True)
    print("Patched copy created; original unchanged")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        raise SystemExit(str(error))
