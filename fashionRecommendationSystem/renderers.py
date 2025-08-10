# app/renderers.py
from rest_framework.renderers import JSONRenderer


class EnvelopeJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context["response"]

        # Skip wrapping for special cases
        if getattr(response, "_skip_envelope", False) or data is None:
            return super().render(data, accepted_media_type, renderer_context)

        if response.exception:
            payload = {
                "success": False,
                "message": data.get("detail", "Request failed."),
                "data": None
            }
        elif isinstance(data, dict) and "data" in data and any(k in data for k in ["count", "page"]):
            # Pagination response — merge directly
            payload = {
                "success": True,
                "message": getattr(response, "_success_message", None),
                **data
            }
        else:
            # Normal response
            payload = {
                "success": True,
                "message": getattr(response, "_success_message", None),
                "data": data
            }

        return super().render(payload, accepted_media_type, renderer_context)
