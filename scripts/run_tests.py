import io
import os
import shutil
import sys
import time
import unittest
from collections import OrderedDict
from contextlib import redirect_stderr, redirect_stdout


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)


GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
GRAY = "\033[90m"
RESET = "\033[0m"

PASS_SYMBOL = "✓"
FAIL_SYMBOL = "✘"
SKIP_SYMBOL = "-"
BAR_FULL = "█"
BAR_EMPTY = "░"
BAR_WIDTH = 24


def _supports_unicode(stream):
    encoding = getattr(stream, "encoding", "") or "ascii"
    try:
        for symbol in (PASS_SYMBOL, FAIL_SYMBOL, "›", BAR_FULL, BAR_EMPTY):
            symbol.encode(encoding)
    except (LookupError, UnicodeEncodeError):
        return False
    return True


def describe_test(test):
    test_class = test.__class__
    module_name = getattr(test_class, "__module__", "") or ""
    if module_name == "unittest.loader":
        return "discovery", test.id()
    module = sys.modules.get(module_name)
    path = getattr(module, "__file__", "") or ""
    if path:
        path = os.path.relpath(path, ROOT).replace("\\", "/")
    else:
        path = module_name.replace(".", "/") or "unknown"
    method = getattr(test, "_testMethodName", "")
    if method:
        name = f"{test_class.__name__}.{method}"
    else:
        try:
            name = test.id()
        except Exception:
            name = test_class.__name__
    return path, name


class TestProgress:
    def __init__(self, stream, total):
        self.stream = stream
        self.total = total
        self.completed = 0
        self.isatty = bool(getattr(stream, "isatty", lambda: False)())
        self.color = bool(self.isatty and not os.getenv("NO_COLOR"))
        self.unicode = _supports_unicode(stream)
        self.status_visible = False
        self.status_width = 0
        if os.name == "nt" and self.color:
            os.system("")

    def paint(self, text, color):
        if not self.color or not color:
            return text
        return f"{color}{text}{RESET}"

    def symbol(self, status):
        if status == "Passed":
            mark = PASS_SYMBOL if self.unicode else "PASS"
            return self.paint(mark, GREEN)
        if status == "Skipped":
            mark = SKIP_SYMBOL if self.unicode else "SKIP"
            return self.paint(mark, YELLOW)
        mark = FAIL_SYMBOL if self.unicode else "FAIL"
        return self.paint(mark, RED)

    def divider(self):
        return "›" if self.unicode else ">"

    def bar(self):
        ratio = self.completed / self.total if self.total else 0
        filled = int(round(ratio * BAR_WIDTH))
        filled = max(0, min(BAR_WIDTH, filled))
        full, empty = (BAR_FULL, BAR_EMPTY) if self.unicode else ("#", "-")
        return full * filled + empty * (BAR_WIDTH - filled)

    def clear_status(self):
        if not self.status_visible:
            return
        self.stream.write("\r" + " " * self.status_width + "\r")
        self.stream.flush()
        self.status_visible = False
        self.status_width = 0

    def write_line(self, text):
        self.clear_status()
        self.stream.write(text + "\n")
        self.stream.flush()

    def status(self, label):
        if not self.isatty:
            return
        percent = int(self.completed * 100 / self.total) if self.total else 0
        text = (
            f"  {self.bar()} {self.completed}/{self.total} "
            f"{percent:3d}%  {self.divider()} {label}"
        )
        columns = shutil.get_terminal_size((120, 20)).columns
        if columns > 4 and len(text) > columns - 1:
            text = text[: columns - 2] + "…" if self.unicode else text[: columns - 1]
        self.clear_status()
        self.stream.write(text)
        self.stream.flush()
        self.status_visible = True
        self.status_width = len(text)

    def test_line(self, test, status, duration):
        self.completed += 1
        path, name = describe_test(test)
        duration_text = f"{duration * 1000:.0f}ms" if duration < 1 else f"{duration:.2f}s"
        counter = f"{self.completed:>{len(str(self.total))}}"
        line = "  {} {} {} {} {} {}".format(
            self.symbol(status),
            counter,
            self.paint("[api]", GRAY),
            self.paint(path, GRAY),
            self.divider(),
            f"{name} {self.paint(f'({duration_text})', GRAY)}",
        )
        self.write_line(line)


class ModuleTestResult(unittest.TextTestResult):
    STATUS_PRIORITY = {"Passed": 0, "Skipped": 1, "Failed": 2, "Error": 3}
    progress = None

    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.module_statuses = OrderedDict()
        self.started_at = {}
        self.subtest_statuses = {}
        self.counts = {"Passed": 0, "Failed": 0, "Error": 0, "Skipped": 0}

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
        self.started_at[test.id()] = time.perf_counter()
        if self.progress is not None:
            self.progress.status(describe_test(test)[1])

    def finishTest(self, test, status):
        started = self.started_at.pop(test.id(), None)
        self.subtest_statuses.pop(test.id(), None)
        duration = time.perf_counter() - started if started is not None else 0.0
        self.counts[status] = self.counts.get(status, 0) + 1
        self.record_status(test, status)
        if self.progress is not None:
            self.progress.test_line(test, status, duration)

    def stopTest(self, test):
        super().stopTest(test)
        if test.id() in self.started_at:
            self.finishTest(test, self.subtest_statuses.get(test.id(), "Passed"))

    def addSuccess(self, test):
        super().addSuccess(test)
        self.finishTest(test, "Passed")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.finishTest(test, "Failed")

    def addError(self, test, err):
        super().addError(test, err)
        self.finishTest(test, "Error")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.finishTest(test, "Skipped")

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.finishTest(test, "Passed")

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.finishTest(test, "Failed")

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is None:
            return
        status = "Failed"
        if not issubclass(err[0], test.failureException):
            status = "Error"
        current = self.subtest_statuses.get(test.id())
        if current is None or self.STATUS_PRIORITY[status] > self.STATUS_PRIORITY[current]:
            self.subtest_statuses[test.id()] = status
        self.record_status(test, status)


def print_failure_details(result):
    entries = [("FAILED", result.failures), ("ERROR", result.errors)]
    for label, items in entries:
        for test, trace in items:
            print()
            print(f"{label}: {test.id()}")
            print(trace.rstrip())


def print_module_summary(result):
    rows = sorted(result.module_statuses.items())
    print("API TEST")
    print("--------")
    for index, (module, status) in enumerate(rows, start=1):
        print(f"{index}. {module} => {status}")


def main():
    suite = unittest.defaultTestLoader.discover("tests", pattern="test_*.py")
    progress = TestProgress(sys.stdout, suite.countTestCases())
    ModuleTestResult.progress = progress

    print(f"Running {progress.total} tests using 1 worker")
    print()

    captured = io.StringIO()
    started_at = time.perf_counter()
    with redirect_stdout(captured), redirect_stderr(captured):
        result = unittest.TextTestRunner(
            stream=captured,
            verbosity=0,
            resultclass=ModuleTestResult,
        ).run(suite)
    elapsed = time.perf_counter() - started_at
    progress.clear_status()

    print()
    print_module_summary(result)

    failed = sum(1 for _, status in result.module_statuses.items() if status == "Failed")
    errors = sum(1 for _, status in result.module_statuses.items() if status == "Error")
    success = sum(1 for _, status in result.module_statuses.items() if status == "Passed")

    print()
    print(f"Result: failed {failed}, success {success}, error {errors}")

    if result.failures or result.errors:
        print_failure_details(result)

    print()
    passed_count = result.counts["Passed"]
    skipped_count = result.counts["Skipped"]
    if progress.color:
        summary = progress.paint(f"{passed_count} passed", GREEN)
        if failed or errors:
            summary += " " + progress.paint(f"{failed + errors} failed", RED)
        if skipped_count:
            summary += " " + progress.paint(f"{skipped_count} skipped", YELLOW)
        summary += " " + progress.paint(f"({elapsed:.2f}s)", GRAY)
    else:
        summary = f"{passed_count} passed"
        if failed or errors:
            summary += f" {failed + errors} failed"
        if skipped_count:
            summary += f" {skipped_count} skipped"
        summary += f" ({elapsed:.2f}s)"
    print(f"  {summary}")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
