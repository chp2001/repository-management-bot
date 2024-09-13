from typing import List, Tuple, Dict, Set, Any, Union, Callable, Literal, Optional, TypeVar
import os, sys, json, pickle
from pathlib import Path

if sys.version_info >= (3, 10):
    from typing import ParamSpec, Concatenate
else:
    from typing_extensions import ParamSpec, Concatenate
    
from functools import wraps

"""
adv_wrap.py
The purpose of this module is to create an interface with the type hinting and annotation
machinery of Python, to allow for wrapped functions to maintain their type hints and annotations.
"""

ParamType = ParamSpec("ParamType")
ReturnType = TypeVar("ReturnType")

def wrapper_gen(wrapper: Callable[[Callable], Callable])->Callable[[Callable[ParamType, ReturnType]], Callable[ParamType, ReturnType]]:
    """wrapper_gen
    This function takes a wrapper function, and returns a modified version that is correctly typed.
    """
    _Param = ParamSpec("_Param")
    _Return = TypeVar("_Return")
    def typed_wrapper(func: Callable[_Param, _Return])->Callable[_Param, _Return]:
        wrapped_func = wrapper(func)
        @wraps(func)
        def wrapped(*args: _Param.args, **kwargs: _Param.kwargs)->_Return:
            return wrapped_func(*args, **kwargs)
        return wrapped
    return typed_wrapper

if __name__ == "__main__":
    # test the wrapper_gen function
    
    @wrapper_gen
    def wrap1(func: Callable)->Callable:
        @wraps(func)
        def inner(*args, **kwargs):
            print("wrap1")
            return func(*args, **kwargs)
        return inner
    
    @wrap1
    def test1(a: int, b: int)->int:
        return a + b
    
    print(test1(1, 2))
    # reveal_type(test1)

