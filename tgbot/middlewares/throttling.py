import time
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import Message


def rate_limit(limit: float, key: Optional[str] = None):
    """
    Decorator for configuring a rate limit and key on a handler function.
    :param limit: Throttling limit in seconds
    :param key: Unique throttling key; if None, uses handler's function name
    """
    def decorator(func: Callable):
        setattr(func, 'throttling_rate_limit', limit)
        if key:
            setattr(func, 'throttling_key', key)
        return func
    return decorator


class ThrottlingMiddleware(BaseMiddleware):
    """
    Simple throttling middleware for aiogram v3.
    - Tracks the last call time for each throttling key.
    - If a user calls the same key again too quickly, it
      sends a warning and returns early (skips the handler).
    """

    def __init__(self, limit: float = 0.5, key_prefix: str = 'antiflood_'):
        super().__init__()
        self.rate_limit = limit
        self.key_prefix = key_prefix

        # Maps throttling key -> last call time
        self._last_call: Dict[str, float] = {}
        # Maps throttling key -> how many times in a row we exceeded the rate
        self._exceeded_counts: Dict[str, int] = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # In aiogram v3, data["handler"] is a HandlerObject; we can access the real callback:
        handler_obj = data.get("handler")

        if handler_obj and hasattr(handler_obj, "callback"):
            callback = handler_obj.callback
            limit = getattr(callback, "throttling_rate_limit", self.rate_limit)
            default_key = f"{self.key_prefix}_{callback.__name__}"
            key = getattr(callback, "throttling_key", default_key)
        else:
            limit = self.rate_limit
            key = f"{self.key_prefix}_message"

        now = time.time()
        last_time = self._last_call.get(key, 0)
        elapsed = now - last_time

        # If this call is happening sooner than "limit" seconds since the last time:
        if elapsed < limit:
            exceeded_count = self._exceeded_counts.get(key, 0) + 1
            self._exceeded_counts[key] = exceeded_count
            # **Skip** calling the handler
            await self.message_throttled(event, exceeded_count)
            return  # <- This early return cancels the original handler call.

        # Otherwise, record the call time and reset exceeded count
        self._last_call[key] = now
        self._exceeded_counts[key] = 0

        # Call the original handler if we're not throttled
        return await handler(event, data)

    async def message_throttled(self, message: Message, exceeded_count: int):
        # You can tailor the warning logic however you like
        if exceeded_count <= 2:
            await message.answer("Too many requests! Please slow down.")
