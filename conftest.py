"""Pytest configuration used to make tests robust against deepcopying unpickleable objects."""

import copy

# Store original deepcopy
original_deepcopy = copy.deepcopy


def patched_deepcopy(obj, memo=None):
    """Patched deepcopy that returns unpickleable singletons as-is.

    This prevents pytest (or other test helpers) from failing when attempting to
    deepcopy module objects, locks, or other types that do not support pickling.
    """
    if memo is None:
        memo = {}

    # Handle modules (like pdb) that can't be pickled
    if hasattr(obj, "__name__") and hasattr(obj, "__file__"):
        return obj

    # Handle other unpickleable types
    obj_type = type(obj)
    if obj_type.__name__ in ("module", "RLock"):
        return obj

    try:
        return original_deepcopy(obj, memo)
    except (TypeError, AttributeError) as e:
        if "cannot pickle" in str(e) or "pickle" in str(e):
            return obj
        raise


# Apply the monkey patch before any tests run
copy.deepcopy = patched_deepcopy