import logging

import httpx


def make_request_to_api(
    *,
    method: str,
    url: str,
    timeout: int = 5,
    **kwargs_for_request,
) -> bytes:
    try:
        res = httpx.request(
            method,
            url,
            timeout=timeout,
            **kwargs_for_request,
        )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logging.exception(e)
        if isinstance(e, httpx.TimeoutException):
            e.add_note("Pass `timeout` argument in the function.")
        raise

    if not res.is_success:
        error_msg = f"[{res.status_code}]:{method}:{url!r}"
        logging.error(error_msg)
        raise httpx.HTTPStatusError(error_msg, request=res.request, response=res)

    return res.content
