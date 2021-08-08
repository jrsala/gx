import re
import subprocess


def sh(cmd, **kwargs):
    """Convenience function for invoking shell commands"""
    print(cmd)
    completed_process = subprocess.run(cmd, shell=True, **kwargs)
    completed_process.check_returncode()
    return completed_process


###################################################################################################
# PARSING OF `gcc -MM` OUTPUT
###################################################################################################

_G_MAKE_OBJECT_FILE_DEPS_REGEXP = re.compile(
    r"\S+?\.o:[\s\\]*\S+?\.cpp(?:[\s\\\r\n]*[^\s\n\r\\]+)*\s*",
    re.ASCII
)

_G_MAKE_OBJECT_FILE_DEPS_PARSING_REGEXP = re.compile(r"[^\s\n\r\\:]+", re.ASCII)


class ObjectFileDeps:
    def __init__(self, object_filename, cpp_filename, header_filenames):
        self.object_filename  = object_filename
        self.cpp_filename     = cpp_filename
        self.header_filenames = header_filenames

    def __str__(self):
        sep = " \\\n "
        return f"{self.object_filename}: {self.cpp_filename}{sep}{sep.join(self.header_filenames)}"


def parse_object_file_make_deps(input_string):
    if _G_MAKE_OBJECT_FILE_DEPS_REGEXP.fullmatch(input_string) is None:
        raise ValueError(f"Invalid or unsupported Make object file rule:\n\"{input_string}\"")

    # Find all filenames that occur in the `input_string`
    lst = _G_MAKE_OBJECT_FILE_DEPS_PARSING_REGEXP.findall(input_string)

    assert len(lst) >= 2, "The object file should depend at least on the .cpp file"
    assert len(lst[0]) > 2, "The object file name should be of length 3 or more"
    assert lst[0][-2:] == ".o", "The object file name should end in \".o\""

    return ObjectFileDeps(lst[0], lst[1], lst[2:])


