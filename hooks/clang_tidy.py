#!/usr/bin/env python3
"""Wrapper script for clang-tidy."""

import re
import sys
from typing import List
import multiprocessing as mp
import copy

from hooks.utils import StaticAnalyzerCmd

class ClangTidyCmd(StaticAnalyzerCmd):
    """Class for the clang-tidy command."""

    command = "clang-tidy"
    lookbehind = "LLVM version "

    def __init__(self, args: List[str]):
        super().__init__(self.command, self.lookbehind, args)
        self.parse_args(args)
        self.edit_in_place = "-fix" in self.args or "--fix-errors" in self.args

    def tidy_file(self, filename: str):
        worker = copy.copy(super())
        worker.run_command([filename] + worker.args)
        # Warnings generated aren't important.
        worker.stderr = re.sub(rb"[\d,]+ warning \S+\s+", b"", worker.stderr)
        if len(worker.stderr) > 0 and "--fix-errors" in worker.args:
            worker.returncode = 1
        return worker.returncode, worker.stdout, worker.stderr

    def run(self):
        """Run clang-tidy. If --fix-errors is passed in, then return code will be 0, even if there are errors."""
        with mp.Pool(mp.cpu_count()) as p:
            results = p.map(self.tidy_file, self.files)
            ret_codes, stdouts, stderrs = zip(*results)

            self.returncode = max(ret_codes)
            self.stdout = b"\n".join(stdouts)
            self.stderr = b"\n".join(stderrs)
            self.exit_on_error()

def main(argv: List[str] = sys.argv):
    cmd = ClangTidyCmd(argv)
    cmd.run()

if __name__ == "__main__":
    main()

