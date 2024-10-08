from __future__ import annotations
from typing import List, Tuple, Dict, Set, Any, Union, Callable, Literal, Optional, TypeVar, TypedDict
import os, sys, json, pickle
from pathlib import Path
import subprocess
import tkinter as tk
from tkinter import ttk
# Local imports
if __name__ == "__main__":
    sys.path.append(".")
from repository_management_bot.src.access_gh import get_user, get_org, get_repo
from repository_management_bot.src.includes import *
from repository_management_bot.src.repo_detail import get_repo_structure, RepoStructureType

class MinimizableFrame(ttk.Frame):
    stored_pack_info: List[Tuple[tk.Widget, Dict[str, Any]]]
    hf: ttk.Frame # Header frame
    cf: ttk.Frame # Content frame
    is_minimized: bool
    minimize_button: ttk.Button
    def __init__(self, master: tk.Misc, **kwargs):
        super().__init__(master, **kwargs)
        self.stored_pack_info = []
        self.is_minimized = False
        self.hf = ttk.Frame(self)
        self.hf.pack(expand=True, fill=tk.BOTH)
        self.minimize_button = ttk.Button(self.hf, text="-", command=self.toggle_minimize)
        self.minimize_button.pack(side=tk.RIGHT, anchor=tk.NE)
        self.cf = ttk.Frame(self)
        self.cf.pack(expand=True, fill=tk.BOTH)
        self.header_widgets = [self.minimize_button]
    
    def content_children(self)->List[tk.Widget]:
        return self.cf.winfo_children()
        
    def store_pack_info(self):
        self.stored_pack_info = []
        for child in self.content_children():
            pack_info = child.pack_info()
            self.stored_pack_info.append((child, pack_info)) # type: ignore
        
    def restore_pack_info(self):
        for child, pack_info in self.stored_pack_info:
            # print(f"Restoring {child}")
            child.pack(pack_info)
            
    def hide_children(self):
        for child in self.content_children():
            if child not in self.header_widgets:
                # print(f"Hiding {child}")
                child.pack_forget()
            
    def toggle_minimize(self):
        # print("Toggling minimize")
        # print(f"Children: {self.content_children()}")
        if self.is_minimized:
            self.restore_pack_info()
            self.minimize_button.config(text="-")
        else:
            self.store_pack_info()
            self.hide_children()
            self.minimize_button.config(text="+")
        self.is_minimized = not self.is_minimized
        self.cf.update()
        self.hf.update()
        self.update()
        self.master.update()
            
class OrgViewer(MinimizableFrame):
    org_name: Optional[str]
    org: Optional[Organization]
    org_repos: List[Repository]
    org_name_label: ttk.Label
    org_repo_list: ttk.Treeview
    
    def __init__(self, master: tk.Misc, org_name: Optional[str] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.org_name = org_name
        self.org = None
        self.org_name_label = ttk.Label(self.hf, text="Organization: ")
        self.org_name_label.pack(side=tk.LEFT, anchor=tk.NW)
        # self.pack_header(self.org_name_label, side=tk.LEFT, anchor=tk.NW)
        # self.header_widgets.append(self.org_name_label)
        self.org_repos = []
        self.org_repo_list = ttk.Treeview(self.cf, columns=("name", "description", "language", "stars", "forks"), show="headings")
        self.org_repo_list.heading("name", text="Name")
        self.org_repo_list.heading("description", text="Description")
        self.org_repo_list.heading("language", text="Language")
        self.org_repo_list.heading("stars", text="Stars")
        self.org_repo_list.heading("forks", text="Forks")
        self.org_repo_list.pack(expand=True, fill=tk.BOTH)
        # self.pack_content(self.org_repo_list, expand=True, fill=tk.BOTH)
        self.update_org()
        
    def update_org(self):
        if self.org_name is not None:
            self.org = get_org(self.org_name)
            self.org_name_label.config(text=f"Organization: {self.org_name}")
            self.org_repos = list(self.org.get_repos())
            self.update_repos()
            
    def update_repos(self):
        self.org_repo_list.delete(*self.org_repo_list.get_children())
        for repo in self.org_repos:
            self.org_repo_list.insert("", "end", values=(repo.name, repo.description, repo.language, repo.stargazers_count, repo.forks_count))
            
class UserViewer(MinimizableFrame):
    user_name: Optional[str]
    user: Optional[User]
    user_repos: List[Repository]
    user_name_label: ttk.Label
    user_repo_list: ttk.Treeview
    
    def __init__(self, master: tk.Misc, user_name: Optional[str] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.user_name = user_name
        self.user = None
        self.user_name_label = ttk.Label(self.hf, text="User: ")
        self.user_name_label.pack(side=tk.LEFT, anchor=tk.NW)
        # self.pack_header(self.user_name_label, side=tk.TOP, anchor=tk.NW)
        # self.header_widgets.append(self.user_name_label)
        self.user_repos = []
        self.user_repo_list = ttk.Treeview(self.cf, columns=("name", "description", "language", "stars", "forks"), show="headings")
        self.user_repo_list.heading("name", text="Name")
        self.user_repo_list.heading("description", text="Description")
        self.user_repo_list.heading("language", text="Language")
        self.user_repo_list.heading("stars", text="Stars")
        self.user_repo_list.heading("forks", text="Forks")
        self.user_repo_list.pack(expand=True, fill=tk.BOTH)
        # self.pack_content(self.user_repo_list, expand=True, fill=tk.BOTH)
        self.update_user()
        
    def update_user(self):
        if self.user_name is not None:
            user = get_user(self.user_name)
            if user is not None:
                self.user = user
                self.user_repos = list(user.get_repos())
                self.user_name_label.config(text=f"User: {self.user_name}")
                self.update_repos()
            
    def update_repos(self):
        self.user_repo_list.delete(*self.user_repo_list.get_children())
        for repo in self.user_repos:
            self.user_repo_list.insert("", "end", values=(repo.name, repo.description, repo.language, repo.stargazers_count, repo.forks_count))
            
class RepoViewer(MinimizableFrame):
    repo_name: Optional[str]
    repo: Optional[Repository]
    repo_structure: Optional[RepoStructureType]
    structure_stats: Dict[str, Tuple[int, int, Optional[str]]]
    current_path: str
    back_button: ttk.Button
    repo_name_label: ttk.Label
    repo_file_tree: ttk.Treeview
    
    def __init__(self, master: tk.Misc, repo_name: Optional[str] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.repo_name = repo_name
        self.repo = None
        self.repo_structure = None
        self.repo_name_label = ttk.Label(self.hf, text="Repository: ")
        self.repo_name_label.pack(side=tk.LEFT, anchor=tk.NW)
        # self.pack_header(self.repo_name_label, side=tk.TOP, anchor=tk.NW)
        # self.header_widgets.append(self.repo_name_label)
        self.structure_stats = {}
        self.current_path = ""
        self.back_button = ttk.Button(self.cf, text="Back", command=self.back)
        self.back_button.pack()
        # self.pack_content(self.back_button, side=tk.LEFT, anchor=tk.NW)
        self.repo_file_tree = ttk.Treeview(self.cf, columns=("name", "type", "size", "date-modified"), show="headings")
        self.repo_file_tree.heading("name", text="Name")
        self.repo_file_tree.heading("type", text="Type")
        self.repo_file_tree.heading("size", text="Size")
        self.repo_file_tree.heading("date-modified", text="Date Modified")
        self.repo_file_tree.column("size", width=100)
        self.repo_file_tree.column("date-modified", width=150)
        self.repo_file_tree.pack(expand=True, fill=tk.BOTH)
        # self.pack_content(self.repo_file_tree, expand=True, fill=tk.BOTH)
        self.setup_bindings()
        self.update_repo()
        
    def setup_bindings(self):
        self.repo_file_tree.bind("<Double-1>", self.on_double_click)
        self.repo_file_tree.bind("<Return>", self.on_double_click)
        self.repo_file_tree.bind("<BackSpace>", self.on_back)
        self.repo_file_tree.bind("<Left>", self.on_back)
        self.repo_file_tree.bind("<Right>", self.on_open)
        
    def update_repo(self):
        if self.repo_name is not None:
            self.repo = get_repo(self.repo_name)
            self.repo_name_label.config(text=f"Repository: {self.repo_name}")
            self.repo_structure = get_repo_structure(self.repo)
            self.show_root()
            
    def pathto(self, path: str)->Union[ContentFile, RepoStructureType, None]:
        cur_dir = self.repo_structure
        for part in path.split("/"):
            if not part:
                continue
            if isinstance(cur_dir, dict):
                cur_dir = cur_dir[part]
            else:
                raise ValueError(f"Path {path} is invalid for structure {cur_dir}")
        return cur_dir
            
    def navigate(self, path: str):
        self.current_path = path
        self.show_structure(path)
        
    def back(self):
        if self.current_path:
            parts = self.current_path.split("/")
            if len(parts) > 1:
                self.navigate("/".join(parts[:-1]))
            else:
                self.show_root()
        else:
            self.show_root()
            
    def on_double_click(self, event):
        item = self.repo_file_tree.selection()[0]
        path = self.repo_file_tree.item(item, "values")[0]
        if self.current_path:
            path = f"{self.current_path}/{path}"
        destination = self.pathto(path)
        if not destination or isinstance(destination, ContentFile):
            return
        self.navigate(path)
        
    def on_back(self, event):
        self.back()
        
    def on_open(self, event):
        item = self.repo_file_tree.selection()[0]
        path = self.repo_file_tree.item(item, "values")[0]
        if self.current_path:
            path = f"{self.current_path}/{path}"
        destination = self.pathto(path)
        if not destination or isinstance(destination, ContentFile):
            return
        self.navigate(path)
            
    def show_root(self):
        if self.repo_structure is not None:
            self.show_structure("")
            
    def get_subtree_stats(self, key: str, subtree: RepoStructureType)->Tuple[int, int, Optional[str]]:
        if key in self.structure_stats:
            return self.structure_stats[key]
        last_modified = None
        total_size = 0
        total_files = 0
        for name, content in subtree.items():
            if isinstance(content, ContentFile):
                total_size += content.size
                total_files += 1
                if content.last_modified is not None:
                    if not last_modified or content.last_modified > last_modified:
                        last_modified = content.last_modified
            else:
                subtree_size, subtree_files, subtree_last_modified = self.get_subtree_stats(f"{key}/{name}", content)
                total_size += subtree_size
                total_files += subtree_files
                if subtree_last_modified is not None:
                    if not last_modified or subtree_last_modified > last_modified:
                        last_modified = subtree_last_modified
        self.structure_stats[key] = (total_size, total_files, last_modified)
        return total_size, total_files, last_modified
            
    def show_structure(self, path: str):
        self.repo_file_tree.delete(*self.repo_file_tree.get_children())
        cur_dir = self.pathto(path)
        if isinstance(cur_dir, dict):
            for name, content in cur_dir.items():
                if isinstance(content, ContentFile):
                    self.repo_file_tree.insert("", "end", values=(name, content.type, content.size, content.last_modified))
                else:
                    subtree_size, subtree_files, subtree_last_modified = self.get_subtree_stats(f"{path}/{name}", content)
                    self.repo_file_tree.insert("", "end", values=(name, "dir", subtree_size, subtree_last_modified))
        else:
            raise ValueError(f"Path {path} is invalid for structure {cur_dir}")
        self.current_path = path
                    
            
            
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Repository Viewer")
    org_frame = OrgViewer(root, org_name=input("Organization: "))
    org_frame.pack(expand=True, fill=tk.BOTH, anchor=tk.NW)
    user_frame = UserViewer(root, user_name=input("User: "))
    user_frame.pack(expand=True, fill=tk.BOTH, anchor=tk.NW)
    repo_frame = RepoViewer(root, repo_name=input("Repository: "))
    repo_frame.pack(expand=True, fill=tk.BOTH, anchor=tk.NW)
    root.mainloop()