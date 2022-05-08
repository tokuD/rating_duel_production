from django import template
from django.contrib.auth import get_user_model


register = template.Library()

@register.simple_tag
def url_replace(request, field, value):
    url_dict = request.GET.copy()
    url_dict.update({field: str(value)})
    return url_dict.urlencode()
