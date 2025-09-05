"""
Case-insensitive JSON field access utilities
"""
from typing import Any, Mapping


def get_ci(d: Mapping[str, Any], *keys: str, default=None):
    """
    Busca en dict ignorando mayúsculas/minúsculas y con alias.
    
    Args:
        d: Dictionary to search in
        *keys: Keys to try (in order of preference)
        default: Default value if no key is found
        
    Returns:
        Value of the first matching key, or default
        
    Example:
        >>> data = {"Status": "Running", "Progress": 45.5}
        >>> get_ci(data, "status")  # Returns "Running"
        >>> get_ci(data, "PROGRESS")  # Returns 45.5
        >>> get_ci(data, "missing", default=0)  # Returns 0
    """
    if not isinstance(d, Mapping):
        return default
    
    # Create lowercase mapping
    lower = {k.lower(): v for k, v in d.items()}
    
    # Try each key in order
    for k in keys:
        v = lower.get(k.lower())
        if v is not None:
            return v
    
    return default
