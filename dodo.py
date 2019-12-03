import os
import subprocess
from surround import Config

CONFIG = Config(os.path.dirname(__file__))
DOIT_CONFIG = {'verbosity':2}
PACKAGE_PATH = os.path.basename(CONFIG["package_path"])
IMAGE = "%s/%s:%s" % (CONFIG["company"], CONFIG["image"], CONFIG["version"])

PARAMS = [
    {
        'name': 'args',
        'long': 'args',
        'type': str,
        'default': ""
    }
]

def task_build():
    """Build the Docker image for the current project"""
    return {
        'actions': ['docker build --tag=%s .' % IMAGE],
        'params': PARAMS
    }


def task_remove():
    """Remove the Docker image for the current project"""
    return {
        'actions': ['docker rmi %s -f' % IMAGE],
        'params': PARAMS
    }

def task_explore():
    """Run the explore task for the project"""
    return {
        'actions': ["docker run --volume \"%s/\":/app %s python3 ./%s/task_explore.py %s" % (CONFIG["volume_path"], IMAGE, PACKAGE_PATH, "%(args)s")],
        'params': PARAMS
    }


def task_interactive():
    """Run the Docker container in interactive mode"""
    def run():
        process = subprocess.Popen(['docker', 'run', '-it', '--rm', '-w', '/app', '--volume', '%s/:/app' % CONFIG['volume_path'], IMAGE, 'bash'], encoding='utf-8')
        process.wait()

    return {
        'actions': [run]
    }


def task_prod():
    """Run the Docker container used for packaging """
    return {
        'actions': ["docker run %s" % (IMAGE)],
        'task_dep': ["build"],
        'params': PARAMS
    }