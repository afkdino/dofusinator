"""
Dofusinator (Translator) - Tradutor em tempo real pro chat do Dofus
Entry point principal.
"""
import sys
import logging

import customtkinter as ctk

from app_info import APP_NAME, APP_FULL_NAME, APP_VERSION, APP_AUTHOR, APP_ID
from assets_helper import set_window_icon, set_app_user_model_id
from settings import Settings
from translator_service import TranslatorService
from slang_processor import SlangProcessor
from custom_terms import CustomTermsManager
from history_manager import HistoryManager
from sound_player import SoundPlayer
from ocr_engine import OCREngine
from main_window import MainWindow
from overlay_window import OverlayWindow
from quick_input_popup import QuickInputPopup
from hotkey_manager import HotkeyManager
from tray_icon import TrayIcon


def setup_logging(enabled: bool):
    level = logging.DEBUG if enabled else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler('debug.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout),
        ]
    )


def main():
    settings = Settings()
    settings.load()

    setup_logging(settings.get('logging_enabled', False))
    log = logging.getLogger(__name__)
    log.info(f"=== {APP_FULL_NAME} v{APP_VERSION} by {APP_AUTHOR} iniciando ===")

    # === i18n: carrega idioma ANTES da UI (Bloco 2 v1.1) ===
    # Tem que vir logo após settings.load() e antes de qualquer t() ser chamada.
    from i18n import set_language
    ui_lang = settings.get('ui_language', 'pt')
    set_language(ui_lang)
    log.info(f"i18n: UI carregada em '{ui_lang}'")

    # CRÍTICO no Windows: define um AppUserModelID único pra que o Windows
    # mostre o ícone correto na taskbar (sem isso, agrupa pelo python.exe
    # em dev, e em alguns casos do .exe não pega o ícone).
    # Tem que ser chamado ANTES de criar qualquer janela tk.
    set_app_user_model_id(f"afkdino.{APP_ID}.{APP_VERSION}")

    ctk.set_appearance_mode("dark")

    # Serviços
    slang = SlangProcessor()
    custom_terms = CustomTermsManager()
    history = HistoryManager(settings)
    # v1.0.21: Histórico do chat capturado (separado do quick_input)
    from chat_history_manager import ChatHistoryManager
    chat_history = ChatHistoryManager(settings)
    sound_player = SoundPlayer(settings)
    translator = TranslatorService(settings, slang, custom_terms)
    ocr = OCREngine(settings)

    root = ctk.CTk()
    root.title(APP_NAME)
    set_window_icon(root)

    # v1.0.21: passa chat_history pro overlay carregar histórico ao mostrar
    overlay = OverlayWindow(root, settings, translator, ocr)
    overlay.chat_history = chat_history
    quick_input = QuickInputPopup(root, settings, translator, history, sound_player)

    # v1.0.21: liga callback do overlay → chat_history
    # (cada linha REALMENTE nova é registrada no histórico persistente)
    def on_truly_new_line(original: str, translated: str):
        src_lang = settings.get('source_language_read', 'fr')
        dest_lang = settings.get('target_language_read', 'pt')
        chat_history.add(original=original, translated=translated, src=src_lang, dest=dest_lang)

    overlay.on_truly_new_line = on_truly_new_line

    # HotkeyManager criado mas não iniciado ainda — vamos registrar os callbacks
    # de overlay_toggle e lurker_toggle DEPOIS de criar a main_window que tem
    # os métodos correspondentes.
    hotkey_mgr = HotkeyManager(settings, quick_input)

    # Forward declarations - vamos preencher depois de criar main_window
    main_window_ref = {'instance': None}
    tray_ref = {'instance': None}

    def on_quit():
        """Fecha o app de verdade."""
        log.info("Encerrando aplicação...")
        try:
            if tray_ref['instance']:
                tray_ref['instance'].stop()
        except Exception as e:
            log.error(f"Erro ao parar tray: {e}")
        try:
            hotkey_mgr.stop()
            overlay.stop_capture()
            translator.cache.save()
            history.save()
            settings.save()
        except Exception as e:
            log.error(f"Erro ao fechar serviços: {e}")
        try:
            root.quit()
            root.destroy()
        except Exception:
            pass

    def on_minimize_to_tray():
        """Esconde a janela principal (vai pra tray)."""
        if main_window_ref['instance']:
            main_window_ref['instance'].hide_to_tray()

    def on_open_from_tray():
        """Tray pediu pra abrir a janela principal."""
        if main_window_ref['instance']:
            # Tray roda em outra thread, agenda no main
            root.after(0, main_window_ref['instance'].show_window)

    def on_toggle_lurker_from_tray():
        """Tray pediu toggle Lurker."""
        if main_window_ref['instance']:
            root.after(0, main_window_ref['instance'].toggle_lurker_external)

    def on_quit_from_tray():
        """Tray pediu pra fechar app."""
        # Schedule no main thread
        root.after(0, on_quit)

    # Cria main_window com callbacks
    main_window = MainWindow(
        root=root,
        settings=settings,
        translator=translator,
        ocr=ocr,
        overlay=overlay,
        quick_input=quick_input,
        custom_terms=custom_terms,
        hotkey_mgr=hotkey_mgr,
        sound_player=sound_player,
        chat_history=chat_history,  # v1.0.21
        on_close_app=on_quit,
        on_minimize_to_tray=on_minimize_to_tray,
    )
    main_window_ref['instance'] = main_window

    # === Hotkeys: registra callbacks adicionais e inicia ===
    # Sub-bloco 3.2: 3 hotkeys customizáveis (quick_input, overlay_toggle, lurker_toggle)
    # quick_input já foi registrado automaticamente no construtor do HotkeyManager.
    # Registrando os outros 2 agora que main_window existe:
    def overlay_toggle_cb():
        """Callback do hotkey de overlay - toggle entre overlay completo e mini-pill."""
        try:
            root.after(0, main_window.toggle_overlay)
        except Exception as e:
            log.error(f"Erro no callback overlay_toggle: {e}")

    def lurker_toggle_cb():
        """Callback do hotkey de lurker - liga/desliga modo lurker."""
        try:
            root.after(0, main_window.toggle_lurker_from_hotkey)
        except Exception as e:
            log.error(f"Erro no callback lurker_toggle: {e}")

    hotkey_mgr.set_callback('overlay_toggle', overlay_toggle_cb)
    hotkey_mgr.set_callback('lurker_toggle', lurker_toggle_cb)
    hotkey_mgr.start()

    # Cria e inicia tray icon
    tray = TrayIcon(
        settings=settings,
        on_open=on_open_from_tray,
        on_quit=on_quit_from_tray,
        on_toggle_lurker=on_toggle_lurker_from_tray,
    )
    tray.start()
    tray_ref['instance'] = tray

    # Hook no protocol close (Alt+F4 etc)
    def on_wm_close():
        if settings.get('close_to_tray', False):
            on_minimize_to_tray()
        else:
            on_quit()

    root.protocol("WM_DELETE_WINDOW", on_wm_close)

    # === Welcome Screen (Bloco 3 / Sub-bloco 3.1) ===
    # Aparece SÓ na primeira execução (settings.first_run_completed = False).
    # Quando usuário finalizar ou pular, marca a flag = True.
    if not settings.get('first_run_completed', False):
        log.info("Primeira execução detectada - mostrando Welcome Screen")
        # Import lazy pra não impactar startup quando não vai usar
        from welcome_screen import WelcomeScreen

        # Agendamos pra após o root estar TOTALMENTE visível e estável.
        # Delay aumentado de 400 → 800ms pra garantir mainloop processou tudo.
        # Bug anterior: 400ms era muito cedo, root ainda não tava mapeada,
        # grab_set falhava silenciosamente e o app travava.
        def show_welcome():
            try:
                # SEGURANÇA: libera qualquer grab que possa estar ativo
                # (paranoia - se algo travou antes, libera)
                try:
                    root.grab_release()
                except Exception:
                    pass

                log.info("Criando WelcomeScreen...")
                welcome = WelcomeScreen(
                    parent=root,
                    settings=settings,
                    on_complete=lambda: log.info("Welcome screen completed"),
                    on_language_changed=None,  # idioma só aplica no próximo restart
                )
                welcome.show()
                log.info("WelcomeScreen.show() retornou")
            except Exception as e:
                log.error(f"FATAL: Erro ao mostrar welcome screen: {e}", exc_info=True)
                # Em caso de erro, marca como completo pra não tentar de novo
                # E libera qualquer grab pendente (segurança)
                try:
                    root.grab_release()
                except Exception:
                    pass
                settings.set('first_run_completed', True)
                settings.save()

        # Delay de 800ms (era 400) - garante que root.mainloop começou a processar
        root.after(800, show_welcome)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_quit()


if __name__ == "__main__":
    main()
