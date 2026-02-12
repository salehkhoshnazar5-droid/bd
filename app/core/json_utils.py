from collections.abc import Mapping

def make_json_safe(value):
    """Convert non-JSON-serializable values (e.g. bytes) to safe representations."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, Mapping):
        return {str(key): make_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(item) for item in value]
    return value