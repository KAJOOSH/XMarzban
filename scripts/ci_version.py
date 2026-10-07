"""Read the application version without importing or executing the application."""
import ast
import json
import os
import re
import subprocess
from pathlib import Path

VERSION_FILE = 'app/__init__.py'

def read_version(source):
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '__version__' for t in node.targets):
            value = ast.literal_eval(node.value)
            if not isinstance(value,str) or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?',value):
                raise ValueError('Application version must be a Docker-compatible semantic version')
            return value
    raise ValueError('Missing __version__')

def release_info(current_source, previous_source):
    version = read_version(current_source)
    previous = read_version(previous_source) if previous_source is not None else None
    return {'version':version,'previous_version':previous or '', 'changed':str(version!=previous).lower()}

def main():
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    previous_ref = event.get('before') if os.environ.get('GITHUB_EVENT_NAME')=='push' else None
    if previous_ref and set(previous_ref)=={'0'}:
        previous_source = None
    else:
        if not previous_ref:
            result = subprocess.run(['git','rev-parse','--verify','HEAD^'],text=True,capture_output=True)
            previous_ref = result.stdout.strip() if result.returncode==0 else None
        previous_source = None
        if previous_ref:
            subprocess.run(['git','cat-file','-e',previous_ref+'^{commit}'],check=True)
            result = subprocess.run(['git','show',previous_ref+':'+VERSION_FILE],text=True,capture_output=True)
            if result.returncode==0:
                previous_source = result.stdout
            else:
                # A first addition of the version file is a version change.
                subprocess.run(['git','ls-tree',previous_ref,'--',VERSION_FILE],check=True,capture_output=True)
                if subprocess.check_output(['git','ls-tree',previous_ref,'--',VERSION_FILE]).strip():
                    raise RuntimeError('Could not read previous version file')
    info = release_info(Path(VERSION_FILE).read_text(),previous_source)
    with open(os.environ['GITHUB_OUTPUT'],'a') as f:
        for key,value in info.items(): f.write(f'{key}={value}\n')
    print(f"Application version: {info['version']}; previous: {info['previous_version'] or 'none'}; changed: {info['changed']}")

if __name__=='__main__': main()
