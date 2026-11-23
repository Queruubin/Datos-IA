from http.client import RemoteDisconnected

import pytest
from urllib3.exceptions import ProtocolError

from app.adapters.ckan import DOWNLOAD_RETRIES, CkanClient, build_session


def test_default_session_retries_dropped_connections():
    adapter = build_session().get_adapter("https://datosabiertos.bogota.gov.co/")
    assert adapter.max_retries is DOWNLOAD_RETRIES
    assert DOWNLOAD_RETRIES.read >= 3


def test_dropped_connection_is_classified_as_retryable():
    # The real failure seen in production: the portal closed the connection mid-download.
    error = ProtocolError("Connection aborted.", RemoteDisconnected("Remote end closed"))
    remaining = DOWNLOAD_RETRIES.increment(method="GET", url="/file.csv", error=error)
    assert remaining.read == DOWNLOAD_RETRIES.read - 1


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_transient_http_statuses_are_retried(status):
    assert DOWNLOAD_RETRIES.is_retry("GET", status)


def test_client_uses_retrying_session_by_default(tmp_path):
    client = CkanClient("https://example.org/api/3/action", cache_dir=tmp_path)
    adapter = client._session.get_adapter("https://example.org/")
    assert adapter.max_retries is DOWNLOAD_RETRIES
