import datetime
import io
import logging

from typing import Any
from typing import Final

import erddapy
import pandas as pd
import requests

from .models import Constraints
from .models import ERDDAPDataset


logger = logging.getLogger(__name__)

DEFAULT_SEARVEY_SESSION = requests.Session()
_REQUESTS_KWARGS_SENTINEL: Final[dict[str, Any]] = {}
_READ_CSV_KWARGS_SENTINEL: Final[dict[str, Any]] = {}


def ts_to_erddap(ts: datetime.datetime) -> str:
    return ts.strftime("%Y/%m/%dT%H:%M:%SZ")


# Adapted from:
# https://github.com/ioos/erddapy/blob/524783242c8b973ffd9bf5ab9f20f70516752f07/erddapy/url_handling.py#L14-L33
# @functools.lru_cache(maxsize=256)
def urlopen(
    url: str,
    session: requests.Session,
    requests_kwargs: dict[str, Any],
    timeout: float = 10,
) -> io.BytesIO:
    # logger.debug("Making a GET request to: %s", url)
    response = session.get(url, allow_redirects=True, timeout=timeout, **requests_kwargs)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise requests.exceptions.HTTPError(f"{response.content.decode()}") from err
    data = io.BytesIO(response.content)
    data.seek(0)
    return data


def get_erddap_url(
    dataset: ERDDAPDataset,
    constraints: Constraints,
    response: str = "csvp",
) -> str:
    erddap = erddapy.ERDDAP(
        server=dataset.server_url,
        protocol=dataset.protocol,
        response=response,
    )
    erddap.dataset_id = dataset.dataset_id
    erddap.constraints = {
        "time>=": ts_to_erddap(constraints.start_date),
        "time<=": ts_to_erddap(constraints.end_date),
        "latitude>=": constraints.lat_min,
        "latitude<=": constraints.lat_max,
        "longitude>=": constraints.lon_min,
        "longitude<=": constraints.lon_max,
    }
    url = erddap.get_download_url()
    return url


def query_erddap(  # pylint: disable=dangerous-default-value
    dataset: ERDDAPDataset,
    constraints: Constraints,
    session: requests.Session = DEFAULT_SEARVEY_SESSION,
    timeout: int = 10,
    read_csv_kwargs: dict[str, Any] = _READ_CSV_KWARGS_SENTINEL,
    requests_kwargs: dict[str, Any] = _REQUESTS_KWARGS_SENTINEL,
) -> pd.DataFrame:
    # Replace sentinel values with empty dicts (if necessary)
    # https://stackoverflow.com/a/67841737/592289
    if requests_kwargs is _REQUESTS_KWARGS_SENTINEL:
        requests_kwargs: dict[str, Any] = {}  # type: ignore[no-redef]
    if read_csv_kwargs is _READ_CSV_KWARGS_SENTINEL:
        read_csv_kwargs: dict[str, Any] = {}  # type: ignore[no-redef]
    # Make the query and parse the result
    url = get_erddap_url(dataset=dataset, constraints=constraints)
    logger.debug(url)
    data = urlopen(url, session=session, requests_kwargs=requests_kwargs, timeout=timeout)
    df = pd.read_csv(data, **read_csv_kwargs)
    return df
