from github.NamedUser import NamedUser
from github.AuthenticatedUser import AuthenticatedUser
from github.Organization import Organization
from github.Repository import Repository
from github.Branch import Branch
from github.ContentFile import ContentFile
from github.PullRequest import PullRequest
from typing import List, Tuple, Dict, Set, Any, Union, Callable, Literal, Optional, TypeVar
import os, sys, json
from pathlib import Path
from repository_management_bot.src.caching import cache, cache_stats
import warnings
User = Union[NamedUser, AuthenticatedUser]

customtab = "    "
def fprint(*args, **kwargs):
    _args = []
    for arg in args:
        if isinstance(arg, str):
            _args.append(arg.replace("\t", customtab))
        else:
            _args.append(arg)
    args = _args
    for k, v in kwargs.items():
        if isinstance(v, str):
            kwargs[k] = v.replace("\t", customtab)
    print(*args, file=sys.stderr, **kwargs)
    
this_repo = "repository_management_bot"
this_repo_author = "chp2001"
this_repo_path = f"{this_repo_author}/{this_repo}"
this_repo_link = f"https://www.github.com/{this_repo_path}"