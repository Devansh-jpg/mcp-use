"""
Unit tests for mcp_use.errors.error_formatting.format_error.
"""

import traceback

import pytest

from mcp_use.errors.error_formatting import format_error


class TestFormatError:
    """Tests for the format_error utility."""

    def test_basic_fields_present(self):
        """format_error must always return error, details, stack, and code keys."""
        error = ValueError("something went wrong")
        result = format_error(error)

        assert "error" in result
        assert "details" in result
        assert "stack" in result
        assert "code" in result

    def test_error_type_name(self):
        """'error' field must be the exception class name."""
        result = format_error(TypeError("bad type"))
        assert result["error"] == "TypeError"

    def test_details_is_str_representation(self):
        """'details' must be str(error)."""
        result = format_error(ValueError("boom"))
        assert result["details"] == "boom"

    def test_extra_context_merged(self):
        """Keyword arguments are merged into the result dict."""
        result = format_error(RuntimeError("err"), tool="my_tool", server="s1")
        assert result["tool"] == "my_tool"
        assert result["server"] == "s1"

    def test_code_from_exception_attribute(self):
        """'code' is read from the exception's own .code attribute when present."""

        class CodedError(Exception):
            code = 42

        result = format_error(CodedError("coded"))
        assert result["code"] == 42

    def test_code_defaults_to_unknown(self):
        """'code' defaults to 'UNKNOWN' when the exception has no .code attribute."""
        result = format_error(ValueError("no code here"))
        assert result["code"] == "UNKNOWN"

    # -------------------------------------------------------------------------
    # The regression: stack must come from the exception object, not sys.exc_info
    # -------------------------------------------------------------------------

    def test_stack_contains_exception_traceback(self):
        """'stack' must reflect the traceback attached to the passed-in exception.

        Regression test for the original bug where traceback.format_exc() was
        used instead of traceback.format_exception(..., error.__traceback__).
        format_exc() reads sys.exc_info() — the *currently handled* exception —
        so it returned the wrong (or empty) traceback whenever format_error was
        called outside the except block that raised `error`.
        """
        # Raise and catch an exception so it has a real __traceback__
        try:
            raise RuntimeError("original error")
        except RuntimeError as exc:
            captured_error = exc

        # Call format_error *outside* any except block — sys.exc_info() is now
        # (None, None, None), but the exception still has its __traceback__.
        result = format_error(captured_error)

        assert "RuntimeError" in result["stack"]
        assert "original error" in result["stack"]
        # Must NOT be the useless sentinel returned when there is no active exception
        assert "NoneType: None" not in result["stack"]

    def test_stack_uses_passed_error_not_current_handler(self):
        """format_error must format `error`, not whatever exception is currently active.

        If two exceptions are raised in sequence and format_error is called while
        the second one is the active handler, the stack should still describe the
        first exception (the one passed as the argument).
        """
        try:
            raise ValueError("error A")
        except ValueError as exc_a:
            error_a = exc_a

        try:
            raise TypeError("error B")
        except TypeError:
            # While error B is the active exception, format error A
            result = format_error(error_a)

        # The stack must describe error A, not the currently active error B
        assert "ValueError" in result["stack"]
        assert "error A" in result["stack"]
        assert "TypeError" not in result["stack"]

    def test_stack_is_string(self):
        """'stack' field must be a plain string (joinable, loggable)."""
        try:
            raise KeyError("missing")
        except KeyError as exc:
            result = format_error(exc)

        assert isinstance(result["stack"], str)
        assert len(result["stack"]) > 0
