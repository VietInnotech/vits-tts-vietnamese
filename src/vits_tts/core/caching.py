from cachetools import LRUCache


def provide_audio_cache() -> LRUCache:
    return LRUCache(maxsize=128)