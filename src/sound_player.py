"""
Tocador de sons com controle de volume.

v3.3.2: implementa atenuação manual via struct (sem audioop).
audioop foi REMOVIDO do Python 3.13. struct tá em qualquer versão.

Estratégia:
- Volume 100%: toca arquivo original direto (SND_FILENAME | SND_ASYNC)
- Volume <100%: gera arquivo com volume ajustado em .sound_cache/,
                cacheia por (sound_file, volume_pct), toca via SND_FILENAME.
"""
import logging
import os
import struct
import threading
import wave
from pathlib import Path

from settings import Settings, get_app_dir

log = logging.getLogger(__name__)

SOUNDS_DIR = get_app_dir() / "sounds"
TEMP_DIR = get_app_dir() / ".sound_cache"


def _multiply_samples(frames: bytes, sampwidth: int, factor: float) -> bytes:
    """
    Multiplica todos os samples por `factor` (0.0 a 1.0+).
    Substitui audioop.mul (removido no Python 3.13).
    Suporta 8-bit unsigned, 16-bit signed e 32-bit signed (formatos comuns).
    """
    if sampwidth == 2:
        # 16-bit signed PCM (formato mais comum)
        n = len(frames) // 2
        samples = struct.unpack(f'<{n}h', frames)
        adjusted = [max(-32768, min(32767, int(s * factor))) for s in samples]
        return struct.pack(f'<{n}h', *adjusted)

    elif sampwidth == 1:
        # 8-bit unsigned (offset 128)
        out = bytearray(len(frames))
        for i, byte in enumerate(frames):
            sample = byte - 128
            adjusted = int(sample * factor)
            adjusted = max(-128, min(127, adjusted))
            out[i] = adjusted + 128
        return bytes(out)

    elif sampwidth == 4:
        # 32-bit signed
        n = len(frames) // 4
        samples = struct.unpack(f'<{n}i', frames)
        max_val = 2**31 - 1
        min_val = -2**31
        adjusted = [max(min_val, min(max_val, int(s * factor))) for s in samples]
        return struct.pack(f'<{n}i', *adjusted)

    elif sampwidth == 3:
        # 24-bit signed - raro mas possível
        n = len(frames) // 3
        out = bytearray(3 * n)
        for i in range(n):
            # Lê 3 bytes little-endian, converte pra signed 24-bit
            b0 = frames[i*3]
            b1 = frames[i*3 + 1]
            b2 = frames[i*3 + 2]
            sample = b0 | (b1 << 8) | (b2 << 16)
            if sample & 0x800000:  # negativo
                sample -= 0x1000000
            adjusted = int(sample * factor)
            adjusted = max(-(2**23), min(2**23 - 1, adjusted))
            if adjusted < 0:
                adjusted += 0x1000000
            out[i*3]     = adjusted & 0xFF
            out[i*3 + 1] = (adjusted >> 8) & 0xFF
            out[i*3 + 2] = (adjusted >> 16) & 0xFF
        return bytes(out)

    else:
        raise ValueError(f"sampwidth {sampwidth} não suportado")


class SoundPlayer:
    def __init__(self, settings: Settings):
        self.settings = settings
        SOUNDS_DIR.mkdir(exist_ok=True)
        TEMP_DIR.mkdir(exist_ok=True)
        self._cache: dict[str, str] = {}
        self._cache_lock = threading.Lock()

    def list_available_sounds(self) -> list[str]:
        if not SOUNDS_DIR.exists():
            return []
        return sorted([f.name for f in SOUNDS_DIR.glob("*.wav")])

    def play(self, sound_file: str = None, force_volume: float = None):
        """Toca som async."""
        if not self.settings.get('sound_enabled', True):
            return

        sound_file = sound_file or self.settings.get('sound_file', 'pop.wav')
        if not sound_file:
            return

        path = SOUNDS_DIR / sound_file
        if not path.exists():
            log.debug(f"Som {sound_file} não existe em {SOUNDS_DIR}. Skip.")
            return

        volume_pct = force_volume if force_volume is not None else self.settings.get('sound_volume', 50)
        volume_pct = max(0, min(100, int(volume_pct)))

        if volume_pct == 0:
            return

        threading.Thread(
            target=self._play_sync, args=(str(path), sound_file, volume_pct), daemon=True
        ).start()

    def _play_sync(self, path: str, sound_file: str, volume_pct: int):
        try:
            import winsound

            if volume_pct == 100:
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return

            cached_path = self._get_or_create_cached_file(path, sound_file, volume_pct)
            if cached_path is None:
                log.warning(f"Falha ao gerar arquivo de volume. Tocando em volume cheio.")
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return

            winsound.PlaySound(cached_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except ImportError:
            log.warning("winsound não disponível (não Windows). Som ignorado.")
        except Exception as e:
            log.error(f"Erro ao tocar som '{path}': {e}", exc_info=True)

    def _get_or_create_cached_file(self, source_path: str, sound_file: str, volume_pct: int) -> str | None:
        cache_key = f"{sound_file}_{volume_pct}"

        with self._cache_lock:
            cached = self._cache.get(cache_key)
            if cached and os.path.exists(cached):
                return cached

            volume_factor = volume_pct / 100.0
            try:
                generated_path = self._build_volumed_file(
                    source_path, sound_file, volume_pct, volume_factor
                )
                if generated_path:
                    self._cache[cache_key] = generated_path
                return generated_path
            except Exception as e:
                log.error(f"Erro ao gerar arquivo de volume: {e}", exc_info=True)
                return None

    def _build_volumed_file(
        self, source_path: str, sound_file: str,
        volume_pct: int, volume: float
    ) -> str | None:
        try:
            with wave.open(source_path, 'rb') as wf:
                nchannels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                nframes = wf.getnframes()
                frames = wf.readframes(nframes)

            adjusted = _multiply_samples(frames, sampwidth, volume)

            stem = Path(sound_file).stem
            out_path = TEMP_DIR / f"{stem}_v{volume_pct}.wav"

            with wave.open(str(out_path), 'wb') as wf:
                wf.setnchannels(nchannels)
                wf.setsampwidth(sampwidth)
                wf.setframerate(framerate)
                wf.writeframes(adjusted)

            log.debug(f"Arquivo de volume gerado: {out_path}")
            return str(out_path)
        except wave.Error as e:
            log.error(f"WAV inválido '{source_path}': {e}")
            return None
        except ValueError as e:
            log.error(f"Formato WAV não suportado: {e}")
            return None
        except Exception as e:
            log.error(f"Erro ao gerar arquivo: {e}")
            return None

    def invalidate_cache(self):
        with self._cache_lock:
            self._cache.clear()
