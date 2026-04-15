"""Voice message transcription via VOSK SERVER."""

import json
import logging
import tempfile
from pathlib import Path

import httpx

import config

logger = logging.getLogger("voice")


async def transcribe_voice(voice, bot) -> str | None:
    """Download voice message and transcribe via VOSK SERVER.

    Args:
        voice: aiogram Voice or Audio object
        bot: aiogram Bot instance

    Returns:
        Transcribed text, error message, or None if not configured
    """
    if not config.VOSK_SERVER_HOST or not config.VOSK_SERVER_PORT:
        return None

    tmp_path = None
    try:
        # Download voice file from Telegram
        file = await bot.get_file(voice.file_id)
        tmp_path = Path(tempfile.gettempdir()) / f"qwenbot_voice_{voice.file_id}.ogg"
        await bot.download_file(file.file_path, destination=str(tmp_path))

        # Convert OGG to WAV (Vosk expects WAV 16kHz mono 16-bit)
        wav_path = tmp_path.with_suffix(".wav")
        proc = await __import__("asyncio").create_subprocess_exec(
            "ffmpeg", "-y", "-i", str(tmp_path),
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
            str(wav_path),
            stdout=__import__("asyncio").subprocess.PIPE,
            stderr=__import__("asyncio").subprocess.PIPE,
        )
        await proc.communicate()

        if proc.returncode != 0:
            logger.error("ffmpeg conversion failed")
            return "[Не удалось конвертировать аудио, попробуй текстом]"

        # Read WAV file and send to VOSK SERVER via WebSocket
        with open(wav_path, "rb") as f:
            audio_data = f.read()

        url = f"ws://{config.VOSK_SERVER_HOST}:{config.VOSK_SERVER_PORT}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            # VOSK SERVER uses WebSocket, but we can also use HTTP API if available
            # Try HTTP POST first (simpler, more reliable)
            http_url = f"http://{config.VOSK_SERVER_HOST}:{config.VOSK_SERVER_PORT}/api/v1/recognize"
            response = await client.post(
                http_url,
                files={"file": (wav_path.name, audio_data, "audio/wav")},
                data={"model": "default"},
            )

        if response.status_code == 200:
            data = response.json()
            # VOSK SERVER response format: {"result": [{"conf": 1.0, "end": 1.23, "start": 0.45, "word": "привет"}], "text": "привет"}
            text = data.get("text", "").strip()
            if text:
                logger.info(f"Transcribed {voice.duration}s voice: {text[:60]}...")
                return text
            return "[Пустая запись]"

        elif response.status_code == 503:
            logger.warning("VOSK SERVER not available")
            return "[VOSK SERVER недоступен, попробуй текстом]"

        else:
            logger.error(f"VOSK SERVER error {response.status_code}: {response.text[:200]}")
            return "[Не удалось распознать, попробуй текстом]"

    except httpx.TimeoutException:
        logger.error("VOSK SERVER timeout")
        return "[Таймаут распознавания, попробуй текстом]"
    except Exception as e:
        logger.error(f"Voice transcription error: {e}", exc_info=True)
        return "[Ошибка распознавания, попробуй текстом]"
    finally:
        # Cleanup temp files
        for path in [tmp_path, tmp_path.with_suffix(".wav") if tmp_path else None]:
            if path and path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass
