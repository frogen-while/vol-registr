from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def static_v(path):
    url = static(path)
    version = getattr(settings, 'STATIC_ASSET_VERSION', 'dev')
    sep = '&' if '?' in url else '?'
    return f"{url}{sep}v={version}"
