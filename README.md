# owls-cache

[![Build Status](https://travis-ci.org/havoc-io/owls-cache.png?branch=master)](https://travis-ci.org/havoc-io/owls-cache)

This is the caching module for the OWLS analysis framework.  This module
implements transient and persistent memoization for Python functions.  Transient
memoization is implemented via an in-memory dictionary.  Persistent memoization
is implemented via a flexible backend interface, with implementations for
on-disk and Redis storage currently available.

This code is made available under the terms of the MIT license.


## Requirements

The OWLS analysis framework supports Python 2.7, 3.3, 3.4, and 3.5.


## Installation

Installation is most easily performed via pip:

    pip install git+https://github.com/havoc-io/owls-cache.git

Alternatively, you may execute `setup.py` manually, but this is not supported.


## Usage

owls-cache provides both transient and persistent memoization.  Both are
provided via a decorator, with different optional arguments depending on the
memoization type and storage.


### Transient memoization

Transient memoization is provided by the `owls_cache.transient.cached`
decorator:

    # owls-cache imports
    from owls_cache.transient import cached

    # Create a transiently memoized function
    @cached()
    def expensive_function(x, y, z):
        print("x = {0}, y = {1}, z = {2}".format(x, y, z))
        return x + y + z

    # Test transient memoization
    r0 = expensive_function(1, 2, 3)
    r1 = expensive_function(4, 5, 6)
    r2 = expensive_function(1, 2, 3) # Doesn't print any message

Note that the decorator must be called because it takes an optional argument.
This optional argument is also a function, so it is impossible to know whether
or not it has been provided without explicitly invoking the decorator.

The `owls_cache.transient.cached` decorator accepts a single optional argument
named `mapper`.  The `mapper` function receives arguments exactly as they are
provided to the cached function, and thus should probably accept arguments as
`*args` and `**kwargs`, unless you know and enforce the form of calls to the
function.  The purpose of the `mapper` function is to map arguments to a key
that will be associated with the memoizied value.  Any two sets of arguments for
which the `mapper` function generates the same key will refer to the same
memoized value.  The value returned by the `mapper` function must be hashable,
because it will be used as a key in a dictionary.

The default `mapper` function simply generates a tuple of `*args` and
`**kwargs`, and may not be suitable for all cases.  For example, you might want
to make two sets of arguments equivalent in terms of their memoized value, you
may want to ignore certain arguments when memoizing results, or you may need to
modify certain arguments to make them hashable.

The resulting memoized function will take two additional optional keyword
arguments: `cache` and `cache_size`.  Memoized functions may have an arbitrary
number of named in-memory caches associated with them, and they can be
created/selected by name by passing a string for the `cache` argument.  If no
value is passed for the `cache` argument, the default unamed (`''`) cache is
used.  If `None` is passed for the `cache` argument, memoization is disabled for
that function call.  Each cache also has a restricted size, specified by the
`cache_size` argument.  Cache entries are purged on a Least-Recently-Used basis,
with a default cache size of 5.  The cache size is re-evaluated and pruning
performed on every call, so different calls can specify a different `cache_size`
arguments if they like.  A `cache_size` value of `None` lets that cache grow in
an unrestricted fashion.


### Persistent memoization

Persistent memoization is provided by the `owls_cache.persistent.cached`
decorator.  Unlike the transient version, which always stores in-memory by
default, the persistent decorator requires an additional persistent storage
context that specifies the persistent store to use (at least if the decorator is
to have any effect):

    # owls-cache imports
    from owls_cache.persistent import cached
    from owls_cache.persistent import caching_into
    from owls_cache.persistent.caches.fs import FileSystemPersistentCache

    # Create a persistently memoized function
    @cached('example.expensive_function')
    def expensive_function(x, y, z):
        print("x = {0}, y = {1}, z = {2}".format(x, y, z))
        return x + y + z

    # Both calls here will print a message because there is no storage context
    r0 = expensive_function(1, 2, 3)
    r1 = expensive_function(1, 2, 3)

    # Create a persistent store
    fs_cache = FileSystemPersistentCache('/tmp')

    # Test persistent memoization
    with caching_into(fs_cache):
        r2 = expensive_function(1, 2, 3)
        r3 = expensive_function(1, 2, 3) # Doesn't print any message

The persistent storage context is separate from the decorator to allow library
implementations to enable caching without forcing a specific persistent store be
used by end users.  A persistent storage context is created and used by invoking
the `owls_cache.persistent.caching_into` context manager with the persistent
store to use.  This is thread-safe.  The persistent store must be a subclass of
`owls_cache.persistent.caches.PersistentCache`.  Results stored in persistent
stores are generally pickled objects, although this depends on the persistent
store implementation.

Note that the `owls_cache.persistent.cached` decorator also takes a required
`name` argument that specifies the name to use when referring to the function in
the persistent store.  This is necessary because the memoization cache isn't
attached directly to the function object like it is in the transient case.  The
`name` argument must be globally unique (using the fully-qualified function
name, e.g. `package.module.function`, is a good option).

The `owls_cache.persistent.cached` decorator also takes a `mapper` argument that
serves the same purpose as in the transient case.

Two backends are provided by the owls-cache module: on-disk storage and storage
in a [Redis key-value store](http://redis.io/).  Their functionality is detailed
below.

Additionally, custom backends can be easily implemented by subclassing
`owls_cache.persistent.caches.PersistentCache`.    Required methods are
documented in the docstrings of the corresponding module, and examples can be
found in the existing backends.


#### On-disk

On-disk storage is implemented by the
`owls_cache.persistent.caches.fs.FileSystemPersistentCache` store.  Its
constructor takes a single argument: the path to a folder in which results can
be stored in a pickled format.  Keys will be used as file names, and objects
will be pickled into individual files.


#### Redis

Redis storage is implemented by the
`owls_cache.persistent.caches.redis.RedisPersistentCache` store.  It uses the
[`redis` Python module](https://redis-py.readthedocs.org/en/latest/), and its
constructor takes the same arguments as the `redis.StrictRedis` constructor,
with an additional optional argument named `prefix`.  The `prefix` argument
specifies a string that will be used to prefix all keys put into Redis.
