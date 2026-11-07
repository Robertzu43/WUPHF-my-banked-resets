"""Local, dependency-free translations for the interface and reminders."""
import json
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=1)
def _all():
    return json.loads(Path(__file__).with_name('translations.json').read_text(encoding='utf-8'))

def languages():
    return tuple(_all())

def catalog(language):
    return _all().get(language, _all()['en'])

def translate(key, language='en', **values):
    return catalog(language).get(key, _all()['en'][key]).format(**values)
