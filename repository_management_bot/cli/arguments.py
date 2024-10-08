from typing import List, Tuple, Dict, Set, Any, Union, Callable, Literal, Optional, TypeVar, TypedDict
import sys
ArgTupleType = Tuple[Tuple[Any,...], Dict[str, Any]]
def argtuple(*args: Any, **kwargs: Any) -> ArgTupleType:
    return args, kwargs

class argtype:
    """## argtype
    class for handling argument types
    """
    # Given attributes
    posargs: List[str] # List of positional argument names
    "a list of positional argument names. user provided"
    kwargs: Dict[str, Any] # Dictionary of keyword argument names and default values
    "a dictionary of keyword argument names and default values. user provided"
    # Derived attributes
    posonlyargs: Set[str] # List of positional only argument names
    "a list of positional only argument names. derived from posargs and kwargs"
    kwonlyargs: Set[str] # List of keyword only argument names
    "a list of keyword only argument names. derived from kwargs and posargs"
    allargs: Set[str] # List of all argument names
    "a list of all argument names. derived from posargs and kwargs"
    def __init__(self, *args: str, **kwargs: Any):
        self.posargs = list(args) or []
        self.kwargs = kwargs or {}
        self.posonlyargs = {posarg for posarg in self.posargs if posarg not in self.kwargs}
        self.kwonlyargs = {kwarg for kwarg in self.kwargs if kwarg not in self.posargs}
        self.allargs = set(self.posargs) | set(self.kwargs.keys())
    
    def __repr__(self):
        argstrs = []
        for posarg in self.posargs:
            if posarg in self.kwargs:
                argstrs.append(f"{posarg}={self.kwargs[posarg]}")
            else:
                argstrs.append(posarg)
        argstrs.append("/")
        argstrs.extend(f"{kwarg}={self.kwargs[kwarg]}" for kwarg in self.kwargs)
        return "argtype(" + ", ".join(argstrs) + ")"
    
    def parse(self, arg: ArgTupleType) -> Dict[str, Any]:
        """## parse
        parse the given argument tuple into a dictionary of argument names and values
        
        ### Parameters:
        - `arg: ArgTupleType` - the argument tuple to parse
        
        ### Returns:
        - `Dict[str, Any]` - the dictionary of argument names and values
        """
        args, kwargs = arg
        argdict = {}
        for i, posarg in enumerate(self.posargs):
            if i < len(args):
                argdict[posarg] = args[i]
            elif posarg in self.kwargs:
                argdict[posarg] = self.kwargs[posarg]
            else:
                raise ValueError(f"missing required positional argument: {posarg}")
        for kwarg in self.kwargs:
            if kwarg in kwargs:
                argdict[kwarg] = kwargs[kwarg]
            elif kwarg in self.posargs:
                continue
            else:
                argdict[kwarg] = self.kwargs[kwarg]
        return argdict

ProgInfoExp = TypedDict(
    "ProgInfoExp", # Store pieces of ProgInfo explicitly, rather than as a single string
    {
        "info_type": Literal["explicit"],
        "program_name": str,
        "program_github_link": Optional[str],
        "program_version": str,
        "program_author": str,
        "program_description": Optional[str],
        "program_header": Optional[str]
    }
)
ProgInfoStr = TypedDict(
    "ProgInfoStr", # Store ProgInfo as a single string
    {
        "info_type": Literal["string"],
        "program_header": str
    }
)
ProgInfoType = Union[ProgInfoExp, ProgInfoStr]
class argparser:
    """## argparser
    class for parsing command line arguments
    """
    arg_configs: List[ArgTupleType] # List of argument configurations
    "a list of argument configurations. user provided"
    arg_config_by_name: Dict[str, ArgTupleType] # Dictionary of argument configurations by name
    "a dictionary of argument configurations by name. derived from arg_configs"
    arg_aliases: Dict[str, str] # Dictionary of argument aliases
    "a dictionary of argument aliases. derived from arg_configs"
    arg_type: argtype # Argument type object
    "an argument type object. derived from arg_configs"
    prog_info: Optional[ProgInfoType] # Program header
    """program information.
    <br> if explicit information is provided, additional arguments are allowed, and a header will be generated (if not provided)
    <br> otherwise only a header will be prepended to the help message"""
    default_args: Dict[str, ArgTupleType] = {
        "help": argtuple("-h", "--help", default=False, argtype=bool, help="Show this help message and exit")
    }
    "a dictionary of default arguments provided by the class"
    conditional_args: Dict[str, ArgTupleType] = {
        "program_version": argtuple("-v", "--version", default=False, argtype=bool, help="Show program version and exit"),
        "program_header": argtuple("-i", "--info", default=False, argtype=bool, help="Show program information and exit")
    }
    "a dictionary of conditional arguments provided by the class"
    __initialized: bool = False
    def __init__(self, arg_configs: List[ArgTupleType]):
        self.arg_configs = arg_configs
        self.arg_config_by_name = {}
        self.arg_aliases = {}
        self.prog_info = None
        self.__initialized = False
    def setup(self):
        if self.__initialized:
            return
        self.arg_type, self.arg_config_by_name, self.arg_aliases = self.initialize_arg_type()
        self.initialize_prog_info()
        self.__initialized = True
    def add_prog_info(self, prog_info: ProgInfoType):
        """## add_prog_info
        add program information to the argument parser
        
        ### Parameters:
        - `prog_info: ProgInfoType` - the program information to add
        """
        self.prog_info = prog_info
    def initialize_prog_info(self):
        if self.prog_info is None:
            return
        if self.prog_info["info_type"] == "explicit":
            if self.prog_info["program_header"] is None:
                header = ""
                version_str = self.prog_info["program_version"]
                if version_str.isnumeric():
                    version_str = f"v{version_str}"
                header += f"{self.prog_info['program_name']} [{version_str}]\n"
                if "program_author" in self.prog_info:
                    header += f"by {self.prog_info['program_author']}"
                    if "program_github_link" in self.prog_info:
                        header += f" (at {self.prog_info['program_github_link']})"
                    header += "\n"
                if "program_description" in self.prog_info:
                    header += f"{self.prog_info['program_description']}\n"
                self.prog_info["program_header"] = header
        elif self.prog_info["info_type"] == "string":
            pass
        else:
            raise ValueError(f"unknown program info type: {self.prog_info['info_type']}")
    def initialize_arg_type(self)->Tuple[argtype, Dict[str, ArgTupleType], Dict[str, str]]:
        """## initialize_arg_type
        initialize the argument type object
        
        ### Returns:
        - `Tuple[argtype, Dict[str, ArgTupleType], Dict[str, str]]` - the argument type object, the argument configurations by name, and the argument aliases
        """
        arg_configs = self.arg_configs
        arg_config_by_name = {}
        arg_aliases = {}
        posargs = []
        kwargs = {}
        for name, config in self.default_args.items():
            arg_configs.append(config)
        for name, config in self.conditional_args.items():
            if "program" in name:
                if self.prog_info is None:
                    continue
                if name in self.prog_info:
                    arg_configs.append(config)
            else:
                raise ValueError(f"unknown conditional argument: {name}")
        for arg_config in arg_configs:
            names, config_kwargs = arg_config
            posnames = [name for name in names if not name.startswith("-")]
            shortnames = [name for name in names if name.startswith("-") and len(name) == 2]
            longnames = [name for name in names if name.startswith("--")]
            long_name = posnames[0] if posnames else longnames[0].lstrip("-")
            if len(shortnames) > 1:
                raise ValueError(f"multiple short names in {names}")
            if len(longnames) > 1:
                raise ValueError(f"multiple long names in {names}")
            if len(posnames) > 1:
                raise ValueError(f"multiple positional names in {names}")
            arg_config_by_name[long_name] = arg_config
            for name in names:
                _name = name.lstrip("-")
                arg_aliases[_name] = long_name
            if posnames:
                posargs.append(posnames[0])
            if longnames:
                kwargs[long_name] = config_kwargs["default"]
        # print(posargs, kwargs)
        # print(self.arg_aliases)
        arg_type = argtype(*posargs, **kwargs)
        return arg_type, arg_config_by_name, arg_aliases
    def help_message(self):
        """## help_message
        print the help message
        """
        self.setup()
        if self.prog_info is not None:
            if self.prog_info["info_type"] == "explicit":
                print(self.prog_info["program_header"])
            elif self.prog_info["info_type"] == "string":
                print(self.prog_info["program_header"])
            else:
                raise ValueError(f"unknown program info type: {self.prog_info['info_type']}")
        print("Usage:")
        for names, config in self.arg_configs:
            helpstr = config.get("help", "")
            if "default" in config:
                helpstr += f" (default: {config['default']})"
            print("\t" + ", ".join(names) + " - " + helpstr)
    def version_message(self):
        """## version_message
        print the version message
        """
        self.setup()
        if self.prog_info is not None and "program_version" in self.prog_info:
            version_str = self.prog_info["program_version"]
            if version_str.isnumeric():
                version_str = f"v{version_str}"
            print(f"{self.prog_info['program_name']} [{version_str}]")
        else:
            raise ValueError(f"unexpected call to version_message without program version")
    def info_message(self):
        """## info_message
        print the info message
        """
        self.setup()
        if self.prog_info is not None:
            if self.prog_info["info_type"] == "explicit":
                print(self.prog_info["program_header"])
            elif self.prog_info["info_type"] == "string":
                print(self.prog_info["program_header"])
            else:
                raise ValueError(f"unknown program info type: {self.prog_info['info_type']}")
    def parse_argv(self)->ArgTupleType:
        """## parse_argv
        parse the command line arguments
        
        ### Returns:
        - `ArgTupleType` - the parsed arguments
        """
        args = sys.argv[1:]
        posargs = []
        kwargs = {}
        i = 0
        while i < len(args) and not args[i].startswith("-"):
            posargs.append(args[i])
            # print(args[i])
            i += 1
        argval = []
        kw = ""
        while i < len(args):
            # print(args[i])
            if args[i].startswith("-"):
                if kw:
                    kwargs[kw] = " ".join(argval) if argval else ""
                argval = []
                kw = self.arg_aliases[args[i].lstrip("-")]
                if self.arg_config_by_name[kw][1]["argtype"] == bool:
                    kwargs[kw] = True
            else:
                argval.append(args[i])
            i += 1
        if argval and kw:
            kwargs[kw] = " ".join(argval)
        # print(posargs, kwargs)
        return (tuple(posargs), kwargs)
    
    def parse_args(self) -> Dict[str, Any]:
        """## parse
        parse the given argument tuple into a dictionary of argument names and values
        
        ### Returns:
        - `Dict[str, Any]` - the dictionary of argument names and values
        """
        self.setup()
        result = self.arg_type.parse(self.parse_argv())
        for arg_name, config in self.arg_configs:
            if arg_name in result and isinstance(result[arg_name], str) and "argtype" in config:
                result[arg_name] = config["argtype"](result[arg_name])
        if result["help"] or (not any(result.values())):
            self.help_message()
            sys.exit(0)
        if result.get("version", False):
            self.version_message()
            sys.exit(0)
        if result.get("info", False):
            self.info_message()
            sys.exit(0)
        return result

# arg_configs = [
#     argtuple(
#         "org",
#         "--org",
#         "-o",
#         default="AlabamaWaterInstitute",
#         argtype=str,
#         help="The organization to check for template compliance"
#     ),
#     argtuple(
#         "repo",
#         "--repo",
#         "-r",
#         default="awi-open-source-project-template",
#         argtype=str,
#         help="The repository to check for template compliance"
#     )
# ]

# python -m repository_management_bot --org AlabamaWaterInstitute --template awi-open-source-project-template
#   Test all repositories in the AlabamaWaterInstitute organization against the awi-open-source-project-template repository
# OR
# python -m repository_management_bot --repo fakeUser/fakeRepo --template AlabamaWaterInstitute/awi-open-source-project-template
#   Test the fakeRepo repository owned by fakeUser against the awi-open-source-project-template repository in the AlabamaWaterInstitute organization

arg_configs = [
    argtuple(
        "org",
        "--org",
        "-o",
        default=None,
        argtype=str,
        help="A target organization to check for template compliance"
    ),
    argtuple(
        "template",
        "--template",
        "-t",
        default=None,
        argtype=str,
        help="The template repository to check against. If org is not provided, this should be in the format 'owner/repo', otherwise it can be just 'repo'"
    ),
    argtuple(
        "repo",
        "--repo",
        "-r",
        default=None,
        argtype=str,
        help="A specific repository to check for template compliance. If org is not provided, this should be in the format 'owner/repo', otherwise it can be just 'repo'"
    ),
    argtuple(
        "user",
        "--user",
        "-u",
        default=None,
        argtype=str,
        help="A specific user to check for template compliance."
    )
]

DefaultArgParse = argparser(arg_configs)