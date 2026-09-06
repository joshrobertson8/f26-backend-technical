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

