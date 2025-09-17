from functools import wraps
from typing import Callable, Dict, Any
from jsonschema import validate as jsonschema_validate, ValidationError


def validate_query_params(schema: Dict[str, Any]) -> Callable:
    """
    Decorator for Tornado request handler methods to validate query params
    against a JSON Schema.

    Usage:
        @validate_query_params(schema)
        def get(self):
            ...

    On validation failure, responds with HTTP 400 and a JSON error message.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                # Collect parameters from request (query string)
                params: Dict[str, Any] = {}
                for key in self.request.arguments:
                    # Tornado stores arguments as lists of bytes; take first and decode
                    val_bytes = self.get_argument(key)
                    params[key] = val_bytes

                # Validate using jsonschema
                jsonschema_validate(instance=params, schema=schema)

            except ValidationError as e:
                # Return 400 with error details
                self.set_status(400)
                try:
                    # Tornado RequestHandler.write accepts dict -> JSON
                    self.write({"error": "Invalid query parameters", "details": e.message})
                except Exception:
                    self.write({"error": "Invalid query parameters"})
                self.finish()
                return
            except Exception as e:
                # Unexpected error while validating
                self.set_status(400)
                self.write({"error": "Error validating query parameters", "details": str(e)})
                self.finish()
                return

            # Validation passed; call the original handler
            return func(self, *args, **kwargs)

        return wrapper

    return decorator