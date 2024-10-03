# Install

## Dependencies

There is essentially no setup required for this project beyond the dependencies. The dependencies are:

1. Python 3.8+ (Ideally 3.10+) (from [here](https://www.python.org/downloads/))
2. PyGithub (from [here](https://pypi.org/project/PyGithub/))

   ```bash
   python -m pip install PyGithub
   ```

3. GitHub CLI (from [here](https://cli.github.com/))
    1. After installing the GitHub CLI, you will need to authenticate with GitHub. This can be done with the following command:

        ```bash
        gh auth login
        ```

    2. You will need to authenticate with a user that has access to the repositories you want to manage.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/chp2001/repository-management-bot.git
    ```

## Usage

The primary entry point is in the [`__main__.py`](repository_management_bot/__main__.py) file. It can be run from the root of the repository with the following command patterns:

```bash
python -m repository_management_bot [organization_name] [template_repository_name]
python -m repository_management_bot -o [organization_name] -r [template_repository_name]
python -m repository_management_bot --org [organization_name] --repo [template_repository_name]
```

If either the organization name or template repository name is not provided, the default values found at the bottom of [`repository_management_bot/cli/arguments.py`](repository_management_bot/cli/arguments.py) will be used.
