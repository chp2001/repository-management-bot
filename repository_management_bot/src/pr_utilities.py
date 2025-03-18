from repository_management_bot.src.access_gh import get_repo_branch, get_user
from repository_management_bot.src.get_template_details import RepoTemplate
from repository_management_bot.src.includes import *
import subprocess

from repository_management_bot.src.access_gh import get_user, get_user_repos, get_org_repos, get_org_repo, get_user_repo, get_repo, get_repo_branch, get_repo_pulls

from repository_management_bot.src.get_template_details import RepoTemplate, AWI_TEMPLATE_REPO, AWI_ORG_NAME
from repository_management_bot.src.repo_detail import get_repo_structure, RepoStructureType

TEMPLATE = RepoTemplate()
CLONE_DIR = Path("clones")

if not CLONE_DIR.exists():
    CLONE_DIR.mkdir()


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


def count_diff(structure: RepoStructureType)->int:
    count = 0
    for name, content in structure.items():
        if isinstance(content, ContentFile):
            count += 1
        else:
            count += count_diff(content)
    return count


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

    missing = count_diff(result)
    if missing == 0:
        return False, None
    return True, result


def check_branch_diff(repo: Repository, branch: str, template: RepoTemplate = TEMPLATE)->Tuple[bool, Optional[RepoStructureType]]:
    """check_branch_diff
    Check if pieces of the template repo are missing from the target repo branch.
    If so, return the missing pieces.

    Args:
        repo (Repository): the target repo
        branch (str): the branch to check
    Returns:
        result_tup (Tuple[bool, Optional[RepoStructureType]]):  (missing, missing_structure)
    """
    result = template.compare_branch(repo, branch)

    missing = count_diff(result)
    if missing == 0:
        return False, None
    return True, result


def check_pr_diff(pr: PullRequest, template: RepoTemplate = TEMPLATE)->Tuple[bool, Optional[RepoStructureType]]:
    """check_pr_diff
    Check if pieces of the template repo are missing from the target PR.
    If so, return the missing pieces.

    Args:
        pr (PullRequest): the target PR
    Returns:
        result_tup (Tuple[bool, Optional[RepoStructureType]]):  (missing, missing_structure)
    """
    result = template.compare_pr(pr)

    missing = count_diff(result)
    if missing == 0:
        return False, None
    return True, result


def check_ref_diff(repo: Repository, ref: str, template: RepoTemplate = TEMPLATE)->Tuple[bool, Optional[RepoStructureType]]:
    """check_ref_diff
    Check if pieces of the template repo are missing from the target ref.

    Args:
        repo (Repository): the target repo
        ref (str): the ref to check
    Returns:
        result_tup (Tuple[bool, Optional[RepoStructureType]]):  (missing, missing_structure)
    """
    result = template.compare_ref(repo, ref)

    missing = count_diff(result)
    if missing == 0:
        return False, None
    return True, result


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
    Create a fork of the repo for use in a PR

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


def make_pr_branch(repo: Repository, branch_name: str)->Optional[Branch]:
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
        confirm = input(f"User lacks push permissions. Create a personal fork? (y/N): ")
        if confirm.lower() == "y":
            target_loc = make_pr_fork(repo)
        else:
            return None
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

def flatten_pr_diff(diff: RepoStructureType)->Dict[str, ContentFile]:
    """flatten_pr_diff
    Instead of getting changes only when creating the commit, pre-calculate the changes dictionary
    
    Args:
        diff (RepoStructureType): the diff
    Returns:
        changes (Dict[str, ContentFile]): the changes
    """
    changes = {}
    for name, content in diff.items():
        if isinstance(content, ContentFile):
            changes[name] = content
        else:
            changes.update(flatten_pr_diff(content))
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
    if not branch:
        return {}
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
    # prs = get_repo_pulls(target_repo)
    # for pr in prs:
    #     if pr.head.ref == PR_branch.name:
    #         pr.edit(title=PR_title, body=PR_body)
    #         return pr
    pr = target_repo.create_pull(title=PR_title, body=PR_body, head=f"{PR_repository.owner.login}:{PR_branch.name}", base=target_repo.default_branch)
    return pr


def check_template_compliance_for_repo(repo: Repository, template: RepoTemplate = TEMPLATE) -> Tuple[bool, Optional[RepoStructureType]]:
    """check_template_compliance_for_repo
    Check if the repo is compliant with the template

    Args:
        repo (Repository): the target repo
    Returns:
        missing (bool): whether the repo is missing files
        result (Optional[RepoStructureType]): the missing files
    """
    missing, result = check_diff(repo, template)
    return missing, result


def check_branch_exists(repo: Repository, branch_name: str) -> bool:
    """check_branch_exists
    Preemptively check if the branch exists before creating it

    Args:
        repo (Repository): the target repo
        branch_name (str): the name of the branch
    Returns:
        exists (bool): whether the branch exists
    """
    try:
        branch = get_repo_branch(repo, branch_name)
        return branch is not None
    except:
        return False


def check_pr_exists(repo: Repository, branch_name: str) -> bool:
    """check_pr_exists
    Preemptively check if the PR exists before creating it

    Args:
        repo (Repository): the target repo
        branch_name (str): the name of the branch
    Returns:
        exists (bool): whether the PR exists
    """
    prs = get_repo_pulls(repo)
    for pr in prs:
        if pr.head.ref == branch_name:
            return True
    return False


@cache
def get_prs_with_branch(repo: Repository, branch_name: str) -> List[PullRequest]:
    """get_pr_with_branch

    Args:
        repo (Repository): the target repo
        branch_name (str): the name of the branch
    Returns:
        pr (Optional[PullRequest]): the PR
    """
    prs = get_repo_pulls(repo)
    result = []
    for pr in prs:
        if pr.head.ref == branch_name:
            result.append(pr)
    return result


def get_pr_with_user_and_branch(repo: Repository, user: str, branch_name: str) -> Optional[PullRequest]:
    """get_pr_with_user_and_branch

    Args:
        repo (Repository): the target repo
        user (str): the user
        branch_name (str): the name of the branch
    Returns:
        pr (Optional[PullRequest]): the PR
    """
    prs = get_prs_with_branch(repo, branch_name)
    for pr in prs:
        if pr.user.login == user:
            return pr
    return None