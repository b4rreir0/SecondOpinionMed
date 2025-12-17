from django import template

register = template.Library()


@register.filter(name='mul')
def mul(value, arg):
    """Multiply value by arg. Returns numeric result or empty string on error."""
    try:
        return float(value) * float(arg)
    except Exception:
        return ''
