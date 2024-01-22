import logging

import httpx

from api.configs import API_HOST_URL


def make_request_to_api(
    *,
    method: str,
    endpoint: str,
    timeout: int = 5,
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

    return res.content
