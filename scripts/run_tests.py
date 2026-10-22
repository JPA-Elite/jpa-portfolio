import io
import os
import sys
import unittest
from collections import OrderedDict
from contextlib import redirect_stderr, redirect_stdout


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)


class ModuleTestResult(unittest.TextTestResult):
    STATUS_PRIORITY = {"Passed": 0, "Failed": 1, "Error": 2}

    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.module_statuses = OrderedDict()

    def module_name(self, test):
        module = getattr(test.__class__, "__module__", "")
        if module == "unittest.loader" or not module:
            identifier = test.id().split("._FailedTest.", 1)[-1]
            parts = identifier.split(".")
            return parts[-1] if parts else "discovery"
        return module.rsplit(".", 1)[-1]

    def record_status(self, test, status):
        module = self.module_name(test)
        current = self.module_statuses.get(module)
        if current is None or self.STATUS_PRIORITY[status] > self.STATUS_PRIORITY[current]:
            self.module_statuses[module] = status

    def startTest(self, test):
        super().startTest(test)
        self.module_statuses.setdefault(self.module_name(test), "Passed")

    def addSuccess(self, test):
        super().addSuccess(test)
        self.record_status(test, "Passed")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.record_status(test, "Failed")

    def addError(self, test, err):
        super().addError(test, err)
        self.record_status(test, "Error")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.record_status(test, "Passed")

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.record_status(test, "Passed")

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.record_status(test, "Failed")


def print_failure_details(result):
    entries = [("FAILED", result.failures), ("ERROR", result.errors)]
    for label, items in entries:
        for test, trace in items:
            print()
            print(f"{label}: {test.id()}")
            print(trace.rstrip())


def main():
    suite = unittest.defaultTestLoader.discover("tests", pattern="test_*.py")
    captured = io.StringIO()
    with redirect_stdout(captured), redirect_stderr(captured):
        result = unittest.TextTestRunner(
            stream=captured,
            verbosity=0,
            resultclass=ModuleTestResult,
        ).run(suite)

    rows = sorted(result.module_statuses.items())

    print("API TEST")
    print("--------")
    for index, (module, status) in enumerate(rows, start=1):
        print(f"{index}. {module} => {status}")

    failed = sum(1 for _, status in rows if status == "Failed")
    errors = sum(1 for _, status in rows if status == "Error")
    success = sum(1 for _, status in rows if status == "Passed")

    print()
    print(f"Result: failed {failed}, success {success}, error {errors}")

    if result.failures or result.errors:
        print_failure_details(result)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
