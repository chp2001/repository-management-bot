from typing import List, Tuple, Dict, Set, Any, Union, Callable, Literal, Optional, TypeVar
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
    def __init__(self, arg_configs: List[ArgTupleType]):
        self.arg_configs = arg_configs
        self.arg_config_by_name = {}
        self.arg_aliases = {}
        posargs = []
        kwargs = {}
        self.add_help_arg(arg_configs)
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
            self.arg_config_by_name[long_name] = arg_config
            for name in names:
                _name = name.lstrip("-")
                self.arg_aliases[_name] = long_name
            if posnames:
                posargs.append(posnames[0])
            if longnames:
                kwargs[long_name] = config_kwargs["default"]
        # print(posargs, kwargs)
        # print(self.arg_aliases)
        self.arg_type = argtype(*posargs, **kwargs)
    def add_help_arg(self, arglist: List[ArgTupleType]):
        """## add_help_arg
        add a help argument to the argument configurations
        """
        argtup = argtuple("-h", "--help", default=False, argtype=bool, help="Show this help message and exit")
        arglist.append(argtup)
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
        result = self.arg_type.parse(self.parse_argv())
        for arg_name, config in self.arg_configs:
            if arg_name in result and isinstance(result[arg_name], str) and "argtype" in config:
                result[arg_name] = config["argtype"](result[arg_name])
        # print(result)
        # input()
        if result["help"]:
            print("Usage:")
            for names, config in self.arg_configs:
                helpstr = config.get("help", "")
                if "default" in config:
                    helpstr += f" (default: {config['default']})"
                print("\t" + ", ".join(names) + " - " + helpstr)
            sys.exit(0)
        return result

arg_configs = [
    argtuple(
        "org",
        "--org",
        "-o",
        default="AlabamaWaterInstitute",
        argtype=str,
        help="The organization to check for template compliance"
    ),
    argtuple(
        "repo",
        "--repo",
        "-r",
        default="awi-open-source-project-template",
        argtype=str,
        help="The repository to check for template compliance"
    )
]

DefaultArgParse = argparser(arg_configs)