__author__ = 'palmer'
from django import template
register = template.Library()

@register.filter
def form_id(form,id):
    return form['yesno_{}'.format(id)]