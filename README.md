<!-- #### AWI Open Source Project Template Instructions

1. Create a new project, doing one of the following:
   1. When creating the new repository, use this template to initialize it.
   2. Clone this repository and copy the contents to a new repository manually.
2. Update the README, replacing the contents below as prescribed.
3. Add any libraries, assets, or hard dependencies whose source code will be included in the project's repository to [Credits And References](#credits-and-references) section.
   1. If there are no such dependencies, consider including a statement to that effect.
4. Delete these instructions and everything up to the _Project Title_ from the README.
5. Write some great software and tell people about it.

> Keep the README fresh! It's the first thing people see and will make the initial impression.

---- -->
# Repository Management Bot

**Description**:  A bot / script setup that manages repositories organization-wide. As the "bot" is currently a manually run script, it will only take actions when run.

Ideally, the bot would run on a schedule or be triggered by events in the organization, but that is not currently implemented.

The primary (and currently, only) functionality is to enforce templates on existing repositories via automatically generated pull requests.

![Example pull request](doc/Screenshot.png)

<!-- - **Technology stack**: Indicate the technological nature of the software, including primary programming language(s) and whether the software is intended as standalone or as a module in a framework or other ecosystem. -->
- **Technology stack**:
  - Language: Python
  - Primary Libraries: PyGithub
  - Interface: GitHub CLI, Command Line
- **Status**:  Alpha (Bare Minimum Functionality)
- **Links**:
  - [GitHub Repository](https://github.com/chp2001/repository-management-bot)

## Dependencies

- Python 3.8+ (Ideally 3.10+) (from [here](https://www.python.org/downloads/))
- PyGithub (from [here](https://pypi.org/project/PyGithub/))
- GitHub CLI (from [here](https://cli.github.com/))

<!-- ## Installation

Detailed instructions on how to install, configure, and get the project running.
This should be frequently tested to ensure reliability. Alternatively, link to
a separate [INSTALL](INSTALL.md) document.

## Configuration

If the software is configurable, describe it in detail, either here or in other documentation to which you link. -->

## Installation & Configuration

View the [INSTALL](INSTALL.md) document for detailed instructions on how to install, configure, and get the project running.

## Usage

<!-- Show users how to use the software.
Be specific.
Use appropriate formatting when showing code snippets. -->

The primary entry point is in the [`__main__.py`](repository_management_bot/__main__.py) file. It can be run with the following command (from the root of the repository):

```bash
python -m repository_management_bot [organization_name] [template_repository_name] [--org|-o organization_name] [--repo|-r template_repository_name] [--help|-h]
```

## Known issues

The bot is currently incomplete. Additionally, it can only act through the logged-in user, so it is not suitable for use in a production environment.

## Getting involved

<!-- Provide instructions on how to get involved in the project. -->
To get involved, please see the [CONTRIBUTING](CONTRIBUTING.md) document.

----

## Open source licensing info

1. [LICENSE](LICENSE)

----

## Credits and references

1. Dependabot (for inspiration)
