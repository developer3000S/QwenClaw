"""Voice message transcription via VOSK SERVER (WebSocket)."""

import asyncio
import json
import logging
import tempfile
from pathlib import Path

import websockets

import config

logger = logging.getLogger("voice")

# Chunk size for sending audio (Vosk server processes incrementally)
CHUNK_SIZE = 8192


async def transcribe_voice(voice, bot) -> str | None:
    """Download voice message and transcribe via VOSK SERVER over WebSocket.

    Args:
        voice: aiogram Voice or Audio object
        bot: aiogram Bot instance

    Returns:
        Transcribed text, error message, or None if not configured
    """
    if not config.VOSK_SERVER_HOST or not config.VOSK_SERVER_PORT:
        return None

    tmp_paths = []
    try:
        # Download voice file from Telegram
        file = await bot.get_file(voice.file_id)
        ogg_path = Path(tempfile.gettempdir()) / f"qwenbot_voice_{voice.file_id}.ogg"
        await bot.download_file(file.file_path, destination=str(ogg_path))
        tmp_paths.append(ogg_path)

        # Convert OGG to WAV (Vosk expects 16kHz mono 16-bit PCM)
        wav_path = ogg_path.with_suffix(".wav")
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-i", str(ogg_path),
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
            str(wav_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.error(f"ffmpeg conversion failed: {stderr.decode()[:200]}")
            return "[Не удалось конвертировать аудио, попробуй текстом]"

        tmp_paths.append(wav_path)

        # Read WAV file and strip WAV header (44 bytes) — VOSK SERVER expects raw PCM
        with open(wav_path, "rb") as f:
            wav_data = f.read()
        # Skip 44-byte WAV header, keep only raw PCM samples
        audio_data = wav_data[44:] if len(wav_data) > 44 else wav_data
        
        logger.info(f"Audio prepared: {len(audio_data)} bytes raw PCM, {voice.duration}s")

        # Connect to VOSK SERVER via WebSocket
        ws_url = f"ws://{config.VOSK_SERVER_HOST}:{config.VOSK_SERVER_PORT}"
        result_text = None

        try:
            async with websockets.connect(ws_url) as ws:
                # Send config — VOSK SERVER expects sample_rate
                await ws.send(json.dumps({"sample_rate": 16000}))

                # Send audio in chunks
                for i in range(0, len(audio_data), CHUNK_SIZE):
                    chunk = audio_data[i:i + CHUNK_SIZE]
                    await ws.send(chunk)

                # Signal end of audio
                await ws.send(json.dumps({"eof": 1}))

                # VOSK SERVER sends ONE response after eof, then closes connection
                # Format: {"text": "распознанный текст"}
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=15.0)
                    result = json.loads(response)
                    result_text = result.get("text", "").strip()
                except asyncio.TimeoutError:
                    logger.warning("VOSK SERVER timeout — no response received")
                    result_text = ""

        except OSError as e:
            logger.error(f"Cannot connect to VOSK SERVER at {ws_url}: {e}")
            return "[VOSK SERVER недоступен, проверь настройки]"
        except Exception as e:
            logger.error(f"WebSocket error: {e}", exc_info=True)
            return "[Ошибка соединения с VOSK SERVER]"

        if result_text:
            logger.info(f"Transcribed {voice.duration}s voice: {result_text[:60]}...")
            return result_text

        logger.warning(f"VOSK SERVER returned empty result (duration: {voice.duration}s)")
        return "[Речь не распознана]"

    except Exception as e:
        logger.error(f"Voice transcription error: {e}", exc_info=True)
        return "[Ошибка распознавания, попробуй текстом]"
    finally:
        # Cleanup temp files
        for path in tmp_paths:
            if path and path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass
