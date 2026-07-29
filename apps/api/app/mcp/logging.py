import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

logger = logging.getLogger("smart_dispatcher.mcp")

F = TypeVar("F", bound=Callable[..., Any])


def log_tool_call(tool_name: str) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            started_at = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                success = bool(result.get("success")) if isinstance(result, dict) else True
                return result
            except Exception:
                logger.exception("[MCP] Tool failed: %s", tool_name)
                raise
            finally:
                elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
                result_label = "SUCCESS" if "success" in locals() and success else "FAILURE"
                logger.info(
                    "\n".join(
                        [
                            "[MCP]",
                            f"Tool:\n{tool_name}",
                            f"Arguments:\nargs={args}, kwargs={kwargs}",
                            f"Execution time:\n{elapsed_ms} ms",
                            f"Result:\n{result_label}",
                        ]
                    )
                )

        return cast(F, wrapper)

    return decorator

