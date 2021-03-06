import os
import subprocess
import collections
from surround import Config
import pandas as pd
import logging
import sys

config = Config()
config.read_config_files(['config.yaml'])
input_path = config['input_path']
output_path = config['output_path']

class ModuleInfo:
    def __init__(self, repo, path, diffcount=0, parse_error=False):
        self.repo = repo
        self.path = path
        # mapping of repo, path -> diffcount
        self.diffcount = diffcount
        self.parse_error = parse_error

    @staticmethod
    def from_diff(repo, path, stdout_capture, stderr_capture):
        parse_error = False
        diffcount = 0
        headers = 0

        lines = stdout_capture.split('\n')
        for line in lines:
            if line.startswith("---"):
                # Diff header
                # TODO: Deal with edge case where line itself begins with --
                headers += 1
                continue
            if line.startswith("+++"):
                # Diff header
                # TODO: Deal with edge case where line itself begins with ++
                continue
            if line.startswith("-"):
                diffcount += 1
                continue
            if line.startswith("+"):
                diffcount += 1
                continue

        # Raise assertion error if it diff header not as expected.
        if diffcount == 0:
            assert headers == 0
        else:
            assert headers == 1

        if "Can't parse" in stderr_capture:
            parse_error = True

        logging.info([repo, path, diffcount, headers, parse_error])
        
        return ModuleInfo(repo, path, diffcount, parse_error)

    # Class variable
    ROW_HEADERS = ["repo", "path", "diffcount", "parse_error"]

    def to_rows(self):
        result = [self.repo, self.path, self.diffcount, self.parse_error]
        return [result]

def process(repo, path, filepath):
    result = subprocess.run(["2to3", filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result_stdout = result.stdout.decode('utf-8')
    result_stderr = result.stderr.decode('utf-8')
    modinfo = ModuleInfo.from_diff(repo, path, result_stdout, result_stderr)
    return modinfo

def analyse_diffs(repo_dir, output_dir, repo_id_list=None):
    # Information Extraction:
    # mapping of repo, path -> ModuleInfo
    modules = {}

    # Post Analysis:
    # mapping of repo, path -> type

    if repo_id_list is None:
        repo_id_list = os.listdir(repo_dir)

    for repo in repo_id_list:
        repo_subdir = os.path.join(repo_dir, repo)
        for dirpath, dirnames, filenames in os.walk(repo_subdir):
            for filename in filenames:
                if filename.endswith(".py"):
                    logging.info([dirpath, filename])
                    filepath = os.path.join(dirpath, filename)
                    path = os.path.normpath(os.path.relpath(filepath, repo_dir))
                    modinfo = process(repo, path, filepath)
                    modules[(repo, path)] = modinfo

    rows = []
    for (repo, path), module in modules.items():
        rows += module.to_rows()

    df = pd.DataFrame.from_records(rows, columns=ModuleInfo.ROW_HEADERS)

    output_filename = os.path.join(output_dir, "results_2to3.csv")
    df.to_csv(output_filename, index=False)

if __name__ == "__main__":
    input_directory = os.path.join("../", input_path)

    try:
        # limit to list of repositories
        repo_list_path = sys.argv[1]
    except IndexError:
        repo_list_path = None

    if repo_list_path:
        repo_list_path = os.path.join("../", repo_list_path)
        repo_id_list = list(pd.read_csv(repo_list_path)["id"].astype(str))
    else:
        repo_id_list = None

    try:
        # custom output_path
        output_path = sys.argv[2]
    except IndexError:
        pass # leave output_path as is

    output_directory = os.path.join("../", output_path)
    logging.basicConfig(filename=os.path.join(output_directory, 'debug.log'),level=logging.DEBUG)

    analyse_diffs(input_directory, output_directory, repo_id_list)