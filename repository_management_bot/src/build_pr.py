from .includes import *
import subprocess

def check_output(cmd: str, **kwargs)->str:
    try:
        kwargs["shell"] = True
        kwargs["stderr"] = subprocess.PIPE
        kwargs["text"] = True
        result = subprocess.check_output(cmd, **kwargs)
        if isinstance(result, bytes):
            return result.decode("utf-8")
        return result
    except subprocess.CalledProcessError as e:
        result = e.output
        if isinstance(result, bytes):
            return result.decode("utf-8")
        return result
    
from .access_gh import get_user, get_org, get_org_repos, get_org_repo, get_user_repo

from .get_template_details import RepoTemplate, AWI_TEMPLATE_REPO, AWI_ORG_NAME
from .repo_detail import get_repo_structure, RepoStructureType

TEMPLATE = RepoTemplate(AWI_ORG_NAME, AWI_TEMPLATE_REPO)
CLONE_DIR = Path("clones")

if not CLONE_DIR.exists():
    CLONE_DIR.mkdir()
    
@cache
def check_diff(repo: Repository, template: RepoTemplate = TEMPLATE)->Tuple[bool, Optional[RepoStructureType]]:
    """check_diff
    Check if pieces of the template repo are missing from the target repo.
    If so, return the missing pieces.
    
    Args:
        repo (Repository): the target repo
    Returns:
        result_tup (Tuple[bool, Optional[RepoStructureType]]):  (missing, missing_structure)
    """
    result = template.compare_repo(repo)
    # print(result) 
    def count_diff(structure: RepoStructureType)->int:
        count = 0
        for name, content in structure.items():
            if isinstance(content, ContentFile):
                count += 1
            else:
                count += count_diff(content)
        return count
    missing = count_diff(result)
    if missing == 0:
        return False, None
    return True, result
    
# Prepare to submit a PR
# 1. Check if the repo is missing any files
# 2. If we have permission to create a branch, create a branch
# 2.1. Else, create a fork and a branch on the fork
# 3. Create the missing files
# 4. Commit the changes to the branch
# 5. Create a PR
# 6. Done

@cache
def get_repo_permissions(repo: Repository)->Dict[str, bool]:
    """get_repo_permissions
    Get the permissions for the authenticated user on the repo.
    
    Args:
        repo (Repository): the target repo
    Returns:
        permissions (Dict[str, bool]): the permissions for the authenticated user
    """
    user = get_user()
    results = {}
    # Check if the user has push access
    result = check_output(f"gh api repos/{repo.full_name}/collaborators/{user.login}/permission", shell=True)
    try:
        response = json.loads(result)
        status = int(response["status"]) if "status" in response else 0
        if status == 403:
            results["push"] = False
        elif status == 200:
            results["push"] = True
        elif "user" in response:
            if "permissions" in response["user"]:
                results.update(response["user"]["permissions"])
        else:
            raise
    except Exception as e:
        results["push"] = False
        warnings.warn(f"Unexpected response from GitHub API: {result}, {e}")
    if "push" not in results:
        results["push"] = False
    if "read" not in results:
        # Check if the user has read access
        result = os.popen(f"git ls-remote {repo.clone_url}").read()
        results["read"] = len(result) > 0
    return results

def clone_tip(repo: Repository, branch: Branch)->Path:
    """clone_tip
    Clone the tip (Bare minimum objects) of the repo to the specified path

    Args:
        repo (Repository): the target repo
        branch (Branch): the branch to clone
    Returns:
        clone_path (Path): the path to the cloned repo
    """
    clone_path = CLONE_DIR / repo.full_name
    if clone_path.exists():
        return clone_path
    os.system(f"git clone --depth 1 --branch {branch.name} {repo.clone_url} {clone_path}")
    return clone_path

def add_file_to_tip(repo: Repository, branch: Branch, content: ContentFile)->Path:
    """add_file_to_tip
    Add a file to the tip of the repo
    
    Args:
        repo (Repository): the target repo
        branch (Branch): the branch to add the file to
        content (ContentFile): the file to add
    Returns:
        path (Path): the path to the added file
    """
    clone_path = clone_tip(repo, branch)
    file_path = clone_path / content.path
    if file_path.exists():
        fprint(f"File already exists: {file_path}")
        return clone_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content.decoded_content)
    return file_path

def push_changes_to_tip(repo: Repository, branch: Branch, commit_message: str)->Path:
    """push_changes_to_tip
    Push the changes to the tip of the repo
    
    Args:
        repo (Repository): the target repo
        branch (Branch): the branch to push to
        commit_message (str): the commit message
    Returns:
        clone_path (Path): the path to the cloned repo
    """
    clone_path = clone_tip(repo, branch)
    result = check_output(f"cd {clone_path} && git add . && git commit -m '{commit_message}' && git push origin {branch.name}")
    return clone_path

def clean_tip(repo: Repository)->Path:
    """clean_tip
    Clean the tip of the repo
    
    Args:
        repo (Repository): the target repo
    Returns:
        clone_path (Path): the path to the cloned repo
    """
    clone_path = CLONE_DIR / repo.full_name
    if not clone_path.exists():
        return clone_path
    result = check_output(f"rm -rf {clone_path}")
    return clone_path

def make_pr_fork(repo: Repository)->Repository:
    """make_pr_fork
    Create a fork of the repo
    
    Args:
        repo (Repository): the target repo
    Returns:
        fork (str): the name of the fork
    """
    # Check if the fork already exists
    user = get_user()
    try:
        fork = user.get_repo(repo.full_name)
        if fork is not None:
            return fork
    except:
        pass
    # Create the fork
    fork = repo.create_fork()
    return fork
    

def make_pr_branch(repo: Repository, branch_name: str)->Branch:
    """make_pr_branch
    Create a branch on the repo
    
    Args:
        repo (Repository): the target repo
        branch_name (str): the name of the branch
    Returns:
        branch (Branch): the branch that was created
    """
    perms = get_repo_permissions(repo)
    default_branch = repo.get_branch(repo.default_branch)
    default_sha = default_branch.commit.sha
    target_loc = repo
    if not perms["push"]:
        target_loc = make_pr_fork(repo)
    try:
        branch = target_loc.get_branch(branch_name)
        if branch is not None:
            return branch
    except:
        pass
    result = target_loc.create_git_ref(f"refs/heads/{branch_name}", default_sha)
    branch = target_loc.get_branch(branch_name)
    return branch

def make_pr_commit(repo: Repository, branch: Branch, structure: RepoStructureType, changes: Dict[str, ContentFile] = {}) -> Dict[str, ContentFile]:
    """make_pr_commit
    Create a commit on the branch that adds the structure to the repo
    
    Args:
        repo (Repository): the target repo
        branch (Branch): the branch to commit to
        structure (RepoStructureType): the structure to commit
        changes (Dict[str, str]): the changes that were made
    Returns:
        changes (Dict[str, str]): the changes that were made
    """
    for name, content in structure.items():
        if isinstance(content, ContentFile):
            add_file_to_tip(repo, branch, content)
            changes[name] = content
        else:
            make_pr_commit(repo, branch, content, changes)
    return changes

def prep_pr_commit(repo: Repository, branch_name: str, template: RepoTemplate = TEMPLATE)->Dict[str, ContentFile]:
    """prep_pr_commit
    Prepare to submit a PR
    
    Args:
        repo (Repository): the target repo
        branch_name (str): the name of the branch
    Returns:
        changes (Dict[str, str]): the changes that were made
    """
    missing, structure = check_diff(repo, template=template)
    if not structure:
        return {}
    branch = make_pr_branch(repo, branch_name)
    changes = make_pr_commit(repo, branch, structure)
    return changes

def push_pr_commit(repo: Repository, branch_name: str, commit_message: str):
    """push_pr_commit
    Push the commit to the repo
    
    Args:
        repo (Repository): the target repo
        branch_name (str): the name of the branch
        commit_message (str): the commit message
    """
    branch = repo.get_branch(branch_name)
    push_changes_to_tip(repo, branch, commit_message)
    return

def make_pr(target_repo: Repository, PR_repository: Repository, PR_branch: Branch, PR_title: str, PR_body: str):
    """make_pr
    Create a PR
    
    Args:
        target_repo (Repository): the target repo
        PR_repository (Repository): the repo to create the PR from
        PR_branch (Branch): the branch to create the PR from
        PR_title (str): the title of the PR
        PR_body (str): the body of the PR
    """
    # check if the PR already exists
    prs = target_repo.get_pulls()
    for pr in prs:
        if pr.head.ref == PR_branch.name:
            pr.edit(title=PR_title, body=PR_body)
            return pr
    pr = target_repo.create_pull(title=PR_title, body=PR_body, head=f"{PR_repository.owner.login}:{PR_branch.name}", base=target_repo.default_branch)
    return pr

def template_compliance_pr(repo: Repository, template: RepoTemplate = TEMPLATE):
    """template_compliance_pr
    Create a PR to make the repo compliant with the template
    
    Args:
        repo (Repository): the target repo
    """
    repo_permissions = get_repo_permissions(repo)
    PR_repo = repo if repo_permissions["push"] else make_pr_fork(repo)
    branch_name = "repository_management_bot/template_compliance"
    commit_msg = "Add missing files to make repo compliant with template"
    pullreq_title = "Enforce Template Compliance"
    template_repository_addr = template.template_repo.html_url
    organization_name = template.template_repo.owner.login
    organization_link = f"[{organization_name}]({template.template_repo.owner.html_url})"
    template_repo_link = f"[{template.template_repo.name}]({template_repository_addr})"
    target_repo_name = repo.full_name
    pullreq_body = f"This PR adds missing files to make the `{target_repo_name}` repository compliant with the {organization_link}'s {template_repo_link} template."
    changes = prep_pr_commit(PR_repo, branch_name)
    if len(changes) == 0:
        return
    pullreq_body += "\n\nChanges made:\n"
    repo_link = repo.html_url
    branch_link = f"{repo_link}/tree/{branch_name}"
    for name, content in changes.items():
        content_link = f"{branch_link}/{content.path}"
        pullreq_body += f" - Added [{name}]({content_link})\n"  
    pullreq_body += "\nThis PR was automatically generated by the [Repository Management Bot](https://github.com/chp2001/repository-management-bot)."
    push_pr_commit(PR_repo, branch_name, commit_msg)
    make_pr(repo, PR_repo, PR_repo.get_branch(branch_name), pullreq_title, pullreq_body)
    clean_tip(repo)
    return

def template_compliance_prs(org: str, template_repo: str):
    """template_compliance_prs
    Create PRs to make all the repos in the organization compliant with the template
    
    Args:
        org (str): the organization
        template_repo (str): the template repo
    """
    repos = get_org_repos(org)
    template = RepoTemplate(org, template_repo)
    for repo in repos:
        missing, result = check_diff(repo, template)
        if not missing:
            continue
        userinput = input(f"{repo.full_name} is missing:\n{result}\nCreate PR? (y/N): ")
        if userinput.lower() == "y":
            template_compliance_pr(repo, template)
            print(f"PR created for {repo.full_name}")
        elif userinput.lower() in ["q", "quit", "exit"]:
            print("Exiting")
            break
        else:
            print(f"Skipping {repo.full_name}")
    return
    
if __name__ == "__main__":
    def test_permissions():
        # Get the 'bmi_rainrate' repo
        repo = get_org_repo(AWI_ORG_NAME, "bmi_rainrate")
        perms = get_repo_permissions(repo)
        fprint(perms)
    # test_permissions()
    
    def test_pr_commit_prep():
        repo = get_user_repo("load_factorio_data")
        missing, structure = check_diff(repo)
        fprint(missing, structure)
        if not structure:
            return
        branch = make_pr_branch(repo, "test-branch")
        fprint(branch)
        fprint(missing, structure)
        make_pr_commit(repo, branch, structure)
        # remove branch
        os.system(f"cd {CLONE_DIR / repo.full_name} && git branch -D test-branch")
        clean_tip(repo)
        
        
    # test_pr_commit_prep()
    
    def test_full_pr():
        repo = get_user_repo("load_factorio_data")
        template_compliance_pr(repo)
        
    # test_full_pr()
    
    def test_template_compliance_prs():
        template_compliance_prs(AWI_ORG_NAME, AWI_TEMPLATE_REPO)
        
    # test_template_compliance_prs()