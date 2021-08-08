#from .rules import StaticFileRule
from .rule_factory import ClassBasedRuleFactory


class RuleSet:
    """A repository of rules and rule factories used for building the dependency graph.
    See `Rule` and `RuleFactory`."""

    def __init__(self, static_rules_by_tid, rule_factories):
        """
        static_rules_by_tid - a mapping of target IDs to `Rule`s (or `Rule`-like objects)
        rule_factories - an iterable of `RuleFactory`s (or `RuleFactory`-like objects)
        """
        self.static_rules_by_tid = static_rules_by_tid
        self.rule_factories      = rule_factories

    def find_or_make_rule(self, tgt):
        """TODO"""

        try:
            return self.static_rules_by_tid[tgt.id]
        except KeyError:
            pass

        matching_rule_factories = [rf for rf in self.rule_factories if rf.matches(tgt)]

        if len(matching_rule_factories) == 0:
            raise NoRuleSetMatchError(tgt)
        elif len(matching_rule_factories) > 1:
            raise AmbiguousTargetIDError(tgt, matching_rule_factories)
        else:
            # TODO maybe try-catch here?
            return matching_rule_factories[0].instantiate(tgt)


class NoRuleSetMatchError(Exception):
    """Raised when no rule or rule factory matching a certain target ID can be found in a
    `RuleSet`"""

    def __init__(self, tgt):
        super().__init__(f"No rule found matching target ID {repr(tgt.id)}.")
        self.tgt = tgt


class AmbiguousTargetIDError(Exception):
    """Raised when two rule factories in a `RuleSet` match a certain target ID"""

    def __init__(self, tgt, matching_rule_factories):
        sep = "\n - "
        super().__init__(
            f"Ambiguous target ID {repr(tgt.id)} corresponds to several rule factories:\n"
            f"{sep.join(str(rf) for rf in matching_rule_factories)}"
        )
        self.tgt                     = tgt
        self.matching_rule_factories = matching_rule_factories


class RuleSetBuilder:
    """Offers convenience functionality for building a `RuleSet`, notably with function and class
    decorators. To finish building the `RuleSet`, call the `build` method."""

    def __init__(self):
        self._static_rules_map = dict()
        # Maps target identifiers to rules

        self._rule_factories = list()
        # A list of rule factories (see `RuleFactory`)

    def add_static_rule(self, rule):
        raise NotImplemented # TODO

    def add_rule_factory(self, rule_factory):
        self._rule_factories.append(rule_factory)

#    def static_file_rule(self, tgt, deps):
#        """Returns a decorator for a standalone recipe function. The decorator registers a `Rule`
#        that will build the `target` by calling the decorated function"""
#
#        def decorator(recipe_function):
#            if tgt.id in self._static_rules_map:
#                # TODO do we really want this? Should we allow several rules for a single target?
#                raise DuplicateRuleError(tgt)
#
#            self._static_rules_map[tgt.id] = StaticFileRule(tgt, deps, recipe_function)
#            return recipe_function
#
#        return decorator

    def generic(self, cls):
        """Decorator for generic rule classes. Creates and registers a `RuleFactory` based on the
        decorated class. The generated rules will be instances of that class."""

        self.add_rule_factory(ClassBasedRuleFactory(cls))
        return cls

    def build(self):
        return RuleSet(self._static_rules_map, self._rule_factories)


class DuplicateRuleError(Exception):
    def __init__(self, tgt):
        super().__init__(f"target ID {self.tgt.id} can only have one rule")
        self.tgt = tgt
