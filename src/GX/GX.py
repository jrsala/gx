import os
import sys

from . import thread_pool as tp
from .dep_graph import DependencyGraph, Datedness, JobStatus


class _GxJob(tp.Job):
    def __init__(self, node):
        super().__init__(node.rule.recipe)
        self.node = node


class GraphExecutor:
    """TODO"""

    def __init__(self, rule_set, worker_count=1, working_dir=sys.path[0]):
        # `sys.path[0]` is the path of the directory containing the script the Python interpeter
        # was started with. In most cases, that should be the directory of the script using GX
        # and describing a build. We expect the user script to refer to files using paths relative
        # to the directory that contains the user's script itself.

        self._thread_pool        = tp.ThreadPool(worker_count)
        self._nb_jobs_in_flight  = 0
        self._dep_graph          = DependencyGraph(rule_set)
        self._unbuilt_leaf_nodes = set()
        self._working_dir        = working_dir
        self._successful         = None


    def build(self, targets):
        """Build the specified `targets`. Returns whether the build succeeded (no errors occurred).
        Also changes the current directory to `self._working_dir` as a side-effect."""

        os.chdir(self._working_dir)

        self._successful = True

        for tgt in targets:
            root_node = self._dep_graph.get_or_make_node(tgt)
            self.expand(root_node)

        self._thread_pool.start()

        while True:
            self._enqueue_jobs()

            assert self._nb_jobs_in_flight >= 0, "nb_jobs_in_flight cannot be negative"

            if self._nb_jobs_in_flight == 0:
                break

            self._dequeue_job_results()

        self._thread_pool.stop()
        return self._successful


    def expand(self, node):
        """TODO"""
        new_leaves = self._dep_graph.expand_dependency_subgraph(node)
        # TODO maybe instead pass our `set` to `expand_dependency_subgraph` to be modified?
        self._unbuilt_leaf_nodes |= new_leaves


    def _enqueue_jobs(self):
        while len(self._unbuilt_leaf_nodes) > 0:
            node = self._unbuilt_leaf_nodes.pop()

            if not node.rule.has_recipe():
                if False:
                    print(f"No recipe for target {node.rule.tgt.id}")

                node.job_status = JobStatus.SUCCESS
                self._on_node_succeeded(node)

            elif node.has_failed_successor():
                print(f"Cannot build target {node.rule.tgt.id}: target has failed dependencies")
                node.job_status = JobStatus.FAILURE
                self._on_node_failed(node)

            else:
                # A target must be built when it's never been built or when one of its dependencies
                # is more recent than it
                datedness = node.datedness()

                if datedness is Datedness.UP_TO_DATE:
                    print(f"Skipping up-to-date target {node.rule.tgt.id}")
                    node.job_status = JobStatus.SKIPPED
                    self._on_node_succeeded(node)

                else:
                    if datedness is Datedness.NEVER_BUILT:
                        print(f"Building target {node.rule.tgt.id}")
                    elif datedness is Datedness.OUT_OF_DATE:
                        print(f"Rebuilding out-of-date target {node.rule.tgt.id}")

                    self._thread_pool.push_job(_GxJob(node))
                    self._nb_jobs_in_flight += 1


    def _dequeue_job_results(self):
        while True:
            job_result = self._thread_pool.pop_result(block=True, timeout=0.02)
            if job_result is None:
                break

            self._nb_jobs_in_flight -= 1
            completed_node = job_result.job.node
            completed_node.job_result = job_result

            if job_result.is_success():
                completed_node.job_status = JobStatus.SUCCESS
                print(f"Built target {completed_node.rule.tgt.id}")
                self._on_node_succeeded(completed_node)
            else:
                self._successful = False
                completed_node.job_status = JobStatus.FAILURE
                print(f"Recipe failed for target {completed_node.rule.tgt.id}: {job_result.error}")
                self._on_node_failed(completed_node)

            # TODO maybe do sthg more with `job_result.value`?


    def _on_node_failed(self, node):
        #node.rule.on_failure(self, node)
        for p in node.predecessors:
            self._refresh_leaf_status(p)


    def _on_node_succeeded(self, node):
        node.rule.on_success(self, node, node.job_value())
        for p in node.predecessors:
            self._refresh_leaf_status(p)


    def _refresh_leaf_status(self, node):
        if node.all_successors_done():
            self._unbuilt_leaf_nodes.add(node)
