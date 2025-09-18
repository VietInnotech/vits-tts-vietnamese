"""Application factory and dependency providers for the TTS service.

This module exposes:
  - provide_piper_tts: Create a shared PiperTTS instance from configuration.
  - provide_tts_service: Construct a TTSService instance with its dependencies.
  - create_app: Build and return a configured Litestar application.

The module also applies a targeted deepcopy patch to avoid test/runtime errors
when attempting to deepcopy unpickleable objects (modules, locks, etc.).
"""

import copy
from litestar import Litestar
from litestar.datastructures import State
from litestar.di import Provide
from litestar.static_files import StaticFilesConfig
from litestar.openapi.config import OpenAPIConfig

from .api.routers import TTSController, RootController
from .core.caching import provide_audio_cache
from .core.tts_service import TTSService
from .config import load_config, get_config
from .tts import create_piper_tts, PiperTTS


# Monkey patch deepcopy to handle modules that can't be pickled
original_deepcopy = copy.deepcopy


def patched_deepcopy(obj, memo=None):
    """Patched deepcopy that returns unpickleable singletons as-is.

    This avoids TypeError/AttributeError raised by the standard deepcopy
    implementation when encountering module objects or other unpickleable
    internals that are safe to pass by reference in this application.
    """
    if memo is None:
        memo = {}

    # Handle modules (like pdb) that can't be pickled
    if hasattr(obj, "__name__") and hasattr(obj, "__file__"):
        # Modules are singletons; returning the original reference is safe.
        return obj

    # Handle other unpickleable types
    obj_type = type(obj)
    if obj_type.__name__ in ("module", "RLock"):
        return obj

    try:
        return original_deepcopy(obj, memo)
    except (TypeError, AttributeError) as e:
        if "cannot pickle" in str(e) or "pickle" in str(e):
            # If we can't pickle it, return the original object
            return obj
        raise


# Apply the monkey patch
copy.deepcopy = patched_deepcopy


def provide_piper_tts() -> PiperTTS:
    """Create a shared PiperTTS instance based on configuration.

    Returns:
        PiperTTS: A PiperTTS instance constructed using model_path from config.
    """
    tts_cfg = get_config().get("tts", {}) or {}
    model_path = tts_cfg.get("model_path", "models/pretrained_vi.onnx")
    return create_piper_tts(model_path)


def provide_tts_service() -> TTSService:
    """Construct a TTSService with its dependencies.

    The provider creates the audio cache and constructs a TTSService instance.
    The service is intentionally lightweight so it can be injected without
    storing unpickleable objects on the application state.
    """
    cache = provide_audio_cache()
    config = get_config()
    model = provide_piper_tts()
    return TTSService(cache=cache, config=config, model=model)


def create_app() -> Litestar:
    """Create and configure the Litestar application.

    Loads configuration, sets up static file routes, registers route handlers
    and dependency providers, and returns the Litestar app instance.

    Returns:
        Litestar: Configured Litestar application.
    """
    # Load config once
    load_config()
    get_config()

    # Static files configuration: serve audio directory
    static_files = [
        StaticFilesConfig(path="/audio", directories=["audio"]),
    ]
 
    # Initialize state with deep_copy=False to prevent recursion during deepcopy
    state = State({}, deep_copy=False)
 
    # Create the Litestar app
    app = Litestar(
        route_handlers=[TTSController, RootController],
        static_files_config=static_files,
        dependencies={"service": Provide(provide_tts_service, sync_to_thread=True)},
        state=state,
        openapi_config=OpenAPIConfig(title="VITS-TTS API", version="1.0.0"),
    )
 
    return app
