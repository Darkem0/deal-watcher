import httpx
import pytest

from deal_watcher.http_client import ControlledHttpClient, HttpClientError


def make_response_handler(response):
    calls = [0]

    def handler(request):
        calls[0] += 1
        return response

    return handler, calls


def test_http_client_retries_retryable_status_and_honors_html() -> None:
    call_count = 0
    seen_user_agent = ""

    def handler(request):
        nonlocal call_count, seen_user_agent
        call_count += 1
        seen_user_agent = request.headers["user-agent"]
        if call_count == 1:
            return httpx.Response(503, headers={"Retry-After": "0"}, request=request)
        return httpx.Response(
            200, headers={"content-type": "text/html"}, text="<html>ok</html>", request=request
        )

    client = ControlledHttpClient(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        min_interval_seconds=0,
        sleeper=lambda _: None,
    )
    result = client.get_html("https://example.test/page")
    assert result.attempts == 2
    assert seen_user_agent.startswith("deal-watcher/")
    client.close()


def test_http_client_does_not_retry_access_denied_or_wrong_content() -> None:
    for response in (
        httpx.Response(403),
        httpx.Response(200, headers={"content-type": "application/json"}, text="{}"),
    ):
        handler, calls = make_response_handler(response)

        client = ControlledHttpClient(
            client=httpx.Client(transport=httpx.MockTransport(handler)),
            max_retries=3,
            min_interval_seconds=0,
            sleeper=lambda _: None,
        )
        with pytest.raises(HttpClientError):
            client.get_html("https://example.test/page")
        assert calls[0] == 1
        client.close()
