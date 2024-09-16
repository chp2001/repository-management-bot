from __future__ import annotations
from includes import *

from access_gh import get_repo_dir

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