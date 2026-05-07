import re

IPV4_PATTERN = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
DOMAIN_PATTERN = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.[A-Za-z]{2,}$")
MD5_PATTERN = re.compile(r"^[a-fA-F0-9]{32}$")
SHA1_PATTERN = re.compile(r"^[a-fA-F0-9]{40}$")
SHA256_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")


def detect_indicator_type(value: str) -> str:
    value = value.strip()
    if IPV4_PATTERN.match(value):
        return "ip"
    if MD5_PATTERN.match(value):
        return "md5"
    if SHA1_PATTERN.match(value):
        return "sha1"
    if SHA256_PATTERN.match(value):
        return "sha256"
    if DOMAIN_PATTERN.match(value):
        return "domain"
    return "unknown"