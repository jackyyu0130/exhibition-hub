"""Narrow TLS compatibility for the Culture Ministry HTTPS endpoint.

Newer Python/OpenSSL combinations may enable ``VERIFY_X509_STRICT`` by
default.  The current cloud.culture.tw certificate chain is otherwise valid,
but one certificate does not include the Subject Key Identifier required by
that optional strict mode.  This adapter disables only that extra flag for the
Culture Ministry origin.  CA-chain validation and hostname verification stay
enabled.
"""

from __future__ import annotations

import ssl
from typing import Any

import requests
from requests.adapters import HTTPAdapter


CULTURE_MINISTRY_HTTPS_PREFIX = "https://cloud.culture.tw/"


def culture_ministry_ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    strict_flag = getattr(ssl, "VERIFY_X509_STRICT", 0)
    if strict_flag:
        context.verify_flags &= ~strict_flag
    return context


class CultureMinistryTLSAdapter(HTTPAdapter):
    """Use a verified, non-strict SSL context for one official origin."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.ssl_context = culture_ministry_ssl_context()
        super().__init__(*args, **kwargs)

    def init_poolmanager(
        self,
        connections: int,
        maxsize: int,
        block: bool = False,
        **pool_kwargs: Any,
    ) -> None:
        pool_kwargs["ssl_context"] = self.ssl_context
        super().init_poolmanager(
            connections,
            maxsize,
            block=block,
            **pool_kwargs,
        )

    def proxy_manager_for(self, proxy: str, **proxy_kwargs: Any) -> Any:
        proxy_kwargs["ssl_context"] = self.ssl_context
        return super().proxy_manager_for(proxy, **proxy_kwargs)


def create_culture_ministry_session() -> requests.Session:
    session = requests.Session()
    session.mount(
        CULTURE_MINISTRY_HTTPS_PREFIX,
        CultureMinistryTLSAdapter(),
    )
    return session
