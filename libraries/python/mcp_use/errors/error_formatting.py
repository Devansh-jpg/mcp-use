import traceback

from mcp_use.logging import logger


def format_error(error: Exception, **context) -> dict:
    """
    Formats an exception into a structured format that can be understood by LLMs.

    Args:
        error: The exception to format.
        **context: Additional context to include in the formatted error.

    Returns:
        A dictionary containing the formatted error.
    """
    formatted_context = {
        "error": type(error).__name__,
        "details": str(error),
        # Use the exception object's own __traceback__ rather than
        # traceback.format_exc(), which reads sys.exc_info() and therefore
        # returns the *currently handled* exception's stack — not necessarily
        # the one passed as `error`.  This matters when format_error is called
        # after the except block, from a different exception handler, or from
        # code that has no active exception at all (where format_exc() would
        # return "NoneType: None\n").
        "stack": "".join(traceback.format_exception(type(error), error, error.__traceback__)),
        "code": getattr(error, "code", "UNKNOWN"),
    }
    formatted_context.update(context)

    logger.error(f"Structured error: {formatted_context}")  # For observability (maybe remove later)
    return formatted_context
