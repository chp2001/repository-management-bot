from __future__ import annotations
import os, sys, json, pickle
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from src.includes import *

from src.access_gh import get_repo_dir, get_repo

RepoStructureType = Dict[str, Union[ContentFile, "RepoStructureType"]]


def get_repo_structure(repo: Repository, path: str = "", file_registerer: Optional[Callable[[ContentFile, str], None]] = None)->RepoStructureType:
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

def get_branch_structure(repo: Repository, branch: str, path: str = "", file_registerer: Optional[Callable[[ContentFile, str], None]] = None)->RepoStructureType:
    repo_branch = repo.get_branch(branch)
    repo_dir = get_repo_dir(repo, path, ref=repo_branch.commit.sha)
    repo_structure = {}
    for content in repo_dir:
        if content.type == "dir":
            repo_structure[content.name] = get_branch_structure(repo, branch, content.path)
        else:
            repo_structure[content.name] = content
            if file_registerer:
                file_registerer(content, path)
    return repo_structure

def get_ref_structure(repo: Repository, ref: str, path: str = "", file_registerer: Optional[Callable[[ContentFile, str], None]] = None)->RepoStructureType:
    repo_dir = get_repo_dir(repo, path, ref=ref)
    repo_structure = {}
    for content in repo_dir:
        if content.type == "dir":
            repo_structure[content.name] = get_ref_structure(repo, ref, content.path)
        else:
            repo_structure[content.name] = content
            if file_registerer:
                file_registerer(content, path)
    return repo_structure

def get_pr_structure(pr: PullRequest, file_registerer: Optional[Callable[[ContentFile, str], None]] = None)->RepoStructureType:
    repo = pr.base.repo
    ref = pr.head.sha
    return get_ref_structure(repo, ref, file_registerer=file_registerer)
    
if __name__ == "__main__":
    username = "chp2001"
    example_repo = "network_decomposition_analysis" # should be public, has 3 branches
    repo = get_repo(f"{username}/{example_repo}")
    structure = get_repo_structure(repo)
    print(structure)
    
    branches = repo.get_branches()
    for branch in branches:
        structure = get_branch_structure(repo, branch.name)
        print(branch.name)
        print(structure)
        print()