import re
import unicodedata


def slugify(value):
    if value is None:
        return 'product'

    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = value.lower().strip()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    value = value.strip('-')

    return value or 'product'
