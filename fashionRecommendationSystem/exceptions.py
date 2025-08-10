from rest_framework.views import exception_handler as drf_handler


def exception_handler(exc, context):
    resp = drf_handler(exc, context)
    if resp is not None and isinstance(resp.data, dict) and "detail" in resp.data:
        # let renderer turn this into success:false + message
        pass
    return resp
