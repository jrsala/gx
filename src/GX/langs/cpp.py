from ..target  import Id, Target, FileTarget, DirectoryTarget
from ..rules   import Rule, FileRule, SourceFileRule
from ..ruleset import RuleSetBuilder
from ..util    import sh, parse_object_file_make_deps
import sys # TODO remove
from pathlib import Path


###################################################################################################
# TARGET TYPES
###################################################################################################

class CompiledTarget(FileTarget):
    """Identifies a compiled file (object file(s) or linked artifact) by its path and set of
    compilation options (debug and release, but there could be more)."""

    def __init__(self, path, cxxflags):
        super().__init__(path)
        self.cxxflags = Id(cxxflags)


class LinkedArtifactTarget(CompiledTarget):
    """Identifies an artifact that's the result of linking: an executable or a shared library."""

    def __init__(self, path, cxxflags, ldflags, cpp_file_paths, make_object_file_path):
        """make_object_file_path - A callable that maps a CPP source file path to the corresponding
        object file path"""
        super().__init__(path, cxxflags)
        self.ldflags               = Id(ldflags)
        self.cpp_file_paths        = Id(cpp_file_paths)
        self.make_object_file_path = make_object_file_path


class StaticLibraryTarget(CompiledTarget):
    """Identifies a static library, made with `ar`"""

    def __init__(self, path, cxxflags, cpp_file_paths):
        super().__init__(path, cxxflags)
        self.cpp_file_paths = Id(cpp_file_paths)


class ObjectFileTarget(CompiledTarget):
    """Identifies an object file"""

    def __init__(self, path, cxxflags, cpp_file_path):
        super().__init__(path, cxxflags)
        self.cpp_file_path = Id(cpp_file_path)


class HeaderDepsTarget(Target):
    """Identifies the target of computing some .cpp file's header depencies"""

    def __init__(self, cpp_file_path):
        super().__init__()
        self.cpp_file_path = Id(cpp_file_path)

    def timestamp(self):
        return None # Always remake this (TODO write the .d file instead?)


class SourceFileTarget(FileTarget):
    """Identifies a .cpp or .h file"""
    pass


###################################################################################################
# RULESET CONSTRUCTION
###################################################################################################

def cpp_ruleset_builder(SRC_DIR_PATH, BUILD_DIR_PATH):

    rsb = RuleSetBuilder()

    @rsb.generic
    class DirectoryRule(Rule):
        @staticmethod
        def matches(tgt):
            return isinstance(tgt, DirectoryTarget)

        def deps(self):
            return []

        def recipe(self):
            sh(f"mkdir -p {self.tgt.path}")


    @rsb.generic
    class LinkedArtifactRule(Rule):
        @staticmethod
        def matches(tgt):
            return isinstance(tgt, LinkedArtifactTarget)

        def init(self):
            self.obj_tgts = list(
                ObjectFileTarget(
                    path         =self.tgt.make_object_file_path(p),
                    cxxflags     =self.tgt.cxxflags,
                    cpp_file_path=p
                )
                for p in self.tgt.cpp_file_paths
            )

        def deps(self):
            return [DirectoryTarget(self.tgt.path.parent)] + self.obj_tgts

        def recipe(self):
            sh(
                 "gcc "
                f"{' '.join(str(obj_tgt.path) for obj_tgt in self.obj_tgts)} "
                f"-o {self.tgt.path} {self.tgt.ldflags}"
            )


    @rsb.generic
    class ObjectFileRule(Rule):
        @staticmethod
        def matches(tgt):
            return isinstance(tgt, ObjectFileTarget)

        def init(self):
            self.header_deps_tgts = []

        def deps(self):
            return [
                DirectoryTarget(self.tgt.path.parent),
                HeaderDepsTarget(self.tgt.cpp_file_path),
                SourceFileTarget(self.tgt.cpp_file_path) # Redundant but meh
            ] + self.header_deps_tgts

        def recipe(self):
            sh(f"gcc -c {self.tgt.cpp_file_path} -o {self.tgt.path} {self.tgt.cxxflags}")

        def set_header_deps(self, header_deps_tgts):
            self.header_deps_tgts = header_deps_tgts


    @rsb.generic
    class HeaderDepsRule(Rule):
        @staticmethod
        def matches(tgt):
            return isinstance(tgt, HeaderDepsTarget)

        def deps(self):
            return [SourceFileTarget(self.tgt.cpp_file_path)]

        def recipe(self):
            completed_process = sh(
                f"gcc -MM {self.tgt.cpp_file_path}",
                capture_output=True,
                text=True
            )
            return parse_object_file_make_deps(completed_process.stdout)

        def on_built(self, gx, node, job_value):
            for p in node.predecessors:
                assert isinstance(p.rule, ObjectFileRule), \
                    "Expected HeaderDepsRule to only have ObjectFileRule predecessors"

                p.rule.set_header_deps([
                    SourceFileTarget(Path(name)) for name in job_value.header_filenames
                ])

                gx.expand(p)


    @rsb.generic
    class CppSourceFileRule(SourceRule):
        @staticmethod
        def matches(tgt):
            return isinstance(tgt, SourceFileTarget)


    return rsb
