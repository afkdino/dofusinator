"""
Motor de OCR. Captura região da tela e extrai texto via Tesseract.
v3: auto-detecção do tesseract.exe + helpers de debug.
"""
import hashlib
import logging
import os
import time
from pathlib import Path
from typing import Optional

from settings import Settings, get_app_dir

log = logging.getLogger(__name__)

DEBUG_DIR = get_app_dir() / "debug"

# Caminhos padrão onde Tesseract costuma ser instalado no Windows
TESSERACT_CANDIDATE_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]


def auto_detect_tesseract() -> Optional[str]:
    """Procura tesseract.exe nos caminhos padrão. Retorna path se achar."""
    candidates = list(TESSERACT_CANDIDATE_PATHS)
    # Adiciona %LOCALAPPDATA% se disponível
    local_app = os.environ.get('LOCALAPPDATA')
    if local_app:
        candidates.append(os.path.join(local_app, 'Programs', 'Tesseract-OCR', 'tesseract.exe'))

    for path in candidates:
        if os.path.isfile(path):
            log.info(f"Tesseract auto-detectado em: {path}")
            return path

    log.info("Tesseract não encontrado nos caminhos padrão.")
    return None


class OCREngine:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._configure_tesseract()

    def _configure_tesseract(self):
        try:
            import pytesseract
            tesseract_path = self.settings.get('tesseract_path', '').strip()

            # Auto-detect se não tem path configurado
            if not tesseract_path:
                detected = auto_detect_tesseract()
                if detected:
                    tesseract_path = detected
                    self.settings.set('tesseract_path', detected)
                    self.settings.save()

            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                log.info(f"Tesseract path: {tesseract_path}")
            else:
                log.warning("Tesseract path: vazio - usando PATH do sistema")
        except ImportError:
            log.error("pytesseract não instalado")

    def check_tesseract(self) -> tuple[bool, str]:
        try:
            import pytesseract
            version = pytesseract.get_tesseract_version()
            langs = pytesseract.get_languages(config='')
            log.info(f"Tesseract v{version}, idiomas: {langs}")
            required = self.settings.get('ocr_language', 'fra')
            if required not in langs:
                return False, (
                    f"Tesseract OK (v{version}) mas o idioma '{required}' não está instalado.\n"
                    f"Idiomas disponíveis: {', '.join(langs)}"
                )
            return True, f"Tesseract v{version} OK. Idioma '{required}' instalado."
        except Exception as e:
            return False, f"Tesseract NÃO ENCONTRADO!\nErro: {e}"

    def capture_region(self, perimeter: list) -> Optional['Image.Image']:
        if not perimeter or len(perimeter) != 4:
            return None
        try:
            from PIL import ImageGrab
            x1, y1, x2, y2 = perimeter
            return ImageGrab.grab(bbox=(x1, y1, x2, y2))
        except Exception as e:
            log.error(f"Erro ao capturar região: {e}", exc_info=True)
            return None

    def preprocess(self, image: 'Image.Image') -> 'Image.Image':
        try:
            from PIL import ImageEnhance, ImageFilter, ImageOps

            img = image
            if self.settings.get('ocr_preprocess_grayscale', True):
                img = img.convert('L')
            if self.settings.get('ocr_preprocess_invert', True):
                if img.mode not in ('L', 'RGB'):
                    img = img.convert('L')
                img = ImageOps.invert(img)
            contrast = float(self.settings.get('ocr_preprocess_contrast', 2.0))
            if contrast != 1.0:
                img = ImageEnhance.Contrast(img).enhance(contrast)
            scale = int(self.settings.get('ocr_preprocess_scale', 2))
            if scale > 1:
                img = img.resize((img.width * scale, img.height * scale))
            return img
        except Exception as e:
            log.error(f"Erro no preprocess: {e}", exc_info=True)
            return image

    def image_to_text(self, image: 'Image.Image', lang: Optional[str] = None) -> str:
        if image is None:
            return ""
        try:
            import pytesseract
            language = lang or self.settings.get('ocr_language', 'fra')
            return pytesseract.image_to_string(image, lang=language, config='--psm 6')
        except Exception as e:
            log.error(f"Erro Tesseract: {e}", exc_info=True)
            return ""

    def hash_image(self, image: 'Image.Image') -> str:
        if image is None:
            return ""
        try:
            return hashlib.md5(image.tobytes()).hexdigest()
        except Exception:
            return ""

    def capture_and_extract(self) -> tuple[list[str], str]:
        perimeter = self.settings.get('perimeter')
        if not perimeter:
            return [], ""

        raw = self.capture_region(perimeter)
        if raw is None:
            return [], ""

        img_hash = self.hash_image(raw)
        processed = self.preprocess(raw)
        text = self.image_to_text(processed)

        if not text or not text.strip():
            return [], img_hash

        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if len(line) >= 2:
                lines.append(line)

        return lines, img_hash

    def debug_capture(self) -> dict:
        """Captura uma vez e retorna info detalhada pra debug."""
        result = {
            'tesseract_ok': False, 'tesseract_msg': '',
            'perimeter': None, 'image_size': None,
            'raw_text': '', 'lines': [], 'lines_count': 0,
            'error': None,
            'raw_image_path': None, 'processed_image_path': None,
        }

        tess_ok, tess_msg = self.check_tesseract()
        result['tesseract_ok'] = tess_ok
        result['tesseract_msg'] = tess_msg
        if not tess_ok:
            result['error'] = tess_msg
            return result

        perimeter = self.settings.get('perimeter')
        result['perimeter'] = perimeter
        if not perimeter:
            result['error'] = "Perimeter não configurado."
            return result

        raw = self.capture_region(perimeter)
        if raw is None:
            result['error'] = "Falha ao capturar região da tela."
            return result
        result['image_size'] = raw.size

        processed = self.preprocess(raw)

        try:
            DEBUG_DIR.mkdir(exist_ok=True)
            ts = int(time.time())
            raw_path = DEBUG_DIR / f"test_{ts}_raw.png"
            proc_path = DEBUG_DIR / f"test_{ts}_processed.png"
            raw.save(raw_path)
            processed.save(proc_path)
            result['raw_image_path'] = str(raw_path)
            result['processed_image_path'] = str(proc_path)
        except Exception as e:
            log.error(f"Erro ao salvar debug images: {e}")

        text = self.image_to_text(processed)
        result['raw_text'] = text
        lines = [line.strip() for line in text.split('\n') if line.strip() and len(line.strip()) >= 2]
        result['lines'] = lines
        result['lines_count'] = len(lines)
        return result
