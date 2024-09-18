from .includes import *
    
from .access_gh import get_org_repo
from .repo_detail import get_repo_structure, RepoStructureType

AWI_ORG_NAME = "AlabamaWaterInstitute"
AWI_TEMPLATE_REPO = "awi-open-source-project-template"

def search_content_list(content_list: List[ContentFile], name: str) -> Optional[ContentFile]:
    return next(
        (content for content in content_list if content.name == name), None
    )

@cache
def get_template_details():
    repo = get_org_repo(AWI_ORG_NAME, AWI_TEMPLATE_REPO)
    repo_dir = repo.get_contents("")
    repo_dir = [repo_dir] if isinstance(repo_dir, ContentFile) else repo_dir
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
        
        
    def load_structure(self, subdir: str = "")->RepoStructureType:
        def file_registerer(content: ContentFile, path: str):
            self.file_list.append(Path(path))
        self.template_structure = get_repo_structure(self.template_repo, subdir, file_registerer)
        return self.template_structure
    
    def print_structure(self, subtree: Optional[Dict[str, Any]] = None, level: int = 0):
        if subtree is None:
            subtree = self.template_structure
        # fprint("\t"*level, "Structure:")
        if level > 4:
            raise RecursionError("Too many levels of recursion")
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
        if "README.md" not in diff_structure and "doc" in diff_structure:
            del diff_structure["doc"]
        return diff_structure
    
    def compare_repo(self, repo: Repository)->RepoStructureType:
        repo_structure = get_repo_structure(repo)
        return self.compare_repo_structure(repo_structure)

if __name__ == "__main__":
    repo, repo_dir, repo_file = get_template_details()
    fprint(repo, repo_dir, repo_file)
    
    template = RepoTemplate(AWI_ORG_NAME, AWI_TEMPLATE_REPO)
    template.print_structure()
    cache_stats()