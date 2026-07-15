#!/usr/bin/env python3
"""Fail-closed public-network URL and redirect policy for TENDER_FINDER.

Editable source definitions are untrusted configuration.  Runtime network
operations must call a helper in this module immediately before every request.
The policy accepts only HTTP(S), resolves hostnames, rejects a destination when
*any* resolved address is not globally routable, and validates every redirect
before following it.
"""
from __future__ import annotations

import ipaddress
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping


SUPPORTED_SCHEMES = frozenset({"http", "https"})
REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
DEFAULT_MAX_REDIRECTS = 5


class URLSafetyError(RuntimeError):
    """Raised before a request when a destination cannot be proven public."""


@dataclass(frozen=True)
class ValidatedPublicURL:
    url: str
    hostname: str
    addresses: tuple[str, ...]


@dataclass(frozen=True)
class SafeURLFetch:
    body: bytes
    status: int
    headers: Any
    final_url: str
    redirect_chain: tuple[str, ...]


@dataclass(frozen=True)
class SafeRequestsResult:
    response: Any
    final_url: str
    redirect_chain: tuple[str, ...]


Resolver = Callable[..., Iterable[Any]]


def _normalized_http_url(value: Any) -> tuple[str, urllib.parse.SplitResult]:
    raw = str(value or "").strip()
    if not raw:
        raise URLSafetyError("URL is empty")
    if raw.startswith(("\\\\", "//")):
        raise URLSafetyError("UNC and scheme-relative destinations are not allowed")
    if any(character in raw for character in ("\r", "\n", "\x00", "\\")):
        raise URLSafetyError("URL contains a forbidden control character or backslash")
    try:
        parsed = urllib.parse.urlsplit(raw)
        port = parsed.port
    except (TypeError, ValueError) as exc:
        raise URLSafetyError(f"Malformed URL: {exc}") from exc
    scheme = parsed.scheme.casefold()
    if scheme not in SUPPORTED_SCHEMES:
        raise URLSafetyError("Only http and https URLs are supported")
    if not parsed.netloc or not parsed.hostname:
        raise URLSafetyError("URL must include a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise URLSafetyError("Credentials in source URLs are not allowed")
    hostname = parsed.hostname.casefold().rstrip(".")
    if not hostname or hostname == "localhost" or hostname.endswith((".localhost", ".local", ".internal")):
        raise URLSafetyError("Local hostnames are not allowed")
    if any(character.isspace() for character in hostname):
        raise URLSafetyError("Hostname contains whitespace")
    try:
        ascii_hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise URLSafetyError("Hostname is not valid IDNA") from exc
    if len(ascii_hostname) > 253 or any(
        not label or len(label) > 63 for label in ascii_hostname.split(".")
    ):
        raise URLSafetyError("Hostname is malformed")
    if port is not None and not 1 <= port <= 65_535:
        raise URLSafetyError("URL port is outside the valid range")
    normalized_netloc = ascii_hostname
    if ":" in ascii_hostname and not ascii_hostname.startswith("["):
        normalized_netloc = f"[{ascii_hostname}]"
    if port is not None:
        normalized_netloc += f":{port}"
    normalized = urllib.parse.urlunsplit(
        (scheme, normalized_netloc, parsed.path or "/", parsed.query, "")
    )
    return normalized, urllib.parse.urlsplit(normalized)


def _public_address(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    try:
        address = ipaddress.ip_address(value.split("%", 1)[0])
    except ValueError as exc:
        raise URLSafetyError(f"Resolver returned an invalid IP address: {value!r}") from exc
    if not address.is_global:
        raise URLSafetyError(f"Destination resolves to a non-public address: {address}")
    return address


def validate_public_url(
    value: Any,
    *,
    resolve: bool = True,
    resolver: Resolver | None = None,
) -> ValidatedPublicURL:
    """Validate one URL and optionally prove its resolved addresses are public."""
    normalized, parsed = _normalized_http_url(value)
    hostname = str(parsed.hostname or "")
    addresses: list[str] = []
    try:
        literal = ipaddress.ip_address(hostname.split("%", 1)[0])
    except ValueError:
        literal = None
    if literal is not None:
        addresses.append(str(_public_address(str(literal))))
    elif resolve:
        lookup = resolver or socket.getaddrinfo
        try:
            results = lookup(hostname, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
        except (OSError, socket.gaierror) as exc:
            raise URLSafetyError(f"Hostname resolution failed for {hostname}: {exc}") from exc
        for result in results:
            try:
                candidate = str(result[4][0])
            except (IndexError, TypeError) as exc:
                raise URLSafetyError("Resolver returned a malformed address record") from exc
            public = str(_public_address(candidate))
            if public not in addresses:
                addresses.append(public)
        if not addresses:
            raise URLSafetyError(f"Hostname resolution returned no addresses for {hostname}")
    return ValidatedPublicURL(normalized, hostname, tuple(addresses))


def validate_public_url_syntax(value: Any) -> ValidatedPublicURL:
    """Perform the no-network portion of the policy for registry loading."""
    return validate_public_url(value, resolve=False)


def public_redirect_target(
    current_url: str,
    location: str,
    *,
    resolver: Resolver | None = None,
) -> ValidatedPublicURL:
    if not str(location or "").strip():
        raise URLSafetyError("Redirect response did not include a Location header")
    target = urllib.parse.urljoin(current_url, str(location).strip())
    return validate_public_url(target, resolve=True, resolver=resolver)


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def _header_value(headers: Any, name: str) -> str:
    if headers is None:
        return ""
    getter = getattr(headers, "get", None)
    if callable(getter):
        return str(getter(name, "") or "")
    if isinstance(headers, Mapping):
        return str(headers.get(name, "") or "")
    return ""


def safe_urllib_fetch(
    url: str,
    *,
    headers: Mapping[str, str] | None = None,
    timeout: float = 20,
    max_bytes: int = 2_000_000,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
    context: ssl.SSLContext | None = None,
    resolver: Resolver | None = None,
    opener: Any | None = None,
) -> SafeURLFetch:
    """GET bytes with certificate validation and prevalidated redirect hops."""
    if max_redirects < 0:
        raise ValueError("max_redirects cannot be negative")
    current = validate_public_url(url, resolve=True, resolver=resolver).url
    chain = [current]
    if opener is None:
        tls_context = context or ssl.create_default_context()
        opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=tls_context),
            _NoRedirectHandler(),
        )
    for redirect_index in range(max_redirects + 1):
        request = urllib.request.Request(current, headers=dict(headers or {}), method="GET")
        try:
            response = opener.open(request, timeout=timeout)
        except urllib.error.HTTPError as exc:
            if int(exc.code) not in REDIRECT_STATUSES:
                raise
            response = exc
        with response:
            status = int(getattr(response, "status", None) or getattr(response, "code", 0) or 0)
            response_headers = getattr(response, "headers", {})
            if status in REDIRECT_STATUSES:
                if redirect_index >= max_redirects:
                    raise URLSafetyError(f"Redirect limit exceeded ({max_redirects})")
                target = public_redirect_target(
                    current,
                    _header_value(response_headers, "Location"),
                    resolver=resolver,
                )
                current = target.url
                chain.append(current)
                continue
            reported_url = str(getattr(response, "geturl", lambda: current)() or current)
            validated_final = validate_public_url(reported_url, resolve=True, resolver=resolver)
            if validated_final.url != current:
                raise URLSafetyError("Transport followed an unvalidated redirect")
            body = response.read(max_bytes)
            return SafeURLFetch(body, status, response_headers, current, tuple(chain))
    raise URLSafetyError("Redirect loop did not produce a final response")


def safe_requests_request(
    method: str,
    url: str,
    *,
    request_callable: Callable[..., Any] | None = None,
    timeout: float = 20,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
    resolver: Resolver | None = None,
    **kwargs: Any,
) -> SafeRequestsResult:
    """Run a requests-compatible call while validating every redirect hop."""
    if max_redirects < 0:
        raise ValueError("max_redirects cannot be negative")
    if request_callable is None:
        import requests

        request_callable = requests.request
    kwargs.pop("allow_redirects", None)
    current = validate_public_url(url, resolve=True, resolver=resolver).url
    chain = [current]
    current_method = str(method or "GET").upper()
    for redirect_index in range(max_redirects + 1):
        response = request_callable(
            current_method,
            current,
            timeout=timeout,
            allow_redirects=False,
            **kwargs,
        )
        status = int(getattr(response, "status_code", 0) or 0)
        reported_url = str(getattr(response, "url", current) or current)
        if validate_public_url(reported_url, resolve=True, resolver=resolver).url != current:
            close = getattr(response, "close", None)
            if callable(close):
                close()
            raise URLSafetyError("Transport followed an unvalidated redirect")
        if status not in REDIRECT_STATUSES:
            return SafeRequestsResult(response, current, tuple(chain))
        if redirect_index >= max_redirects:
            close = getattr(response, "close", None)
            if callable(close):
                close()
            raise URLSafetyError(f"Redirect limit exceeded ({max_redirects})")
        target = public_redirect_target(
            current,
            _header_value(getattr(response, "headers", {}), "Location"),
            resolver=resolver,
        )
        close = getattr(response, "close", None)
        if callable(close):
            close()
        if status == 303 or (status in {301, 302} and current_method == "POST"):
            current_method = "GET"
            kwargs.pop("data", None)
            kwargs.pop("json", None)
        current = target.url
        chain.append(current)
    raise URLSafetyError("Redirect loop did not produce a final response")


def install_playwright_public_route(
    context: Any,
    *,
    resolver: Resolver | None = None,
    on_blocked: Callable[[str, str], None] | None = None,
) -> Callable[..., None]:
    """Block browser requests whose destination cannot be proven public.

    Playwright otherwise follows page and subresource redirects inside the
    browser process.  A context-wide route makes the same public-address policy
    apply before every HTTP(S) request.  Non-network document schemes used by
    the browser itself (``about:``, ``data:``, ``blob:``) are allowed; all
    other network schemes are rejected.
    """

    def route_handler(route: Any, request: Any) -> None:
        url = str(getattr(request, "url", "") or "")
        scheme = urllib.parse.urlsplit(url).scheme.casefold()
        try:
            if scheme in {"about", "data", "blob"}:
                route.continue_()
                return
            validate_public_url(url, resolve=True, resolver=resolver)
        except Exception as exc:
            if on_blocked:
                on_blocked(url, str(exc))
            route.abort("blockedbyclient")
            return
        route.continue_()

    context.route("**/*", route_handler)
    return route_handler
