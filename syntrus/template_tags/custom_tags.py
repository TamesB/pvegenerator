from django import template

register = template.Library()


@register.filter
def index(indexable, i):
    return indexable[i]


@register.filter
def next_one(indexable, i):
    try:
        return indexable[i + 1]
    except IndexError:
        return int("0")


@register.filter
def previous_one(indexable, i):
    try:
        return indexable[i - 1]
    except IndexError:
        return int("0")
