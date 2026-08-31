def strip_or_none(value):
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return value
