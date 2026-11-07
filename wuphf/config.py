import math


def validate(settings):
    for key in ('advance_days','repeat_hours'):
        value=settings.get(key)
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:
            raise ValueError(key+' must be a positive number')
    if not isinstance(settings.get('channels',{}),dict) or set(settings.get('channels',{})) - {'telegram','email','ntfy'}:
        raise ValueError('Unknown channel')
