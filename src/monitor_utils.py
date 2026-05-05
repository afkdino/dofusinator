"""
Utilitários pra detectar monitores e gerenciar geometrias por monitor.
Usa screeninfo (cross-platform).
"""
import logging
from typing import Optional

log = logging.getLogger(__name__)


def get_monitors() -> list[dict]:
    """
    Retorna lista de monitores conectados.
    Cada item: {name, x, y, width, height, is_primary}
    """
    try:
        from screeninfo import get_monitors as _get
        monitors = _get()
        result = []
        for i, m in enumerate(monitors):
            name = m.name or f"Monitor {i}"
            result.append({
                'name': name,
                'x': m.x,
                'y': m.y,
                'width': m.width,
                'height': m.height,
                'is_primary': getattr(m, 'is_primary', i == 0),
            })
        return result
    except Exception as e:
        log.warning(f"Erro ao detectar monitores ({e}). Usando fallback de monitor único.")
        # Fallback: usar tkinter pra pegar monitor primário
        try:
            import tkinter as tk
            root = tk._default_root
            if root is None:
                root = tk.Tk()
                root.withdraw()
                created = True
            else:
                created = False
            w = root.winfo_screenwidth()
            h = root.winfo_screenheight()
            if created:
                root.destroy()
            return [{
                'name': 'Monitor 0',
                'x': 0, 'y': 0,
                'width': w, 'height': h,
                'is_primary': True,
            }]
        except Exception:
            return []


def get_monitor_for_point(x: int, y: int) -> Optional[dict]:
    """Retorna o monitor que contém o ponto (x, y)."""
    for m in get_monitors():
        if m['x'] <= x < m['x'] + m['width'] and m['y'] <= y < m['y'] + m['height']:
            return m
    return None


def get_monitor_key(monitor: dict) -> str:
    """Gera chave única e estável pra monitor (usada em settings)."""
    if not monitor:
        return "default"
    # Use nome + dimensões pra chave estável
    return f"{monitor['name']}_{monitor['width']}x{monitor['height']}"


def get_primary_monitor() -> Optional[dict]:
    monitors = get_monitors()
    for m in monitors:
        if m['is_primary']:
            return m
    return monitors[0] if monitors else None


def parse_geometry(geom_str: str) -> Optional[tuple[int, int, int, int]]:
    """Parse string '600x400+100+200' -> (w, h, x, y). Aceita coordenadas negativas."""
    try:
        # Formato: WxH+X+Y ou WxH-X-Y etc
        size_part, *pos_parts = geom_str.replace('-', '+-').split('+')
        w, h = size_part.split('x')
        # pos_parts pode ser ['', '100', '200'] se começou com + ou ['100', '200']
        pos_parts = [p for p in pos_parts if p != '']
        if len(pos_parts) >= 2:
            x = int(pos_parts[0])
            y = int(pos_parts[1])
        else:
            x, y = 100, 100
        return int(w), int(h), x, y
    except Exception:
        return None


def center_window_on_parent(window, parent, width: int, height: int):
    """
    Centraliza uma janela toplevel relativa ao parent (em cima dele).

    Usado pelos popups Sobre, Termos Personalizados, etc.

    Args:
        window: Toplevel a ser centralizada
        parent: janela pai (ex: root da MainWindow)
        width: largura desejada
        height: altura desejada

    Aplica geometry "{w}x{h}+{x}+{y}" calculando x/y pelo centro do parent.
    Se o parent ainda não tá mapeado (winfo_width=1), faz fallback pro centro
    da tela primária.
    """
    try:
        parent.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()

        # Fallback: se parent ainda não mapeou direito, usa screen
        if pw <= 1 or ph <= 1:
            sw = window.winfo_screenwidth()
            sh = window.winfo_screenheight()
            x = max(0, (sw - width) // 2)
            y = max(0, (sh - height) // 2)
            window.geometry(f"{width}x{height}+{x}+{y}")
            return

        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        x = px + (pw - width) // 2
        y = py + (ph - height) // 2
        # Clamp pra não sair da tela
        x = max(0, x)
        y = max(0, y)
        window.geometry(f"{width}x{height}+{x}+{y}")
    except Exception as e:
        log.debug(f"center_window_on_parent falhou: {e}")
        window.geometry(f"{width}x{height}")
