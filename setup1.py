from distutils.core import setup
import py2exe,os
import cmd,code,pdb,urllib3

setup(
options = { 
    "py2exe": 
    { 
        "includes": ["sys", "os", "configparser", "time", "datetime",
                     "base64", "json", "ast", "urllib3", "threading", "cmd", "code", "pdb", ],
        "dll_excludes": ["Secur32.dll", "SHFOLDER.dll"],
        'bundle_files': 1
    }
},
console = ['tse_file_get.py'],
zipfile = None
)

