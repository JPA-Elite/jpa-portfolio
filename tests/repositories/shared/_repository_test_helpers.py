import importlib
import inspect
from contextlib import ExitStack
from unittest.mock import patch

from flask import Flask

from backend.Repositories.BaseRepository import BaseRepository
from tests.test_support import FakeCollection, dummy_repo_param


def _fake_get_mongo_client(self, collection_name):
    return object(), {}, FakeCollection()


def load_repository_class(module_name: str, class_name: str):
    module = importlib.import_module(f"backend.Repositories.{module_name}")
    return module, getattr(module, class_name)


def iter_repository_methods(repo_class):
    for name, fn in inspect.getmembers(repo_class, inspect.isfunction):
        if fn.__module__ != repo_class.__module__:
            continue
        if name in {"__init__", "get_mongo_client"}:
            continue
        if name.startswith("_"):
            continue
        yield name, fn


def run_repository_smoke_test(testcase, module_name: str, class_name: str):
    _, repo_class = load_repository_class(module_name, class_name)
    with patch.object(BaseRepository, "get_mongo_client", new=_fake_get_mongo_client):
        repo = repo_class()
        testcase.assertTrue(hasattr(repo, "collection"))
        testcase.assertTrue(hasattr(repo, "db"))
        testcase.assertTrue(hasattr(repo, "client"))


def _execute_repository_method(module_name: str, class_name: str, method_name: str):
    _, repo_class = load_repository_class(module_name, class_name)
    app = Flask(__name__)

    with ExitStack() as stack:
        stack.enter_context(patch.object(BaseRepository, "get_mongo_client", new=_fake_get_mongo_client))
        stack.enter_context(patch("backend.Repositories.LoginAttemptRepository.get_request_ip", return_value="127.0.0.1"))

        repo = repo_class()
        method = getattr(repo, method_name)
        method_fn = getattr(repo_class, method_name)
        sig = inspect.signature(method_fn)
        args = []
        for param_name, param in list(sig.parameters.items())[1:]:
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            if param.default is not inspect._empty:
                continue
            args.append(dummy_repo_param(param_name))

        with app.test_request_context("/"):
            result = method(*args)

    return result, args


def _assert_repository_method_contract(testcase, class_name: str, method_name: str, result):
    # explicit exceptions first
    if class_name == "AuthRepository" and method_name == "update_user":
        testcase.assertTrue(hasattr(result, "matched_count"))
        return
    if class_name in {"GalleryCommentRepository", "VlogCommentRepository"} and method_name == "update_comment":
        testcase.assertTrue(hasattr(result, "matched_count"))
        return
    if class_name == "PortfolioRepository" and method_name.startswith("insert_"):
        testcase.assertTrue(hasattr(result, "inserted_id"))
        return
    if class_name == "VisitRepository" and method_name == "delete_system_info_by_id":
        testcase.assertIsNone(result)
        return
    if class_name == "LoginAttemptRepository" and method_name in {"get_attempt_info", "update_attempt"}:
        testcase.assertIsInstance(result, dict)
        testcase.assertIn("attempts", result)
        testcase.assertIn("lockout_until", result)
        return
    if class_name == "VisitRepository" and method_name == "count_visits":
        testcase.assertIsInstance(result, dict)
        testcase.assertIn("visitor_total_count", result)
        testcase.assertIn("bot_total_count", result)
        return
    if class_name in {"VlogLikeRepository", "VlogCommentRepository"} and method_name in {
        "get_vlog_likes_counts_by_ids",
        "get_vlog_liked_states_by_ids_and_ip",
        "count_comments_by_vlog_ids",
    }:
        testcase.assertIsInstance(result, dict)
        return
    if method_name.startswith("get_") and "_count" in method_name:
        testcase.assertIsInstance(result, int)
        return

    # generic contracts by method naming
    if method_name.startswith("get_paginated_") or method_name.startswith("search_"):
        testcase.assertIsInstance(result, tuple)
        testcase.assertEqual(len(result), 2)
        testcase.assertIsInstance(result[0], list)
        testcase.assertIsInstance(result[1], int)
        return
    if method_name.startswith("get_active_"):
        testcase.assertIsInstance(result, list)
        return
    if method_name.startswith("get_all_tags"):
        testcase.assertIsInstance(result, list)
        return
    if method_name.startswith("count_"):
        testcase.assertIsInstance(result, int)
        return
    if method_name.startswith("add_many_"):
        testcase.assertIsInstance(result, list)
        return
    if method_name.startswith("add_"):
        testcase.assertIsInstance(result, str)
        return
    if method_name.startswith("update_"):
        testcase.assertIsInstance(result, bool)
        return
    if method_name.startswith("delete_"):
        testcase.assertIsInstance(result, bool)
        return
    if method_name.startswith("find_") or method_name.startswith("get_"):
        # repository "get_*_by_id" / "find_by_*" methods generally return a document dict
        testcase.assertTrue(result is None or isinstance(result, dict) or isinstance(result, list))
        return
    if method_name.startswith("insert_"):
        testcase.assertTrue(hasattr(result, "inserted_id"))
        return

    testcase.fail(f"No repository contract assertion configured for {class_name}.{method_name}")


def attach_repository_contract_tests(test_class, module_name: str, class_name: str):
    """Attach one unittest method per public repository method (individual coverage)."""
    _, repo_class = load_repository_class(module_name, class_name)

    for method_name, _ in iter_repository_methods(repo_class):
        test_name = f"test_contract_{method_name}"
        if hasattr(test_class, test_name):
            continue

        def _generated_test(self, _method_name=method_name):
            result, _args = _execute_repository_method(module_name, class_name, _method_name)
            _assert_repository_method_contract(self, class_name, _method_name, result)

        _generated_test.__name__ = test_name
        setattr(test_class, test_name, _generated_test)


def run_repository_methods_test(testcase, module_name: str, class_name: str):
    _, repo_class = load_repository_class(module_name, class_name)
    app = Flask(__name__)

    executed = []
    failures = []

    with ExitStack() as stack:
        stack.enter_context(patch.object(BaseRepository, "get_mongo_client", new=_fake_get_mongo_client))
        stack.enter_context(patch("backend.Repositories.LoginAttemptRepository.get_request_ip", return_value="127.0.0.1"))

        repo = repo_class()
        for method_name, method in iter_repository_methods(repo_class):
            sig = inspect.signature(method)
            args = []
            for param_name, param in list(sig.parameters.items())[1:]:
                if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                    continue
                if param.default is not inspect._empty:
                    continue
                args.append(dummy_repo_param(param_name))

            try:
                with app.test_request_context("/"):
                    getattr(repo, method_name)(*args)
                executed.append(method_name)
            except Exception as exc:
                failures.append(f"{class_name}.{method_name}: {exc}")

    if failures:
        testcase.fail("Repository method execution failures:\n" + "\n".join(failures))
    testcase.assertGreater(len(executed), 0, f"No methods executed for {class_name}")
