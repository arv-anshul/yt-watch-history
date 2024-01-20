import logging
from typing import overload

import httpx

from api.configs import API_HOST_URL


@overload
def make_request_to_api(
    *,
    method: str,
    endpoint: str,
    timeout: int = 5,
    return_type: type[str] = str,
    **kwargs_for_request,
) -> str:
    ...


@overload
def make_request_to_api(
    *,
    method: str,
    endpoint: str,
    timeout: int = 5,
    return_type: type[bytes] = bytes,
    **kwargs_for_request,
) -> bytes:
    ...


@overload
def make_request_to_api(
    *,
    method: str,
    endpoint: str,
    timeout: int = 5,
    return_type: type[dict] = dict,
    **kwargs_for_request,
) -> dict:
    ...


def make_request_to_api(
    *,
    method: str,
    endpoint: str,
    timeout: int = 5,
    return_type: type[str | bytes | dict] = str,
    **kwargs_for_request,
) -> str | bytes | dict:
    try:
        res = httpx.request(
            method,
            f"{API_HOST_URL}{endpoint}",
            timeout=timeout,
            **kwargs_for_request,
        )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logging.exception(e)
        if isinstance(e, httpx.TimeoutException):
            e.add_note("Pass `timeout` argument in the function.")
        raise

    if not res.is_success:
        error_msg = f"[{res.status_code}]:{method}:{endpoint!r}"
        logging.error(error_msg)
        raise httpx.HTTPStatusError(error_msg, request=res.request, response=res)

    if return_type is str:
        return res.text
    elif return_type is bytes:
        return res.content
    elif return_type is dict:
        return res.json()
    else:
        raise ValueError(f"{return_type = }")
