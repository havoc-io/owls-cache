# System imports
import threading
from functools import wraps
from contextlib import contextmanager
import logging


# Global persistent caching logger (with debug disabled by default)
_cache_log = logging.getLogger(__name__)
_cache_log.setLevel(logging.INFO)


def set_cache_debug(debug = True):
    """Sets whether or not to print debugging information for persistent cache
    hits/misses.

    Args:
        debug: Whether or not to print debugging information
    """
    _cache_log.setLevel(logging.DEBUG if debug else logging.INFO)


# Create a thread-local variable to track the current persistent cache
_thread_local = threading.local()


# Utility function to get the current thread's cache
def _get_cache():
    return getattr(_thread_local, 'cache', None)


# Utility function to set the current thread's cache
def _set_cache(cache):
    setattr(_thread_local, 'cache', cache)


def cached(name,
           mapper = lambda *args, **kwargs: args + tuple(iteritems(kwargs))):
    """Creates a persistently-cached version of a function.

    If there is no cache associated with the current thread's context, then no
    caching is performed.

    Args:
        name: A unique name by which to refer to the callable in the persistent
            cache
        mapper: A function which accepts the same arguments as the underlying
            function and maps them to a hashable tuple of values, which will
            then be hashed to act as the cache key.  If the argument types to
            the underlying function are not hashable (e.g. they are lists or
            dictionaries), then this function provides a mechanism by which to
            convert them to hashable types (e.g. tuples).  Defaults to a
            function which concatenates args and kwargs into a tuple.

    Returns:
        A cached version of the callable.
    """
    # Create the decorator
    def decorator(f):
        # Create the wrapper function
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Get the cache
            cache = _get_cache()

            # Get the value which will be used as a key within this namespace
            identifier = mapper(*args, **kwargs)

            # Check if caching is disabled
            if cache is None:
                _cache_log.debug('caching disabled for {0} in {1}'.format(
                    identifier,
                    name
                ))
                return f(*args, **kwargs)

            # Compute the cache key
            key = hash((name, identifier))

            # Check if we have a cache hit
            result = cache.get(key)
            if result is not None:
                _cache_log.debug('cache hit for {0} in {1}'.format(
                    identifier,
                    name
                ))
                return result

            # Log the cache miss
            _cache_log.debug('cache miss for {0} in {1}'.format(
                identifier,
                name
            ))

            # If not, do the hard work
            result = f(*args, **kwargs)

            # Cache the value
            cache.set(key, result)

            # All done
            return result

        # Return the wrapper function
        return wrapper

    # Return the decorator
    return decorator


@contextmanager
def caching_into(cache):
    """Provides a context manager for use with a `with` statement for control
    of caching.

    For example:

        my_cache = FileSystemPersistentCache()
        with caching_into(my_cache):
            # Do operations....

    Args:
        cache: The persistent cache to use
    """
    # Set the cache
    _set_cache(cache)

    # Let code run
    yield

    # All done
    _set_cache(None)
