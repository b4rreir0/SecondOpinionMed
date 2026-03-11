from django import template

register = template.Library()


@register.filter(name='mul')
def mul(value, arg):
    """Multiply value by arg. Returns numeric result or empty string on error."""
    try:
        return float(value) * float(arg)
    except Exception:
        return ''


@register.filter(name='filter_by_document_type')
def filter_by_document_type(documents, doc_type):
    """Filter documents by document_type."""
    return [doc for doc in documents if doc.document_type == doc_type]
