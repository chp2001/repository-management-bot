import os, sys, json, pickle
from pathlib import Path
from typing import List, Tuple, Dict, Set, Any, Union, Callable, Literal, Optional, TypeVar
from functools import wraps, cache as functools_cache
from adv_wrap import wrapper_gen

cache = wrapper_gen(functools_cache)
cache_stats = lambda: None