from __future__ import annotations

from django import VERSION as DJANGO_VERSION


def patch_unfold_flatten_context() -> None:
    """
    Work around Django 5.0.x RequestContext.flatten() bug (#35417)
    used by django-unfold component rendering.
    """
    if DJANGO_VERSION >= (5, 1):
        return

    try:
        from unfold.templatetags import unfold as unfold_tags
    except Exception:
        return

    def _safe_flatten_context(context):
        keys = set()

        for item in getattr(context, "dicts", []):
            if hasattr(item, "keys"):
                keys.update(item.keys())

        return {key: context[key] for key in keys}

    unfold_tags._flatten_context = _safe_flatten_context
