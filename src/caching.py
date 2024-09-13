import os, sys, json, pickle
from pathlib import Path
from typing import List, Tuple, Dict, Set, Any, Union, Callable, Literal, Optional, TypeVar
from functools import wraps
from adv_wrap import wrapper_gen
import warnings
import inspect
src = Path(__file__).parent # src
ghcache = src.parent / "ghcache"

"""
caching.py
The purpose of this module is to provide a simple caching mechanism for the Github API,
to avoid unnecessary requests and reduce the impact of the rate limit.
"""

cache_hits = 0
cache_misses = 0
cache_near_misses = 0
cache_requests = 0

class CacheManager:
    func_name: str
    storage_method: Literal["file", "dir"]
    cache_path: Path # file or directory
    # dir mode only
    keytable: Path # file that maps keys to files
    keymap: List[List[str]] # for each file, list of keys
    subfiles: List[str] # list of files in the directory
    # both modes
    data: Dict[str, Any] # key -> data
    size_threshold: int = 1 * 10**6 # 1 MB
    size: int
    def file_load(self):
        if not self.cache_path.exists():
            self.data = {}
            self.file_save()
            return
        with open(self.cache_path, "rb") as f:
            self.data = pickle.load(f)
    def file_save(self):
        with open(self.cache_path, "wb") as f:
            pickle.dump(self.data, f)
    def dir_load(self):
        self.keymap = pickle.load(self.keytable.open("rb"))
        self.subfiles = [f.name for f in self.cache_path.iterdir() if f.is_file() and f.name != self.keytable.name]
        self.data = {}
    def dir_subfile_load(self, index: int):
        subdata = pickle.load(file=(self.cache_path / self.subfiles[index]).open("rb"))
        self.data.update(subdata)
    def dir_subfile_save(self, index: int, keys: List[str]):
        subdata = {k: self.data[k] for k in keys}
        with open(self.cache_path / self.subfiles[index], "wb") as f:
            pickle.dump(subdata, f)
    def dir_load_all(self):
        for i in range(len(self.subfiles)):
            self.dir_subfile_load(i)
    def dir_key_index(self, key: str)->Optional[int]:
        for i, keys in enumerate(self.keymap):
            if key in keys:
                return i
        return None
    def save_keytable(self):
        with open(self.keytable, "wb") as f:
            pickle.dump(self.keymap, f)
    def distribute_all_keys(self)->List[List[str]]:
        keylists = []
        curlist = []
        size = 0
        for key, datum in self.data.items():
            keysize = len(key) + len(pickle.dumps(datum))
            if size + keysize > self.size_threshold:
                keylists.append(curlist)
                curlist = []
                size = 0
            curlist.append(key)
            size += keysize
        if curlist:
            keylists.append(curlist)
        return keylists
    def redistribute(self):
        self.dir_load_all()
        keylists = self.distribute_all_keys()
        for i in range(len(self.subfiles)):
            self.dir_subfile_save(i, keylists[i])
        self.keymap = keylists
        self.save_keytable()
    def dir_add_key(self, key: str, datum: Any):
        curfile = len(self.subfiles) - 1
        curfilesize = (self.cache_path / self.subfiles[curfile]).stat().st_size
        self.data[key] = datum
        if curfilesize + len(key) + len(pickle.dumps(datum)) > self.size_threshold:
            curfile += 1
            self.keymap.append([key])
            self.subfiles.append(f"{curfile}.pkl")
            self.dir_subfile_save(curfile, self.keymap[curfile])
        else:
            self.keymap[curfile].append(key)
            self.dir_subfile_save(curfile, self.keymap[curfile])
        self.save_keytable()
    def dir_set_key(self, key: str, datum: Any):
        index = self.dir_key_index(key)
        if index is not None:
            self.data[key] = datum
            self.dir_subfile_save(index, self.keymap[index])
            self.save_keytable()
        else:
            self.dir_add_key(key, datum)
    def manage_size(self):
        if self.storage_method == "file":
            if self.size > self.size_threshold:
                self.storage_method = "dir"
                new_cache_path = ghcache / self.func_name
                new_cache_path.mkdir()
                self.keytable = new_cache_path / "keytable.pkl"
                self.keymap = []
                self.subfiles = []
                self.save_keytable()
                self.redistribute()
                self.cache_path.unlink()
                self.cache_path = new_cache_path
        elif self.storage_method == "dir":
            pass
    def __init__(self, func_name: str, storage_method: Literal["file", "dir"] = "file"):
        self.func_name = func_name
        self.storage_method = storage_method
        self.cache_path = ghcache / func_name
        if storage_method == "file":
            self.cache_path = self.cache_path.with_suffix(".pkl")
            self.file_load()
            if not self.cache_path.exists():
                self.cache_path.touch()
                self.data = {}
            self.size = self.cache_path.stat().st_size
            self.manage_size()
        elif storage_method == "dir":
            self.keytable = self.cache_path / "keytable.pkl"
            self.dir_load()
        self.size = self.cache_path.stat().st_size
    def __contains__(self, key: str)->bool:
        if key in self.data:
            return True
        elif self.storage_method == "dir":
            index = self.dir_key_index(key)
            return index is not None
        else:
            return False
    def __getitem__(self, key: str)->Any:
        global cache_hits, cache_misses, cache_near_misses, cache_requests
        cache_requests += 1
        if key in self.data:
            cache_hits += 1
            return self.data[key]
        elif self.storage_method == "dir":
            index = self.dir_key_index(key)
            if index is not None:
                cache_near_misses += 1
                self.dir_subfile_load(index)
                return self.data[key]
            else:
                cache_misses += 1
                return None
        else:
            cache_misses += 1
            return None
    def __setitem__(self, key: str, datum: Any):
        if key in self.data:
            return
        if self.storage_method == "file":
            self.data[key] = datum
            self.file_save()
            self.size = self.cache_path.stat().st_size
            self.manage_size()
        elif self.storage_method == "dir":
            self.dir_set_key(key, datum)
        else:
            return
    def clear(self):
        warnings.warn(f"Clearing cache for {self.func_name}")
        if self.storage_method == "dir":
            for subfile in self.subfiles:
                (self.cache_path / subfile).unlink()
            self.keytable.unlink()
            self.cache_path.rmdir()
            self.cache_path = ghcache / (self.func_name + ".pkl")
        self.data = {}
        self.size = 0
        self.file_save()
        
class FreshnessManager:
    """
    FreshnessManager
    This class is used to manage the freshness of the cache.
    A cache from a function is fresh only if the data was created with the up-to-date version of the code.
    """
    impl_path: Path
    "Location that we store implementation data"
    info_path: Path
    "Location that we store human-readable information"
    impl_data: Dict[str, Any]
    "Loaded implementation data"
    managed_functions: Set[str]
    "Functions currently managed by the FreshnessManager"
    def __init__(self):
        self.impl_path = ghcache / "freshness.pkl"
        self.info_path = ghcache / "freshness_info.json"
        self.managed_functions = set()
        if self.impl_path.exists():
            with open(self.impl_path, "rb") as f:
                self.impl_data = pickle.load(f)
            self.managed_functions.update(self.impl_data.keys())
        else:
            self.impl_data = {}
        self.save()
            
    def save(self):
        with open(self.impl_path, "wb") as f:
            pickle.dump(self.impl_data, f)
        with open(self.info_path, "w") as f:
            json.dump({"managed_functions": list(self.managed_functions)}, f)
    
    def manage_function(self, func: Callable):
        func_name = func.__name__
        if func_name not in self.managed_functions:
            self.managed_functions.add(func_name)
            self.impl_data[func_name] = inspect.getsource(func)
            self.save()
            
    def check_freshness(self, func: Callable)->bool:
        func_name = func.__name__
        if func_name not in self.managed_functions:
            return False
        newsrc = inspect.getsource(func)
        oldsrc = self.impl_data[func_name]
        if newsrc != oldsrc:
            # print(f"Function {func_name} is not fresh: {newsrc} != {oldsrc}")
            self.impl_data[func_name] = newsrc
            self.save()
            return False
        return True
    
    def __contains__(self, func: Callable)->bool:
        return func.__name__ in self.managed_functions
    def __getitem__(self, func: Callable)->bool:
        return self.check_freshness(func)
    def __setitem__(self, func: Callable, value: bool):
        raise Exception("FreshnessManager is read-only")
    def __delitem__(self, func: Callable):
        raise Exception("FreshnessManager is read-only")
    
class FunctionCacheManager:
    freshness_manager: FreshnessManager
    caches: Dict[str, CacheManager]
    def __init__(self):
        self.freshness_manager = FreshnessManager()
        self.caches = {}
    def register_function(self, func: Callable):
        self.freshness_manager.manage_function(func)
        self.get_cache(func)
    def get_cache(self, func: Callable)->CacheManager:
        func_name = func.__name__
        if func_name not in self.caches:
            cache = CacheManager(func_name)
        else:
            cache = self.caches[func_name]
        if func not in self.freshness_manager:
            # If the function is not managed, manage it
            self.freshness_manager.manage_function(func)
        elif not self.freshness_manager[func]:
            # If the function is already managed, but not fresh, clear the cache
            cache.clear()
        self.caches[func_name] = cache
        return cache
    def __getitem__(self, func: Callable)->CacheManager:
        return self.get_cache(func)
    def __contains__(self, func: Callable)->bool:
        return func.__name__ in self.caches

CACHES: FunctionCacheManager = FunctionCacheManager()


# type coherent cache decorator
args = TypeVar("args")
result = TypeVar("result")
@wrapper_gen
def cache(func: Callable[..., result])->Callable[..., result]:
    if func not in CACHES:
        CACHES.freshness_manager.manage_function(func)
    @wraps(func)
    def wrapper(*args, **kwargs)->result:
        cache = CACHES[func]
        try:
            key = json.dumps((args, kwargs))
        except TypeError:
            key = str((args, kwargs))
        if key in cache:
            return cache[key]
        else:
            result = func(*args, **kwargs)
            cache[key] = result
            return result
    return wrapper

def cache_stats():
    global cache_hits, cache_misses, cache_near_misses, cache_requests
    print(f"Cache hits: {cache_hits}")
    print(f"Cache misses: {cache_misses}")
    print(f"Cache near misses: {cache_near_misses}")
    print(f"Cache requests: {cache_requests}")


if __name__ == "__main__":
    @cache
    def test_decorable(a: int, b: int)->int:
        return a + b
    
    val = 0
    val2 = 0
    for i in range(10):
        val = test_decorable(val, i)
        val2 = val2 + i
        assert val == val2
    print("Test passed.")