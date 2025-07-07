from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from loguru import logger


class ErrorHandlerMiddleware(BaseMiddleware):
    """Middleware для обработки ошибок"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Error in handler: {e}")
            
            # Отправляем сообщение об ошибке пользователю
            if isinstance(event, Message):
                await event.answer("❌ Произошла ошибка. Попробуйте позже.")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)
            
            # Пробрасываем ошибку дальше для логирования
            raise 