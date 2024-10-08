from .src.build_pr import compliance_pr_dispatch
from .cli.arguments import DefaultArgParse, ProgInfoExp

if __name__ == "__main__":
    proginfo: ProgInfoExp = ProgInfoExp(
        info_type = "explicit",
        program_name = "Repository Management Bot",
        program_description = "A bot to manage repositories and ensure that they are up to date with a template repository",
        program_version = "unversioned prototype",
        program_author = "Chad Perry",
        program_github_link="https://github.com/chp2001/repository-management-bot",
        program_header = None
    )
    DefaultArgParse.add_prog_info(proginfo)
    arg = DefaultArgParse.parse_args()
    org = arg["org"]
    user = arg["user"]
    repo = arg["repo"]
    template = arg["template"]
    # This is the main entry point for the program
    # It will list repositories in the {org} organization, and what files are missing from each repository
    # It will query the user for which repositories to create PRs for, and then create the PRs
    # 
    # The repository assumes that the user has the GitHub CLI installed and authenticated (gh auth login),
    # and uses their account to create the PRs
    compliance_pr_dispatch(user_name=user, org_name=org, repo_name=repo, template_name=template)