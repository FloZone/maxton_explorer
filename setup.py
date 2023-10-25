import distutils.cmd
import distutils.log
import os
import shutil
import subprocess

from packaging import version
import pyinstaller_versionfile
from setuptools import find_packages, setup

from maxton_explorer import SCRIPT_NAME, SCRIPT_VERSION

DESCRIPTION = "Maxton Explorer script"
INPUT_FILE = "maxton_explorer.py"
OUTPUT_FILE = "maxton_explorer.exe"
VERSION_FILE = "version_info.txt"


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class BuildCommand(distutils.cmd.Command):
    """Build script binary."""

    description = "Build script to .exe file"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self) -> bool:
        print("test")
        self.announce("Generating version file", level=distutils.log.WARN)
        v = version.parse(str(SCRIPT_VERSION))
        v = f"{str(v)}.0.0"
        pyinstaller_versionfile.create_versionfile(
            output_file=VERSION_FILE,
            version=v,
            company_name="FloZone",
            file_description=DESCRIPTION,
            internal_name=SCRIPT_NAME,
            legal_copyright="Copyright © 2023",
            original_filename=OUTPUT_FILE,
            product_name=SCRIPT_NAME,
        )

        self.announce("\nBuilding binary", level=distutils.log.WARN)
        res = subprocess.run(
            [
                "pyinstaller",
                "--clean",
                "--icon=app.ico",
                "--onefile",
                f"--version-file={VERSION_FILE}",
                f"./{INPUT_FILE}",
            ]
        )
        if res.returncode == 0:
            self.announce(f"\nBinary file generated to './dist/{OUTPUT_FILE}'", level=distutils.log.WARN)
            return True
        else:
            return False


class CleanCommand(distutils.cmd.Command):
    """Clean temporary files."""

    description = "Clean temporary files"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self) -> bool:
        self.announce("Cleaning project...", level=distutils.log.WARN)

        paths = ["build", "dist", "__pycache__", "maxton_explorer.spec", VERSION_FILE]
        for p in paths:
            if os.path.isdir(p):
                self.announce(f"Cleaning ./{p}/", level=distutils.log.WARN)
                shutil.rmtree(p)
            elif os.path.isfile(p):
                self.announce(f"Cleaning ./{p}", level=distutils.log.WARN)
                os.remove(p)
        return True


class LintCommand(distutils.cmd.Command):
    """Lint with flake8."""

    description = "run flake8 on source files"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self) -> bool:
        self.announce("Linting...", level=distutils.log.WARN)

        self.announce("flake8 pass...", level=distutils.log.WARN)
        return subprocess.run(["flake8", INPUT_FILE]).returncode == 0


class FormatCommand(distutils.cmd.Command):
    """Format with black."""

    description = "Run isort and black on source files"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self) -> bool:
        self.announce("Formatting...", level=distutils.log.WARN)

        self.announce("isort pass...", level=distutils.log.WARN)
        if subprocess.run(["isort", "-rc", "--atomic", INPUT_FILE]).returncode != 0:
            return False

        self.announce("black pass...", level=distutils.log.WARN)
        return subprocess.run(
            [
                "black",
                "--target-version",
                "py38",
                "-l",
                "120",
                INPUT_FILE,
            ],
        ).returncode == 0


setup(
    name=SCRIPT_NAME,
    version=SCRIPT_VERSION,
    author="FloZone",
    description=DESCRIPTION,
    long_description=read("README.md"),
    packages=find_packages(),
    cmdclass={
        "clean": CleanCommand,
        "build": BuildCommand,
        "lint": LintCommand,
        "fmt": FormatCommand,
    },
)
