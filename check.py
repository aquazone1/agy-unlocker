"""Offline check; run with python3 check.py. No original binary required."""
import hashlib
import patch
from proxy_config import build_config

fixture = b"prefix:" + b"ineligible:" * 9 + b"https_proxy:HTTPS_PROXY:suffix"
saved_hash = patch.ORIGINAL_SHA256
try:
    patch.ORIGINAL_SHA256 = hashlib.sha256(fixture).hexdigest()
    result = patch.patch_bytes(fixture)
    assert len(result) == len(fixture)
    assert result.count(b"inexigible") == 9
    assert b"ineligible" not in result
    assert result.replace(b"inexigible", b"ineligible") == fixture
    assert b"https_proxy:HTTPS_PROXY" in result
    for invalid in (b"unknown binary", fixture + b"changed", result):
        try:
            patch.patch_bytes(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Unsupported input accepted")
finally:
    patch.ORIGINAL_SHA256 = saved_hash
uri = "vless://00000000-0000-0000-0000-000000000000@example.com:443?type=tcp&security=reality&sni=example.com&pbk=test"
config = build_config(uri)
assert config["inbounds"][0]["listen"] == "127.0.0.1"
assert config["outbounds"][0]["tls"]["enabled"] is True
assert config["route"]["final"] == config["outbounds"][0]["tag"]
for invalid in ("trojan://example.com", uri.replace("type=tcp", "type=xhttp"), uri.replace("00000000-0000-0000-0000-000000000000", "invalid")):
    try:
        build_config(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("Unsupported proxy input accepted")
print("PASS: reversible patch, version guard, loopback-only proxy, transport and UUID validation")
