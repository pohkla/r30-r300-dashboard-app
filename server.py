from __future__ import annotations

from typing import Any, Awaitable, Callable

from main import app as base_app


class ContentSecurityPolicyMiddleware:
    """Keep the existing CSP but allow JavaScript served by this application.

    The application currently sends ``script-src 'none'`` from main.py, which
    blocks /static/trade_form.js entirely. This outer ASGI wrapper only changes
    that directive to ``script-src 'self'``; all other security directives are
    preserved unchanged.
    """

    def __init__(self, app: Callable[..., Awaitable[Any]]) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        async def send_with_csp(message) -> None:
            if message.get("type") == "http.response.start":
                headers = list(message.get("headers", []))
                rewritten = []
                for name, value in headers:
                    if name.lower() == b"content-security-policy":
                        policy = value.decode("latin-1")
                        policy = policy.replace("script-src 'none'", "script-src 'self'")
                        value = policy.encode("latin-1")
                    rewritten.append((name, value))
                message["headers"] = rewritten
            await send(message)

        await self.app(scope, receive, send_with_csp)


app = ContentSecurityPolicyMiddleware(base_app)
