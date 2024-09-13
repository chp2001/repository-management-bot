from build_pr import template_compliance_prs

if __name__ == "__main__":
    org = "AlabamaWaterInstitute"
    repo = "awi-open-source-project-template"
    # This is the main entry point for the program
    # It will list repositories in the {org} organization, and what files are missing from each repository
    # It will query the user for which repositories to create PRs for, and then create the PRs
    # 
    # The repository assumes that the user has the GitHub CLI installed and authenticated (gh auth login),
    # and uses their account to create the PRs
    template_compliance_prs(org, repo)