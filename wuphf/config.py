import math
from .i18n import languages


def validate(settings):
    for key in ('advance_days','repeat_hours'):
        value=settings.get(key)
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:
            raise ValueError(key+' must be a positive number')
    if settings.get('language','en') not in languages(): raise ValueError('Unknown language')
    if not isinstance(settings.get('channels',{}),dict) or set(settings.get('channels',{})) - {'telegram','email','ntfy'}:
        raise ValueError('Unknown channel')
