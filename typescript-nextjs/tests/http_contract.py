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

