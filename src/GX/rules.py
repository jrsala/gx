from abc import ABC, abstractmethod


class Rule(ABC):
    """Abstract base class of build rules. A rule associates a single target (identified by its ID)
    with a set of dependencies (identified by their IDs) and a recipe for building that target."""

    def __init__(self, tgt, *args, **kwargs):
        self.tgt = tgt
        self.init(*args, **kwargs)

    def init(self):
        """Initialization method invoked by `Rule.__init__` so subclasses can override it instead
        of all defining a `__init__` that does the sempiternal `super().__init__(tgt)`."""
        pass

    @abstractmethod
    def deps(self):
        """Returns an iterable of targets that are the dependencies of this rule"""
        raise NotImplemented

    @abstractmethod
    def recipe(self):
        """Executes the job"""
        raise NotImplemented

    def has_recipe(self):
        """Returns whether this rule has a recipe. The default implementation returns `True`
        because most rules will be non-trivial and have a recipe."""
        return True

    def on_success(self, gx, node, job_value):
        """Invoked by the build algorithm after the rule's recipe has been run successfully,
        after it was skipped or if there was no recipe."""
        pass

    #def on_failure(self, node):
    #    pass


class TrivialRule(Rule):
    def recipe(self):
        raise NotImplemented

    def has_recipe(self):
        return False


class FileRule(Rule):
    """Base class for rules that produce a file."""
    pass

class DirectoryRule(FileRule):
    """Class for rules that produce a directory"""

    def timestamp(self):
        # If the directory exists already, no need to remake it
        # TODO make this `sys.maxsize` a GX constant?
        return -sys.maxsize if self.tgt.path.is_dir() else None


#class StaticRule(Rule):
#    """Rule where the list of dependencies and recipe function are set at construction time and
#    never changed."""
#
#    def __init__(self, filename, deps, recipe_function):
#        super().__init__(filename)
#        self._deps            = deps
#        self._recipe_function = recipe_function
#
#    def deps(self):
#        return self._deps
#
#    def recipe(self):
#        return self._recipe_function()
#
#
#class StaticFileRule(StaticRule, FileRule):
#    def __init__(self, filename, deps, recipe_function):
#        super().__init__(filename, deps, recipe_function)


class SourceRule(TrivialRule):
    """Rule stating that the target has no dependencies (it is therefore a "leaf", i.e. a node
    without successors in the dependency graph described by the rules) and that nothing needs to
    be done in order to make it.
    For example, a manually written source code file would correspond to a `SourceRule`."""

    def deps(self):
        return []


class SourceFileRule(SourceRule, FileRule):
    """The target is a source file: no dependencies and no recipe"""
    pass


#class PhonyTargetRule(Rule):
#    """Base class for rules that do not produce a file. The targets are therefore "phony"."""
#    pass


#class GroupingRule(PhonyTargetRule, TrivialRule):
#    """A rule with no recipe (trivial) and not corresponding to a file target (phony): its only
#    purpose is to serve as a handle to a group of dependencies."""
#    pass
