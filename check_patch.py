from pathlib import Path
import hashlib
root = Path.home()
original = (root / ".local/bin/agy").read_bytes()
patched = (root / ".local/lib/antigravity-proxy/agy-1.4.12").read_bytes()
assert hashlib.sha256(original).hexdigest() == "1edfb30477447825f0aaa05fd9a91d82f9adf26686f41cd4f5c70b90abe383e8", "Original changed"
assert original.count(b"ineligible") == 9
assert patched.count(b"ineligible") == 0 and patched.count(b"inexigible") == 9
assert len(original) == len(patched)
assert patched.replace(b"inexigible", b"ineligible") == original
assert (root / ".local/lib/antigravity-proxy/agy-1.4.12").stat().st_mode & 0o111
print("PASS: original unchanged, 9 substitutions, equal size, byte-exact reversal, executable")
