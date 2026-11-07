import math
import re
from .i18n import languages


def validate(settings):
    for key in ('advance_days','repeat_hours'):
        value=settings.get(key)
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:
            raise ValueError(key+' must be a positive number')
    if settings.get('language','en') not in languages(): raise ValueError('Unknown language')
    if not isinstance(settings.get('channels',{}),dict) or set(settings.get('channels',{})) - {'telegram','email','ntfy','gmail'}:
        raise ValueError('Unknown channel')

    gmail=settings.get('channels',{}).get('gmail')
    if gmail is not None:
        address=gmail.get('to') if isinstance(gmail,dict) else None
        if not isinstance(address,str) or len(address)>254 or not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?",address):
            raise ValueError('Enter one valid Gmail recipient address')
