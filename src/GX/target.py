from abc import ABCMeta, abstractmethod
import json
import os
import sys


class TargetID:
    def __init__(self, data):
        self._json = json.dumps(
            data,
            sort_keys=True,
            allow_nan=False,
            separators=(',', ':'),
            default=str
        )
        self.data = data

    def __eq__(self, other):
        return self._json == other._json

    def __hash__(self):
        return hash(self._json)

    def __str__(self):
        return self._json


class Id:
    """Marker for attributes of a `Target` instance that must be a part of the target's `id`.
    See `Target`."""

    def __init__(self, x):
        self._wrapped = x


class _TargetMeta(ABCMeta):
    def __new__(metacls, clsname, bases, attrs):
        old_init = attrs.get("__init__", None)

        if old_init is None:
            # TODO is this the right default `__init__` algorithm?
            def default_init(self, *args, **kwargs):
                for base in bases:
                    base.__init__(self, *args, **kwargs)

            old_init = default_init

        def new_init(self, *args, **kwargs):
            old_init(self, *args, **kwargs)

            # This function closes over `result_cls` which is defined below this function...
            if type(self) == result_cls:
                id_data = dict()

                for key, value in self.__dict__.items():
                    if key == "id":
                        # TODO better error type?
                        raise ValueError(
                            "`Target` instance cannot have custom attribute with reserved name "
                            "'id'"
                        )

                    if isinstance(value, Id):
                        id_data[key]       = value._wrapped
                        self.__dict__[key] = value._wrapped

                self.__dict__["id"] = TargetID(id_data)

        attrs["__init__"] = new_init
        result_cls = super().__new__(metacls, clsname, bases, attrs)
        return result_cls


class Target(metaclass=_TargetMeta):
    """Convenience base class for class-based targets (note that it is generally NOT necessary for
    a target to be an instance of this class or a subclass).

    TODO explain the `id` and stuff"""

    def __init__(self):
        self.type = Id(type(self).__name__)

    @abstractmethod
    def timestamp(self):
        """Returns the date and time when the target was last successfully built, or `None` if it
        was never run.
        TODO other possible values like `-sys.maxsize`"""
        raise NotImplemented


class PhonyTarget(Target):
    """Class for targets that do not correspond to files (and therefore have no timestamp)"""

    def timestamp(self):
        return None


class FileTarget(Target):
    """Identifies a file by its path"""

    def __init__(self, path):
        super().__init__()
        self.path = Id(path)

    def timestamp(self):
        try:
            # TODO we can do better than this
            return os.stat(self.path).st_mtime
        except FileNotFoundError:
            return None


class DirectoryTarget(FileTarget):
    """Identifies a directory"""
    def __init__(self, path):
        super().__init__(path)

    def timestamp(self):
        # TODO define a GX constant for `-sys.maxsize`
        return -sys.maxsize if self.path.is_dir() else None
