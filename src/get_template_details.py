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
from repo_detail import get_repo_structure, RepoStructureType

ORG_NAME = "AlabamaWaterInstitute"
TEMPLATE_REPO = "awi-open-source-project-template"

def search_content_list(content_list: List[ContentFile], name: str)->Optional[ContentFile]:
    for content in content_list:
        if content.name == name:
            return content
    return None

@cache
def get_template_details():
    repo = get_org_repo(ORG_NAME, TEMPLATE_REPO)
    repo_dir = get_repo_dir(repo, "")
    repo_file = search_content_list(repo_dir, "README.md")
    return repo, repo_dir, repo_file

class RepoTemplate:
    template_repo: Repository
    template_structure: RepoStructureType
    file_list: List[Path]
    file_prefabs: Dict[str, Dict[str, Any]]
    def __init__(self, org: str, repo_name: str):
        self.template_repo = get_org_repo(org, repo_name)
        self.template_structure = {}
        self.file_list = []
        self.file_prefabs = {}
        self.load_structure()
        
    def get_prefab(self, content_file: ContentFile, path: str)->Dict[str, Any]:
        file_prefab = {}
        file_prefab["name"] = content_file.name
        file_prefab["path"] = path
        file_prefab["size"] = content_file.size
        file_prefab["download_url"] = content_file.download_url
        file_prefab["type"] = content_file.type
        file_prefab["encoding"] = content_file.encoding
        file_prefab["contentFile"] = content_file
        self.file_prefabs[path] = file_prefab
        return file_prefab
        
    def load_structure(self, subdir: str = "", substruct: Optional[RepoStructureType] = None)->RepoStructureType:
        def file_registerer(content: ContentFile, path: str):
            self.file_list.append(Path(path))
            self.get_prefab(content, path)
        self.template_structure = get_repo_structure(self.template_repo, subdir, file_registerer)
        return self.template_structure
    
    def print_structure(self, subtree: Optional[Dict[str, Any]] = None, level: int = 0):
        if subtree is None:
            subtree = self.template_structure
        # fprint("\t"*level, "Structure:")
        if level > 4:
            raise Exception("Structure too deep")
        for name, content in subtree.items():
            if isinstance(content, dict):
                fprint("\t"*level, f"{name}/:")
                self.print_structure(content, level + 1)
            else:
                fprint("\t"*level, f"{name}")
                
    def compare_repo_structure(self, repo: RepoStructureType)->RepoStructureType:
        """compare_repo
        Compare the structure of the template repo to another repo
        Creates and returns a structure of what parts of the template repo are missing in the other repo
        """
        other_structure = repo
        diff_structure = {}
        def recurse_diff(structure1: RepoStructureType, structure2: Optional[RepoStructureType], diff: RepoStructureType):
            """recurse_diff
            Recursively compare the structure of two repos
            """
            def alldiff(name: str):
                loc = structure1[name]
                if isinstance(loc, ContentFile):
                    diff[name] = loc
                else:
                    subdiff = {}
                    recurse_diff(loc, None, subdiff)
                    diff[name] = subdiff
            for name, loc in structure1.items():
                if structure2 is None or name not in structure2:
                    alldiff(name)
                    continue
                loc2 = structure2[name]
                type1 = isinstance(loc, ContentFile)
                type2 = isinstance(loc2, ContentFile)
                if not type1:
                    if type2:
                        alldiff(name)
                        continue
                    subdiff = {}
                    recurse_diff(loc, loc2, subdiff)
                    diff[name] = subdiff
                    continue
                elif not type2:
                    alldiff(name)
                    continue
        recurse_diff(self.template_structure, other_structure, diff_structure)
        if "README.md" not in diff_structure:
            if "doc" in diff_structure:
                del diff_structure["doc"]
        return diff_structure
    
    def compare_repo(self, repo: Repository)->RepoStructureType:
        repo_structure = get_repo_structure(repo)
        return self.compare_repo_structure(repo_structure)

if __name__ == "__main__":
    repo, repo_dir, repo_file = get_template_details()
    fprint(repo, repo_dir, repo_file)
    
    template = RepoTemplate(ORG_NAME, TEMPLATE_REPO)
    template.print_structure()
    cache_stats()