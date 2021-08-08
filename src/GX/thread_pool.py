import queue as mqueue
import threading


class Job:
    """Base class for jobs (doesn't have to be inherited from)."""
    def __init__(self, function):
        self.function = function


class JobResult:
    """Output of the queue once a `Job` has run to completion. A `JobResult` contains
        `job` - the `Job` that yielded this result
        `value` - the return value of the job's `function`, if any
        `error` - the `Exception` raised by the job's `function` if any, or some error message
    """
    def __init__(self, job, value, error):
        self.job   = job
        self.value = value
        self.error = error

    def is_success(self):
        return self.error is None

    def is_failure(self):
        return not self.is_success()


class ThreadPool:
    """A generic thread pool. `Job`s can be enqueued with `push_job` and `JobResult`s come out the
    other end with `pop_result`."""

    _STOP_SIGNAL = object()

    def __init__(self, thread_count):
        assert isinstance(thread_count, int) and thread_count > 0, \
               "Invalid thread_count argument %s" % thread_count

        self.thread_count = thread_count

        self._threads       = [threading.Thread(target=self._do_work) for _ in range(thread_count)]
        self._jobs_queue    = mqueue.SimpleQueue()
        self._results_queue = mqueue.SimpleQueue()

    def start(self):
        for t in self._threads:
            t.start()

    def stop(self):
        for _ in self._threads:
            self._jobs_queue.put(ThreadPool._STOP_SIGNAL)

        for t in self._threads:
            t.join()

    def push_job(self, job):
        return self._jobs_queue.put(job)

    def pop_result(self, block=True, timeout=None):
        """Returns a `JobResult` if there's an element in the queue (or if one is added within
        `timeout` seconds) or `None` otherwise."""
        try:
            return self._results_queue.get(block=block, timeout=timeout)
        except mqueue.Empty:
            return None

    def _do_work(self):
        while True:
            job = self._jobs_queue.get()

            if job is ThreadPool._STOP_SIGNAL:
                break

            try:
                value = job.function()
                exc   = None
            except Exception as e:
                value = None
                exc   = e

            self._results_queue.put(JobResult(job, value, exc))
