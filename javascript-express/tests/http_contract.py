#!/usr/bin/env python3
"""Black-box contract tests; Python 3.9+ standard library, no test packages."""
import argparse
import contextlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import unittest
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import uuid4

BASE_URL = ""
USERS = [
    {"id": "u1", "name": "Ada"},
    {"id": "u2", "name": "Grace"},
    {"id": "u3", "name": "Linus"},
]


def request(method, path, body=None, raw=None):
    payload = (
        raw
        if raw is not None
        else (json.dumps(body).encode() if body is not None else None)
    )
    req = Request(
        BASE_URL + path,
        data=payload,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        response = urlopen(req, timeout=30)
    except HTTPError as error:
        response = error
    with response:
        data = response.read()
        try:
            parsed = json.loads(data) if data else None
        except (ValueError, UnicodeDecodeError):
            parsed = data.decode(errors="replace")
        return response.status, parsed, data


class ApiTest(unittest.TestCase):
    longMessage = False

    def assertEqual(self, received, expected, msg=None):
        try:
            super().assertEqual(received, expected, msg)
        except self.failureException:
            if msg is not None:
                raise

            expected_text = json.dumps(expected, indent=2, ensure_ascii=False, default=str)
            received_text = json.dumps(received, indent=2, ensure_ascii=False, default=str)
            raise self.failureException(
                f"Expected:\n{expected_text}\n\nReceived:\n{received_text}"
            ) from None

    def setUp(self):
        self.created_ids = []

    def tearDown(self):
        for event_id in self.created_ids:
            request("DELETE", self.path(event_id))

    @staticmethod
    def path(event_id):
        return "/api/events/" + quote(event_id, safe="")

    def call(self, method, path, expected, body=None, raw=None):
        status, data, wire = request(method, path, body, raw)
        self.assertEqual(
            status,
            expected,
            f"Request:  {method} {path}\n"
            f"Expected: HTTP {expected}\n"
            f"Received: HTTP {status}\n"
            f"Response: {json.dumps(data, ensure_ascii=False)}",
        )
        if expected == 204:
            self.assertEqual(wire, b"", "204 responses must have no body")
        if expected >= 400:
            self.assertIsInstance(data, dict)
            self.assertIsInstance(data.get("error"), str)
            self.assertTrue(data["error"].strip())
        return data

    def create(self, body=None):
        body = (
            body
            if body is not None
            else {
                "title": "Team dinner",
                "description": "Friday evening",
                "inviteeIds": ["u1", "u2"],
            }
        )
        event = self.call("POST", "/api/events", 201, body)
        self.assertIsInstance(event, dict)
        self.assertIsInstance(event.get("id"), str)
        self.assertTrue(event["id"])
        self.created_ids.append(event["id"])
        self.assert_event(event, event["id"], body)
        return event

    def assert_event(self, event, event_id, body):
        self.assertEqual(
            event,
            {
                "id": event_id,
                "title": body["title"],
                "description": body.get("description", ""),
                "inviteeIds": body.get("inviteeIds", []),
            },
        )


class ScaffoldTests(ApiTest):
    def test_health(self):
        """Health endpoint responds"""
        self.assertEqual(self.call("GET", "/api/health", 200), {"status": "ok"})

    def test_seeded_users(self):
        """Seeded users are available"""
        users = self.call("GET", "/api/users", 200)
        self.assertEqual(sorted(users, key=lambda user: user["id"]), USERS)

    def test_request_shape_rejected_before_service(self):
        """Invalid request fields return 400"""
        invalid = [
            {},
            {"title": ""},
            {"title": " \t\n"},
            {"title": None},
            {"title": 42},
            {"title": True},
            {"title": "Dinner", "description": None},
            {"title": "Dinner", "description": 12},
            {"title": "Dinner", "inviteeIds": None},
            {"title": "Dinner", "inviteeIds": "u1"},
            {"title": "Dinner", "inviteeIds": [3]},
            {"title": "Dinner", "inviteeIds": [None]},
            {"title": "Dinner", "id": "client-chosen"},
            {"title": "Dinner", "extra": True},
            [],
            "string",
            42,
        ]
        for body in invalid:
            for method, path in [
                ("POST", "/api/events"),
                ("PUT", "/api/events/missing"),
            ]:
                with self.subTest(method=method, body=body):
                    self.call(method, path, 400, body)

    def test_malformed_json(self):
        """Malformed JSON returns 400"""
        for raw in [b'{"title":', b"null", b'{"title":"Dinner"} trailing']:
            for method, path in [
                ("POST", "/api/events"),
                ("PUT", "/api/events/missing"),
            ]:
                with self.subTest(method=method, raw=raw):
                    self.call(method, path, 400, raw=raw)


class CandidateTests(ApiTest):
    def test_create_event(self):
        """Create an event"""
        body = {
            "title": "  Café team dinner  ",
            "description": 'Line one\n"Bring snacks" ☕',
            "inviteeIds": ["u3", "u1", "u2"],
        }
        event = self.create(body)
        self.assert_event(event, event["id"], body)

        minimal = self.create({"title": "Minimal"})
        self.assert_event(minimal, minimal["id"], {"title": "Minimal"})

        events = [self.create({"title": f"Event {i}"}) for i in range(8)]
        created = [event, minimal] + events
        self.assertEqual(len({item["id"] for item in created}), len(created))

    def test_create_rejects_invalid_invitations(self):
        """Create rejects invalid invitations"""
        for invitees in [["no-such-user"], ["u1", "unknown"], ["u1", "u1"], [""]]:
            with self.subTest(invitees=invitees):
                self.call(
                    "POST",
                    "/api/events",
                    400,
                    {"title": "Invalid", "inviteeIds": invitees},
                )

    def test_read_event(self):
        """Read an event"""
        event = self.create()
        path = self.path(event["id"])
        self.assertEqual(self.call("GET", path, 200), event)

    def test_read_missing_event(self):
        """Read reports a missing event"""
        path = self.path("missing-" + uuid4().hex)
        self.call("GET", path, 404)

    def test_update_event(self):
        """Update an event"""
        event = self.create({"title": "Minimal"})
        other = self.create({"title": "Other event", "inviteeIds": ["u1"]})
        path = self.path(event["id"])
        populated = {
            "title": "Populated",
            "description": "Details",
            "inviteeIds": ["u2"],
        }
        self.call("PUT", path, 200, populated)
        replaced = self.call("PUT", path, 200, {"title": "Reset"})
        self.assert_event(replaced, event["id"], {"title": "Reset"})

        body = {
            "title": "  Café team dinner  ",
            "description": 'Line one\n"Bring snacks" ☕',
            "inviteeIds": ["u3", "u1", "u2"],
        }
        updated = self.call("PUT", path, 200, body)
        self.assert_event(updated, event["id"], body)

        cleared = self.call(
            "PUT",
            path,
            200,
            {"title": "Clear", "description": "", "inviteeIds": []},
        )
        self.assert_event(cleared, event["id"], {"title": "Clear"})
        self.assertEqual(self.call("GET", path, 200), cleared)
        self.assertEqual(self.call("GET", self.path(other["id"]), 200), other)
        self.assertEqual(
            sorted(self.call("GET", "/api/users", 200), key=lambda user: user["id"]),
            USERS,
        )

    def test_update_rejects_invalid_data(self):
        """Update rejects invalid data"""
        event = self.create()
        path = self.path(event["id"])

        for invitees in [["u1", "unknown"], ["u2", "u2"], [""]]:
            with self.subTest(invitees=invitees):
                self.call(
                    "PUT",
                    path,
                    400,
                    {
                        "title": "Do not save",
                        "description": "Rejected",
                        "inviteeIds": invitees,
                    },
                )
                self.assertEqual(self.call("GET", path, 200), event)

        self.call("PUT", path, 400, {"title": "Do not save", "inviteeIds": [42]})
        self.assertEqual(self.call("GET", path, 200), event)

        missing = self.path("missing-" + uuid4().hex)
        self.call(
            "PUT", missing, 404, {"title": "Missing", "inviteeIds": ["unknown", "unknown"]}
        )

    def test_delete_event(self):
        """Delete an event"""
        body = {
            "title": "Team dinner",
            "description": "Friday evening",
            "inviteeIds": ["u1", "u2"],
        }
        event = self.create(body)
        other = self.create({"title": "Keep this event", "inviteeIds": ["u3"]})
        self.call("DELETE", self.path(event["id"]), 204)
        self.call("GET", self.path(event["id"]), 404)
        self.call("PUT", self.path(event["id"]), 404, {"title": "Deleted"})
        self.call("DELETE", self.path(event["id"]), 404)
        self.assertEqual(self.call("GET", self.path(other["id"]), 200), other)
        self.assertEqual(
            sorted(self.call("GET", "/api/users", 200), key=lambda user: user["id"]),
            USERS,
        )

        later = self.create({"title": "After delete"})
        self.assertNotEqual(later["id"], event["id"])

    def test_delete_missing_event(self):
        """Delete reports a missing event"""
        path = self.path("missing-" + uuid4().hex)
        self.call("DELETE", path, 404)


class ConsoleResult(unittest.TestResult):
    def __init__(self, verbose=False):
        super().__init__()

        self.verbose = verbose
        self.group = None
        self.passed_count = 0
        self.failed_count = 0
        self.error_count = 0
        self.skipped_count = 0
        self.saw_unimplemented_service = False

    def startTest(self, test):
        super().startTest(test)

        self.status = "PASS"
        self.details = []

        group = "Server setup"
        if isinstance(test, CandidateTests):
            method = test._testMethodName.split("_")[1]
            group = "Event service: " + method.capitalize()

        if group != self.group:
            print(f"\n{group}", flush=True)
            print("-" * len(group), flush=True)
            self.group = group

    def record_problem(self, error, status, case=None):
        if self.status != "ERROR":
            self.status = status

        message = str(error[1]) or error[0].__name__

        if "Received: HTTP 501" in message:
            self.saw_unimplemented_service = True

        if self.verbose:
            message = "".join(traceback.format_exception(*error)).rstrip()

        if case:
            message = f"Case: {case}\n{message}"

        self.details.append(message)

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.record_problem(error, "FAIL")

    def addError(self, test, error):
        super().addError(test, error)
        self.record_problem(error, "ERROR")

    def addSubTest(self, test, subtest, error):
        super().addSubTest(test, subtest, error)

        if error is None:
            return

        status = "ERROR"
        if issubclass(error[0], test.failureException):
            status = "FAIL"

        case = ", ".join(f"{key}={value!r}" for key, value in subtest.params.items())
        self.record_problem(error, status, case)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)

        if self.status == "PASS":
            self.status = "SKIP"

        self.details.append(reason)

    def addExpectedFailure(self, test, error):
        super().addExpectedFailure(test, error)
        self.status = "SKIP"
        self.details.append("Marked as an expected failure")

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.status = "FAIL"
        self.details.append("Test passed but was marked as an expected failure")

    def stopTest(self, test):
        super().stopTest(test)

        label = test.shortDescription()
        if not label:
            label = test._testMethodName.removeprefix("test_").replace("_", " ").capitalize()

        marker = f"[{self.status}]"
        print(f"  {marker:7} {label}", flush=True)

        if self.status == "PASS":
            self.passed_count += 1
        elif self.status == "FAIL":
            self.failed_count += 1
        elif self.status == "ERROR":
            self.error_count += 1
        else:
            self.skipped_count += 1

        visible_details = self.details
        if not self.verbose:
            visible_details = self.details[:3]

        for message in visible_details:
            for line in message.splitlines():
                print(f"          {line}")

        hidden = len(self.details) - len(visible_details)
        if hidden:
            print(f"          Additional details hidden: {hidden}. Use --verbose to see all.")

        if self.details:
            print(flush=True)

    def print_summary(self, elapsed):
        counts = (
            f"Passed: {self.passed_count}  |  Failed: {self.failed_count}  |  "
            f"Errors: {self.error_count}"
        )
        if self.skipped_count:
            counts += f"  |  Skipped: {self.skipped_count}"

        outcome = "PASSED" if self.wasSuccessful() else "FAILED"
        if self.wasSuccessful() and self.skipped_count:
            outcome = "FINISHED WITH SKIPS"

        print("\n" + "=" * 72)
        print(f"RESULT: {outcome}")
        print(counts)
        print(f"Total: {self.testsRun} tests  |  Time: {elapsed:.2f}s")
        print("=" * 72)

        if self.saw_unimplemented_service:
            print("\nHTTP 501 means a service method is not implemented yet.")
            print("Complete the CRUD methods in the service file, then run the tests again.")
        elif not self.wasSuccessful():
            print("\nReview the failures and errors above, then run the tests again.")
        elif self.skipped_count:
            print("\nRun complete. Some checks were skipped.")
        elif self.wasSuccessful():
            print("\nAll checks passed.")

        if self.failed_count or self.error_count:
            print("For full tracebacks: python3 tests/http_contract.py --verbose")

        print()


@contextlib.contextmanager
def running_server(base_url):
    global BASE_URL
    if base_url:
        BASE_URL = base_url.rstrip("/")
        yield
        return
    root = Path(__file__).resolve().parent.parent
    config = json.loads((root / "tests/server.json").read_text())
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    BASE_URL = f"http://127.0.0.1:{port}"
    command = [
        arg.format(python=sys.executable, port=port) for arg in config["command"]
    ]
    environment = dict(os.environ, PORT=str(port), NEXT_TELEMETRY_DISABLED="1")
    with tempfile.TemporaryFile(mode="w+b") as log:
        process = subprocess.Popen(
            command,
            cwd=root,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=os.name != "nt",
        )
        try:
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(
                        "Server exited during startup; install/build this option first"
                    )
                try:
                    if request("GET", "/api/health")[:2] == (200, {"status": "ok"}):
                        break
                except (URLError, TimeoutError, OSError):
                    pass
                time.sleep(0.15)
            else:
                raise RuntimeError("Server did not become healthy within 120 seconds")
            yield
        except Exception as error:
            log.seek(0)
            output = log.read().decode(errors="replace")[-12000:].strip()
            message = str(error)

            if output:
                message += "\n\nServer output:\n" + output

            raise RuntimeError(message) from error
        finally:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.wait(timeout=5)
                except ProcessLookupError:
                    pass
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            log.seek(0)
            server_log = log.read().decode(errors="replace")
            if any(
                marker in server_log
                for marker in [
                    "ERROR: AddressSanitizer",
                    "ERROR: LeakSanitizer",
                    "runtime error:",
                ]
            ):
                raise RuntimeError("Server sanitizer failure:\n" + server_log[-12000:])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke", action="store_true", help="Only test the supplied scaffold"
    )
    parser.add_argument(
        "--base-url", help="Use a running server instead of launching one"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show all failure details and tracebacks"
    )
    args = parser.parse_args()

    suite = unittest.TestSuite(ScaffoldTests(name) for name in [
        "test_health",
        "test_seeded_users",
        "test_malformed_json",
        "test_request_shape_rejected_before_service",
    ])

    if not args.smoke:
        suite.addTests(CandidateTests(name) for name in [
            "test_create_event",
            "test_create_rejects_invalid_invitations",
            "test_read_event",
            "test_read_missing_event",
            "test_update_event",
            "test_update_rejects_invalid_data",
            "test_delete_event",
            "test_delete_missing_event",
        ])

    project = Path(__file__).resolve().parent.parent.name
    mode = "Server setup only" if args.smoke else "Full API checks"
    print("\n" + "=" * 72, flush=True)
    print(f"Event API tests | {project}", flush=True)
    print(f"{mode} | {suite.countTestCases()} tests", flush=True)
    print("=" * 72, flush=True)

    if args.base_url:
        print(f"Using {args.base_url}", flush=True)
    else:
        print("Starting test server...", flush=True)

    result = ConsoleResult(verbose=args.verbose)

    try:
        with running_server(args.base_url):
            started = time.monotonic()
            suite.run(result)
            elapsed = time.monotonic() - started
    except Exception as error:
        print("\n" + "=" * 72)
        print("RESULT: ERROR - Test run could not finish")
        print("=" * 72)
        for line in str(error).splitlines():
            print(f"  {line}")
        if args.verbose:
            traceback.print_exc()
        print("\nCheck the install/build commands in commands.md.\n")
        return 1

    result.print_summary(elapsed)

    if result.wasSuccessful():
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
