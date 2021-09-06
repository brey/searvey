import pytest

from requests import HTTPError
from requests import ReadTimeout

from searvey import erddap


def test_openurl_wrong_url_raises() -> None:
    with pytest.raises(HTTPError) as exc:
        erddap.urlopen(
            url="https://www.google.com/gibberish",
            session=erddap.DEFAULT_SEARVEY_SESSION,
            requests_kwargs={},
        )
    assert "The requested URL <code>/gibberish</code> was not found on this server" in str(exc)


def test_openurl_timeout_raises() -> None:
    with pytest.raises(ReadTimeout) as exc:
        erddap.urlopen(
            url="https://www.google.com/gibberish",
            session=erddap.DEFAULT_SEARVEY_SESSION,
            requests_kwargs={},
            timeout=0.001,
        )
    assert "Read timed out" in str(exc)
