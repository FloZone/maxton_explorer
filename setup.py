import distutils.cmd
import distutils.log
import os
import subprocess
import sys

from setuptools import setup


def list_git_modified_files():
    files = []
    output = subprocess.check_output(["git", "status", "--porcelain"])
    decoded_output = output.decode("utf-8")
    for line in decoded_output.split("\n"):
        if line.strip() == "":
            continue
        elems = line.strip().split(" ")
        status, filename = elems[0], " ".join(elems[1:]).strip()
        if status not in ["M", "U", "??", "A"]:
            continue
        files.append(filename)
    return files


def filter_python_files(files):
    return [f for f in files if f.endswith(".py") or os.path.isdir(f)]


def check_is_not_python(path):
    base, path_ext = os.path.splitext(path)
    return path_ext != "" and path_ext != ".py"


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class BaseCommand(distutils.cmd.Command):

    user_options = [("path=", "p", "path"), ("auto", "a", "auto")]

    def announce_with_paths(self, msg, paths):
        self.announce(f"{msg} on path(s) {', '.join(paths)} ...", level=distutils.log.INFO)

    def try_execute(self, msg, args):
        try:
            if msg:
                self.announce(msg, level=distutils.log.INFO)
            subprocess.check_call(args)
        except subprocess.CalledProcessError:
            return False

        return True

    def initialize_options(self):
        self.path = None
        self.auto = False

    def finalize_options(self):
        if self.path is None:
            self.path = "."

    def run(self):
        if self.auto:
            files = filter_python_files(list_git_modified_files())
            if not self.apply_command(files):
                sys.exit(1)
        else:
            if not self.apply_command([self.path]):
                sys.exit(1)


class LintCommand(BaseCommand):
    """Lint with flake8."""

    description = "run flake8 on source files"

    def apply_command(self, paths) -> bool:
        self.announce_with_paths("linting files", paths)
        return self.try_execute("flake8 pass ...", ["flake8", *paths])


class FormatCommand(BaseCommand):
    """Format with black."""

    description = "run lf script, isort and black on source files"

    def apply_command(self, paths) -> bool:
        self.announce_with_paths("formatting files", paths)

        if not self.try_execute("isort pass ...", ["isort", "-rc", "--atomic", *paths]):
            return False

        return self.try_execute(
            "black pass ...",
            [
                "black",
                "--target-version",
                "py38",
                "-l",
                "120",
                "--exclude",
                "/node_modules|staticfiles|translations|dist/",
                *paths,
            ],
        )


class FormatCheckCommand(BaseCommand):
    """Format check with black."""

    description = "run black check on source files"

    def apply_command(self, paths) -> bool:
        self.announce_with_paths("checking if files are formatted", paths)

        return self.try_execute(
            "black pass ...",
            [
                "black",
                "--target-version",
                "py36",
                "-l",
                "120",
                "--exclude",
                "/node_modules|staticfiles|translations/",
                "--check",
                *paths,
            ],
        )


setup(
    name="Product Explorer",
    author="FloZone",
    description=("Product Explorer"),
    long_description=read("README.md"),
    cmdclass={
        "lint": LintCommand,
        "fmt": FormatCommand,
        "fmtcheck": FormatCheckCommand,
    },
)
