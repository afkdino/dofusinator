"""
Wrapper do UpdateManager do Velopack pro Dofusinator.

Responsabilidade: encapsular toda lógica de auto-update num único módulo,
mantendo main.py e main_window.py desacoplados do velopack.

Funcionamento:
- Em modo DEV (rodando direto via python main.py), self.is_active = False
  e todos os métodos são no-op. Isso permite desenvolver sem o Velopack
  estar empacotado.
- Em PROD (instalado via Setup.exe gerado por vpk pack), self.is_active = True
  e check_async() consulta o GitHub Releases periodicamente.
"""
import logging
import threading
from typing import Callable, Optional

import velopack

from app_info import APP_VERSION

log = logging.getLogger(__name__)

# URL pública do repo. UpdateManager vai buscar releases.win.json daqui.
GITHUB_REPO_URL = "https://github.com/afkdino/dofusinator"


class DofusUpdater:
    """
    Encapsula o UpdateManager do Velopack.

    Uso típico:
        updater = DofusUpdater()
        updater.check_async(on_available=lambda v: show_toast(v))

    Quando user clicar pra atualizar:
        updater.apply_and_restart()
    """

    def __init__(self):
        self._manager: Optional[velopack.UpdateManager] = None
        self._update_info = None

        try:
            self._manager = velopack.UpdateManager(GITHUB_REPO_URL)
            log.info(
                f"DofusUpdater inicializado. Versão atual: {APP_VERSION}, "
                f"buscando updates em: {GITHUB_REPO_URL}"
            )
        except Exception as e:
            # Modo DEV: app rodando direto, não foi instalado via Velopack.
            # UpdateManager falha na inicialização. É comportamento esperado.
            log.info(f"DofusUpdater em modo DEV (Velopack não disponível): {e}")
            self._manager = None

    @property
    def is_active(self) -> bool:
        """True se foi instalado via Velopack e pode checar updates."""
        return self._manager is not None

    @property
    def latest_version(self) -> Optional[str]:
        """Versão da última atualização disponível, ou None se não tem."""
        if self._update_info is None:
            return None
        try:
            return str(self._update_info.target_full_release.version)
        except Exception:
            return None

    def check_async(self, on_available: Callable[[str], None]) -> None:
        """
        Verifica updates em background.

        Args:
            on_available: callback chamado SE houver update.
                Recebe a string da versão nova (ex: "1.1.1").
                Esse callback roda numa thread de background — quem
                consome deve marshallar pro main thread se for mexer em UI.
        """
        if not self.is_active:
            log.debug("check_async: pulando (modo DEV)")
            return

        def _work():
            try:
                info = self._manager.check_for_updates()
                if info is None:
                    log.info("Nenhuma atualização disponível.")
                    return
                self._update_info = info
                new_version = self.latest_version or "?"
                log.info(f"Atualização disponível: v{new_version}")
                try:
                    on_available(new_version)
                except Exception as e:
                    log.error(f"Callback on_available levantou: {e}", exc_info=True)
            except Exception as e:
                # Falha de rede, repo inacessível, etc. NÃO quebra o app.
                log.warning(f"Falha ao verificar atualização: {e}")

        thread = threading.Thread(
            target=_work,
            daemon=True,
            name="DofusUpdater-check",
        )
        thread.start()

    def download_async(
        self,
        on_done: Callable[[bool], None],
        on_progress: Optional[Callable[[int], None]] = None,
    ) -> None:
        """
        Baixa o update em background.

        Args:
            on_done: callback chamado quando termina. Recebe True se sucesso.
            on_progress: opcional, recebe int 0-100 com progresso do download.
                NOTA: a versão atual do velopack-py pode não passar progresso
                granular. Vamos só chamar on_progress(0) e on_progress(100).
        """
        if not self.is_active or self._update_info is None:
            on_done(False)
            return

        def _work():
            try:
                if on_progress:
                    on_progress(0)
                self._manager.download_updates(self._update_info)
                if on_progress:
                    on_progress(100)
                log.info(f"Update baixado: v{self.latest_version}")
                on_done(True)
            except Exception as e:
                log.error(f"Falha ao baixar update: {e}", exc_info=True)
                on_done(False)

        thread = threading.Thread(
            target=_work,
            daemon=True,
            name="DofusUpdater-download",
        )
        thread.start()

    def apply_and_restart(self) -> None:
        """
        Aplica o update baixado e reinicia o app.

        ATENÇÃO: este método NÃO retorna. O processo do app é encerrado
        e substituído pela nova versão. Salva tudo que precisa salvar
        ANTES de chamar.
        """
        if not self.is_active or self._update_info is None:
            log.warning("apply_and_restart chamado sem update disponível")
            return
        try:
            log.info("Aplicando update e reiniciando...")
            self._manager.apply_updates_and_restart(self._update_info)
            # Não retorna — Velopack mata o processo
        except Exception as e:
            log.error(f"Falha ao aplicar update: {e}", exc_info=True)
            raise