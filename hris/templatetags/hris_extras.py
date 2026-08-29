"""
Custom template tags for HRIS import preview.
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Return dictionary[key] if key exists, otherwise empty string."""
    return dictionary.get(key, "")