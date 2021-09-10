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

    # TODO is there a use case for this?
    #def on_failure(self, node):
    #    pass


class TrivialRule(Rule):
    """A trivial rule has no recipe: nothing needs to be done to build its target"""
    def recipe(self):
        raise NotImplemented

    def has_recipe(self):
        return False


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


class LeafRule(Rule):
    """Rule stating that the target has no dependencies (it is therefore a "leaf", i.e. a node
    without successors in the dependency graph described by the rules)."""
    def deps(self):
        return []


class SourceRule(LeafRule, TrivialRule):
    """The target has no dependencies and no recipe. For example, a manually written source code
    file would correspond to a `SourceRule`."""
    pass
