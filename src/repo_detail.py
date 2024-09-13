from __future__ import annotations
from github import Github
from github import Auth
from github.NamedUser import NamedUser
from github.AuthenticatedUser import AuthenticatedUser
from github.Organization import Organization
from github.Repository import Repository
from github.Branch import Branch
from github.ContentFile import ContentFile
from github.PullRequest import PullRequest
from github.Issue import Issue
from github.IssueComment import IssueComment
from github.Label import Label
from typing import List, Tuple, Dict, Set, Any, Union, Callable, Literal, Optional, TypeVar
import os, sys, json
from pathlib import Path
# from functools import cache
from caching import cache, cache_stats
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
    
from access_gh import get_Github, get_org_repo, get_repo_dir, get_repo_file

RepoStructureType = Dict[str, Union[ContentFile, "RepoStructureType"]]


def get_repo_structure(repo: Repository, path: str = "", file_registerer: Optional[Callable[[ContentFile, str], None]] = None)->Dict[str, Any]:
    repo_dir = get_repo_dir(repo, path)
    repo_structure = {}
    for content in repo_dir:
        if content.type == "dir":
            repo_structure[content.name] = get_repo_structure(repo, content.path)
        else:
            repo_structure[content.name] = content
            if file_registerer:
                file_registerer(content, path)
    return repo_structure