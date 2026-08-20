# -*- coding: utf-8 -*-
"""HTTP/WebSocket origin, SSRF, and path trust-boundary checks."""

import ipaddress
import socket
from aiohttp.abc import AbstractResolver
from dataclasses import dataclass
from typing import Callable, Iterable, Set, Tuple
from urllib.parse import urlsplit

_PRIVATE_NETWORKS = tuple(ipaddress.ip_network(value) for value in (
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "100.64.0.0/10", "fc00::/7"
))
_BLOCKED_HOSTS = {"localhost", "metadata.google.internal"}
_BLOCKED_IPS = {ipaddress.ip_address("169.254.169.254")}


def assert_origin_allowed(
    origin: str, scheme: str, host: str, allowed_origins: Set[str]
) -> None:
    if not origin:
        return
    normalized = origin.rstrip("/").lower()
    same_origin = f"{scheme.lower()}://{host.lower()}".rstrip("/")
    explicit = {value.rstrip("/").lower() for value in allowed_origins}
    if normalized != same_origin and normalized not in explicit:
        raise ValueError("Cross-origin request is not allowed")


def _resolve(host: str) -> Iterable[str]:
    return {
        item[4][0]
        for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    }


def _always_blocked(address: ipaddress._BaseAddress) -> bool:
    return (
        address in _BLOCKED_IPS
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_unspecified
        or address.is_reserved
    )


def _is_private_allowed(address: ipaddress._BaseAddress) -> bool:
    return any(address in network for network in _PRIVATE_NETWORKS)


@dataclass(frozen=True)
class ProxyTarget:
    url: str
    hostname: str
    port: int
    addresses: Tuple[str, ...]


class PinnedResolver(AbstractResolver):
    """Keep the HTTP connection on the addresses validated before the request."""

    def __init__(self, target: ProxyTarget):
        self.target = target

    async def resolve(self, host: str, port: int = 0, family: int = socket.AF_INET):
        if host.lower().rstrip(".") != self.target.hostname:
            raise OSError("Unexpected proxy hostname")
        return [{
            "hostname": host,
            "host": address,
            "port": port,
            "family": socket.AF_INET6 if ":" in address else socket.AF_INET,
            "proto": 0,
            "flags": 0,
        } for address in self.target.addresses]

    async def close(self) -> None:
        return None


def resolve_safe_proxy_target(
    raw_url: str,
    method: str,
    allowed_hosts: Set[str],
    resolver: Callable[[str], Iterable[str]] = _resolve,
) -> ProxyTarget:
    normalized_method = str(method or "GET").upper()
    if normalized_method not in {"GET", "POST"}:
        raise ValueError("Proxy method is not allowed")
    parsed = urlsplit(str(raw_url or ""))
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only HTTP(S) proxy targets are allowed")
    if parsed.username or parsed.password:
        raise ValueError("Proxy URL credentials are not allowed")
    hostname = parsed.hostname.lower().rstrip(".")
    if hostname in _BLOCKED_HOSTS:
        raise ValueError("Proxy host is blocked")
    try:
        addresses = tuple(dict.fromkeys(str(item) for item in resolver(hostname)))
    except OSError as exc:
        raise ValueError("Proxy host could not be resolved") from exc
    if not addresses:
        raise ValueError("Proxy host did not resolve")
    explicit = hostname in {item.lower().rstrip(".") for item in allowed_hosts}
    for value in addresses:
        try:
            address = ipaddress.ip_address(value)
        except ValueError as exc:
            raise ValueError("Proxy host resolved to an invalid address") from exc
        if _always_blocked(address) or (not explicit and not _is_private_allowed(address)):
            raise ValueError("Proxy target address is not allowed")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return ProxyTarget(raw_url, hostname, port, addresses)
