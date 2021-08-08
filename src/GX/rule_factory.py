from abc import ABC, abstractmethod


class RuleFactory(ABC):
    @abstractmethod
    def matches(self, tgt):
        raise NotImplemented

    @abstractmethod
    def instantiate(self, tgt):
        raise NotImplemented


class ClassBasedRuleFactory(RuleFactory):
    def __init__(self, rule_cls):
        self.rule_cls = rule_cls

    def matches(self, tgt):
        return self.rule_cls.matches(tgt)

    def instantiate(self, tgt):
        return self.rule_cls(tgt)
