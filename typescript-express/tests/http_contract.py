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

