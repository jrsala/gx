import argparse
import glob
import enum
import sys
from pathlib import Path

from GX           import GraphExecutor
from GX.target    import Id, PhonyTarget
from GX.rules     import TrivialRule
from GX.langs.cpp import cpp_ruleset_builder, LinkedArtifactTarget


SRC_DIR_PATH   = Path("src")
BUILD_DIR_PATH = Path("build")

ARTIFACT_FILENAME = "foo"

CPP_FILE_PATHS = list(SRC_DIR_PATH.glob("**/*.cpp"))

CXXFLAGS_COMMON  = "-Wall -Werror"
CXXFLAGS_RELEASE = f"{CXXFLAGS_COMMON} -O2 -flto -march=native"
CXXFLAGS_DEBUG   = f"{CXXFLAGS_COMMON} -O0 -g3"

LDFLAGS = "-lstdc++"


class BuildMode(enum.Enum):
    RELEASE = 0
    DEBUG   = 1

    @staticmethod
    def from_string(s):
        """Case-insensitively converts a "release" or "debug" string to `BuildMode`"""
        u = s.upper()
        if u == "RELEASE": return BuildMode.RELEASE
        elif u == "DEBUG": return BuildMode.DEBUG
        else: raise ValueError(f"Invalid BuildMode string \"{s}\"")


class BuildModeTarget(PhonyTarget):
    def __init__(self, build_mode):
        super().__init__()
        self.build_mode = Id(build_mode)

    def dirname(self):
        return self.build_mode.name.lower() # "release" or "debug"


rsb = cpp_ruleset_builder(SRC_DIR_PATH, BUILD_DIR_PATH)

@rsb.generic
class BuildModeRule(TrivialRule):
    @staticmethod
    def matches(tgt):
        return isinstance(tgt, BuildModeTarget)

    def deps(self):
        mode_build_dir = BUILD_DIR_PATH / self.tgt.dirname()

        return [LinkedArtifactTarget(
            path          =mode_build_dir / ARTIFACT_FILENAME,
            cxxflags      =CXXFLAGS_DEBUG if self.tgt.build_mode is BuildMode.DEBUG else CXXFLAGS_RELEASE,
            ldflags       =LDFLAGS,
            cpp_file_paths=CPP_FILE_PATHS,
            make_object_file_path=lambda cpp_file_path: (
                mode_build_dir / cpp_file_path.with_suffix(".o").relative_to(SRC_DIR_PATH)
            )
        )]


def positive_int(s):
    n = int(s)
    if n <= 0:
        raise ValueError(f"Expected positive integer but got '{s}'")
    return n


def read_program_arguments():
    parser = argparse.ArgumentParser(description="Hi")

    parser.add_argument("targets", nargs="*", default=["release"])
    parser.add_argument("-j", "--jobs", dest="worker_count", type=positive_int, default=1)

    return parser.parse_args()


def main():
    args = read_program_arguments()
    gx = GraphExecutor(rsb.build(), args.worker_count)
    success = gx.build(BuildModeTarget(BuildMode.from_string(t)) for t in args.targets)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
