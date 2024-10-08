from .includes import *
from github import Github

@cache
def get_auth()->str:
    # Query gh for the token
    cmd = "gh auth token"
    token = os.popen(cmd).read().strip()
    return token

@cache
def get_Github()->Github:
    token = get_auth()
    return Github(token)

@cache
def get_user(name: Optional[str] = None)->User:
    if name is None:
        return get_Github().get_user()
    return get_Github().get_user(name)

@cache
def get_org(org: str)->Organization:
    return get_Github().get_organization(org)

@cache
def get_user_orgs(name: Optional[str] = None)->List[Organization]:
    return list(get_user(name).get_orgs())

@cache
def get_user_repos(name: Optional[str] = None)->List[Repository]:
    return list(get_user(name).get_repos())

@cache
def get_user_repo(repo: str, user: Optional[str] = None)->Repository:
    return get_user(user).get_repo(repo)

@cache
def get_org_repos(org: str)->List[Repository]:
    return list(get_Github().get_organization(org).get_repos())

@cache
def get_org_repo(org: str, repo: str)->Repository:
    return get_Github().get_organization(org).get_repo(repo)

@cache
def get_repo(repo: str)->Repository:
    """get_repo
    Get a repository by name
    
    args:
        repo: str - the path to the repository, in the form "org/repo" or "user/repo"
    returns:
        Repository - the repository object
    """
    if not "/" in repo:
        raise ValueError(f"Invalid repo name {repo}")
    owner, name = repo.split("/")
    gh = get_Github()
    try:
        user = gh.get_user(owner)
        return user.get_repo(name)
    except:
        org = gh.get_organization(owner)
        return org.get_repo(name)

@cache
def get_org_members(org: str)->List[NamedUser]:
    return list(get_Github().get_organization(org).get_members())

@cache
def get_repo_branches(repo: Repository)->List[Branch]:
    return list(repo.get_branches())

@cache
def get_repo_main_branch(repo: Repository)->Branch:
    return repo.get_branch(repo.default_branch)

@cache
def get_repo_main_dir(repo: Repository)->List[ContentFile]:
    return get_repo_dir(repo, "")
@cache
def contentfile_isdir(cf: ContentFile)->bool:
    return cf.type == "dir"
@cache
def contentfile_isfile(cf: ContentFile)->bool:
    return cf.type == "file"
@cache
def get_repo_dir(repo: Repository, dir: str)->List[ContentFile]:
    content = repo.get_contents(dir)
    if isinstance(content, ContentFile):
        return [content]
    else:
        return content
@cache
def get_repo_file(repo: Repository, file: str)->ContentFile:
    content = repo.get_contents(file)
    if isinstance(content, ContentFile):
        return content
    else:
        raise ValueError(f"{file} is not a file")

if __name__ == "__main__":
    def quicklook_t(obj: type[object]):
        print(obj.__name__)
        for k, v in obj.__dict__.items():
            vstr = str(v)
            if len(vstr) < 100:
                fprint("\t" + k, v)
            else:
                fprint("\t" + k, vstr[:100] + " ...")
    def quicklook(obj: object):
        for k, v in obj.__dict__.items():
            if k.startswith("_"):
                continue
            vstr = str(v)
            
            if len(vstr) < 100:
                fprint("\t" + k, v)
            else:
                fprint("\t" + k, vstr[:100] + " ...")
                
    user = get_user()
    fprint(f"User: {user.login}")
    quicklook(user)
    fprint("Orgs:")
    awi = None
    for org in get_user_orgs():
        fprint(f"\t{org.login}")
        if "Alabama" in org.login:
            awi = org
            print(f"(awi is {awi.login})")
    fprint("awi-open-source-project-template")
    if awi is None:
        raise ValueError("awi is None")
    template_repo = get_org_repo(awi.login, "awi-open-source-project-template")
    print(template_repo, template_repo.name)
    contentfiles = get_repo_main_dir(template_repo)
    for cf in contentfiles:
        fprint(cf.name, cf.type)
        if cf.type == "dir":
            subfiles = get_repo_dir(template_repo, cf.name)
            for sf in subfiles:
                fprint("\t", sf.name, sf.type)
    cache_stats()