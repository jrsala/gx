import enum


class _PathHoldingException(Exception):
    """TODO"""
    def __init__(self, tip_node):
        self.path = [tip_node]
        # This is the `path` from most depended-on node (`tip_node`) to most dependent node
        # (root node)

    def add_predecessor(self, node):
        self.path.append(node)

    def __str__(self):
        sep = "\n\t-> "
        return (
              f"{type(self).__name__}:\n\t   "
            + sep.join(str(n.rule.tgt.id) for n in reversed(self.path))
        )

class CyclicDependencyError(_PathHoldingException):
    pass

class GraphExpansionError(_PathHoldingException):
    """Meant to be used with `raise ... from ...` in order to provide a cause"""
    pass


class Datedness(enum.Enum):
    NEVER_BUILT = 0
    OUT_OF_DATE = 1
    UP_TO_DATE  = 2


class JobStatus(enum.Enum):
    INITIAL = 0
    SUCCESS = 1 # The recipe was run successfully or there was no recipe to run
    FAILURE = 2 # The recipe was run and failed
    SKIPPED = 3 # The recipe was not run because it didn't need to be


class _TraversalState(enum.Enum):
    TRAVERSING = 0
    TRAVERSED = 1


class DependencyGraphNode:
    """TODO this class is accessible by client code in `Rule.on_built` so it should encapsulate
    better."""

    def __init__(self, rule):
        self.rule = rule

        # Not known at construction time, computed later during graph generation
        self.successors   = None  # List of dependencies
        self.predecessors = set() # Set of dependents

        # Used for graph generation
        self._traversal_state = None

        # Computed during build execution (TODO this is accessed by `GraphExecutor`, breaking
        # encapsulation)
        self.job_status = JobStatus.INITIAL
        self.job_result = None

    def has_failed_successor(self):
        return any(s.job_status is JobStatus.FAILURE for s in self.successors)

    def job_value(self):
        return None if self.job_result is None else self.job_result.value

    def datedness(self):
        target_ts = self.rule.tgt.timestamp()

        if target_ts is None:
            return Datedness.NEVER_BUILT

        else:
            successor_timestamps = [
                ts for ts in (
                    s.rule.tgt.timestamp() for s in self.successors
                ) if ts is not None
            ]

            # TODO `<=` or `<`?
            if len(successor_timestamps) > 0 and target_ts <= max(successor_timestamps):
                return Datedness.OUT_OF_DATE
            else:
                return Datedness.UP_TO_DATE

    def all_successors_done(self):
        return all(s.job_status != JobStatus.INITIAL for s in self.successors)


class DependencyGraph:
    def __init__(self, ruleset):
        self._ruleset      = ruleset
        self._nodes_by_tid = {}


    def get_or_make_node(self, tgt):
        try:
            return self._nodes_by_tid[tgt.id]
        except KeyError:
            pass

        rule = self._ruleset.find_or_make_rule(tgt)
        new_node = DependencyGraphNode(rule)
        self._nodes_by_tid[tgt.id] = new_node
        return new_node


    def expand_dependency_subgraph(self, node):
        node._traversal_state = None
        leaves = set()
        self._do_expand_dependency_subgraph(node, leaves)
        return leaves

    def _do_expand_dependency_subgraph(self, node, leaves):
        if node._traversal_state is _TraversalState.TRAVERSED:
            return

        elif node._traversal_state is _TraversalState.TRAVERSING:
            raise CyclicDependencyError(duplicate_node=node)

        else:
            assert node._traversal_state is None, \
                   "Expected node._traversal_state to be None or a _TraversalState value"

            node._traversal_state = _TraversalState.TRAVERSING

            node.successors = [self.get_or_make_node(dep) for dep in node.rule.deps()]

            if len(node.successors) == 0:
                if False:
                    print(f"Found leaf {node.rule.tgt.id}\n")

                leaves.add(node)

            else:
                if False:
                    sep = "\n\t- "
                    print(f"{node.rule.tgt.id} depends on:" + ''.join((sep + str(n.rule.tgt.id)) for n in node.successors))
                    print()

                for s in node.successors:
                    s.predecessors.add(node)

                for s in node.successors:
                    try:
                        self._do_expand_dependency_subgraph(s, leaves)
                    except _PathHoldingException as ex:
                        ex.add_predecessor(node)
                        raise
                    except Exception as ex:
                        raise GraphExpansionError(s) from ex

            node._traversal_state = _TraversalState.TRAVERSED
