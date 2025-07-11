"""Telegram bot API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from app.services.telegram_service import TelegramService
from app.models.schemas import TelegramUpdate, TelegramResponse

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_telegram_service(request: Request) -> TelegramService:
    """Dependency to get Telegram service from app state."""
    if hasattr(request.app.state, 'telegram_service'):
        return request.app.state.telegram_service
    raise HTTPException(status_code=503, detail="Telegram service not available")


@router.post("/webhook")
async def telegram_webhook(
    update_data: Dict[str, Any],
    request: Request,
    telegram_service: TelegramService = Depends(get_telegram_service)
):
    """Handle Telegram webhook updates."""
    try:
        await telegram_service.process_update(update_data)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/send_message")
async def send_message(
    chat_id: int,
    message: str,
    request: Request,
    telegram_service: TelegramService = Depends(get_telegram_service)
):
    """Send a message via Telegram bot."""
    try:
        if telegram_service.bot:
            await telegram_service.bot.send_message(chat_id=chat_id, text=message)
            return {"status": "sent"}
        else:
            raise HTTPException(status_code=503, detail="Bot not initialized")
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")


@router.get("/webhook_info")
async def get_webhook_info(
    request: Request,
    telegram_service: TelegramService = Depends(get_telegram_service)
):
    """Get webhook information."""
    try:
        if telegram_service.bot:
            webhook_info = await telegram_service.bot.get_webhook_info()
            return {
                "url": webhook_info.url,
                "has_custom_certificate": webhook_info.has_custom_certificate,
                "pending_update_count": webhook_info.pending_update_count,
                "last_error_date": webhook_info.last_error_date,
                "last_error_message": webhook_info.last_error_message,
                "max_connections": webhook_info.max_connections,
                "allowed_updates": webhook_info.allowed_updates
            }
        else:
            raise HTTPException(status_code=503, detail="Bot not initialized")
    except Exception as e:
        logger.error(f"Failed to get webhook info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get webhook info")


@router.post("/set_webhook")
async def set_webhook(
    webhook_url: str,
    request: Request,
    telegram_service: TelegramService = Depends(get_telegram_service)
):
    """Set Telegram webhook URL."""
    try:
        if telegram_service.bot:
            await telegram_service.bot.set_webhook(url=webhook_url)
            return {"status": "webhook_set", "url": webhook_url}
        else:
            raise HTTPException(status_code=503, detail="Bot not initialized")
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to set webhook")


@router.delete("/webhook")
async def delete_webhook(
    request: Request,
    telegram_service: TelegramService = Depends(get_telegram_service)
):
    """Delete Telegram webhook."""
    try:
        if telegram_service.bot:
            await telegram_service.bot.delete_webhook()
            return {"status": "webhook_deleted"}
        else:
            raise HTTPException(status_code=503, detail="Bot not initialized")
    except Exception as e:
        logger.error(f"Failed to delete webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete webhook")


@router.get("/bot_info")
async def get_bot_info(
    request: Request,
    telegram_service: TelegramService = Depends(get_telegram_service)
):
    """Get bot information."""
    try:
        if telegram_service.bot:
            me = await telegram_service.bot.get_me()
            return {
                "id": me.id,
                "username": me.username,
                "first_name": me.first_name,
                "can_join_groups": me.can_join_groups,
                "can_read_all_group_messages": me.can_read_all_group_messages,
                "supports_inline_queries": me.supports_inline_queries
            }
        else:
            raise HTTPException(status_code=503, detail="Bot not initialized")
    except Exception as e:
        logger.error(f"Failed to get bot info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get bot info")