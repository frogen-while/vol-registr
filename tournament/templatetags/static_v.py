from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


def _clean_asset_path(path):
    if path is None:
        return ""
    return str(path).strip()


@register.simple_tag
def static_v(path):
    url = static(path)
    version = getattr(settings, 'STATIC_ASSET_VERSION', 'dev')
    sep = '&' if '?' in url else '?'
    return f"{url}{sep}v={version}"


@register.filter
def asset_url(path):
    asset_path = _clean_asset_path(path)
    if not asset_path:
        return ""

    if asset_path.startswith(("http://", "https://", "//", "/")):
        return asset_path

    if asset_path.startswith(("assets/", "css/", "js/")):
        return static(asset_path)

    media_url = getattr(settings, "MEDIA_URL", "/media/")
    media_prefix = media_url.lstrip("/")
    if media_prefix and asset_path.startswith(media_prefix):
        return f"/{asset_path.lstrip('/')}"

    return f"{media_url.rstrip('/')}/{asset_path.lstrip('/')}"
