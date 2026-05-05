"""
AutoApply - Helper pra conectar variáveis tk a callbacks de auto-apply.

Padrão:
  - Cada widget de configuração tem uma var tk (StringVar/BooleanVar/DoubleVar/IntVar)
  - Quando user mexe → var muda → trace dispara callback
  - Callback persiste em settings + aplica live + mostra toast

Suporta debounce pra inputs digitáveis (font_size, intervalo, etc.) onde
o user digita vários caracteres e a gente quer disparar só uma vez.

Uso:
    auto = AutoApply(settings, root, toast_mgr)
    auto.bind(my_var, 'setting_key',
              label_pt='Tema do overlay',
              apply_fn=update_overlay_theme,
              requires_restart=False,
              debounce_ms=0)

v1.0.30
"""
import logging
from typing import Callable, Optional

import tkinter as tk

log = logging.getLogger(__name__)


class AutoApply:
    """
    Conecta uma variável tk a callbacks de salvamento + apply + toast.
    """

    def __init__(self, settings, root, toast_mgr):
        """
        Args:
            settings: instância de Settings (com .set() e .save())
            root: tk root pra agendar after()
            toast_mgr: ToastManager (ou None se não quiser toasts)
        """
        self.settings = settings
        self.root = root
        self.toast_mgr = toast_mgr

        # Mapeamento var → debounce after_id
        self._debounce_ids: dict = {}
        # Mapeamento var → trace name (pra desconectar se necessário)
        self._traces: dict = {}
        # Flag pra suprimir toasts durante carregamento inicial das vars
        self._silent = False

    def silent(self, value: bool):
        """
        Modo silencioso: vars setadas não disparam toast.
        Útil quando inicializando vars no boot do app.
        """
        self._silent = value

    def bind(self, var: tk.Variable, setting_key: str,
             label: str = "Configuração",
             apply_fn: Optional[Callable] = None,
             requires_restart: bool = False,
             debounce_ms: int = 0,
             validator: Optional[Callable] = None):
        """
        Conecta uma variável tk pra auto-apply.

        Args:
            var: a variável tk (StringVar/BooleanVar/DoubleVar/IntVar)
            setting_key: chave em settings.json
            label: nome amigável pra mostrar no toast (ex: "Tema do overlay")
            apply_fn: função pra aplicar live (chamada após salvar settings)
            requires_restart: se True, mostra toast warning de reabrir
            debounce_ms: se >0, espera essa quantidade de ms antes de disparar
                         (útil pra IntVar/StringVar de campos digitáveis)
            validator: função(novo_valor) -> valor_ajustado | None
                       Se retornar None, ignora a mudança
        """
        def on_change(*args):
            if self._silent:
                return

            try:
                new_value = var.get()
            except Exception as e:
                log.debug(f"AutoApply: erro ao ler var de {setting_key}: {e}")
                return

            # Validação opcional
            if validator:
                try:
                    validated = validator(new_value)
                    if validated is None:
                        return
                    new_value = validated
                except Exception as e:
                    log.debug(f"AutoApply: validador falhou pra {setting_key}: {e}")
                    return

            # Debounce: se já tem timer pendente, cancela
            if debounce_ms > 0:
                old_id = self._debounce_ids.get(setting_key)
                if old_id:
                    try:
                        self.root.after_cancel(old_id)
                    except Exception:
                        pass

                # Agenda o commit pra debounce_ms depois
                def commit():
                    self._debounce_ids.pop(setting_key, None)
                    self._do_commit(setting_key, new_value, label,
                                    apply_fn, requires_restart)

                self._debounce_ids[setting_key] = self.root.after(debounce_ms, commit)
            else:
                # Commit imediato
                self._do_commit(setting_key, new_value, label,
                                apply_fn, requires_restart)

        trace_name = var.trace_add('write', on_change)
        self._traces[setting_key] = (var, trace_name)

    def _do_commit(self, setting_key: str, new_value, label: str,
                   apply_fn: Optional[Callable], requires_restart: bool):
        """Salva no settings + chama apply_fn + mostra toast."""
        try:
            # 1. Salva
            self.settings.set(setting_key, new_value)
            self.settings.save()

            # 2. Aplica live (se houver callback)
            if apply_fn:
                try:
                    apply_fn()
                except Exception as e:
                    log.error(f"AutoApply.apply_fn de {setting_key} falhou: {e}", exc_info=True)

            # 3. Toast
            if self.toast_mgr:
                if requires_restart:
                    # Toast warning amarelo
                    from i18n import t as _t
                    msg = _t('toast.restart_required', label=label)
                    self.toast_mgr.show(msg, level='warning')
                else:
                    from i18n import t as _t
                    msg = _t('toast.config_changed', label=label)
                    self.toast_mgr.show(msg, level='success')

            log.info(f"Auto-apply: {setting_key} = {new_value!r}")
        except Exception as e:
            log.error(f"AutoApply._do_commit falhou pra {setting_key}: {e}", exc_info=True)

    def cleanup(self):
        """Remove todos os traces. Chamar ao destruir a janela."""
        for setting_key, (var, trace_name) in self._traces.items():
            try:
                var.trace_remove('write', trace_name)
            except Exception:
                pass
        self._traces.clear()

        for setting_key, after_id in list(self._debounce_ids.items()):
            try:
                self.root.after_cancel(after_id)
            except Exception:
                pass
        self._debounce_ids.clear()
