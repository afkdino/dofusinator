<div align="center">

<img src="https://raw.githubusercontent.com/afkdino/dofusinator/main/assets/dofusinator.png" alt="Dofusinator" width="200"/>

# Dofusinator

**Speak every tongue in Amakna.**
Real-time chat translator for Dofus Retro using OCR. FR · PT · EN · ES.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078d6)](https://github.com/afkdino/dofusinator/releases)
[![Made with Python](https://img.shields.io/badge/Made%20with-Python-3776AB)](https://www.python.org/)

[🇧🇷 Português](#-português) · [🇬🇧 English](#-english)

</div>

---

## 🇧🇷 Português

### O que é

Dofusinator é um app de desktop pra Windows que captura o chat do **Dofus Retro** em tempo real e traduz entre os 4 idiomas suportados — **Francês, Português, Inglês e Espanhol** — usando OCR (Tesseract). Mostra a tradução numa janela overlay sobreposta ao jogo, e ainda permite que tu envie mensagens no teu idioma que são automaticamente traduzidas pro idioma do servidor e digitadas no chat in-game.

Tu escolhe livremente a combinação de leitura (ex: FR → PT) e a de escrita (ex: PT → FR). Cada direção é configurada independente, então dá pra usar o app em qualquer servidor de Dofus Retro.

### Features principais

- 🔍 **OCR ao vivo** do chat do Dofus Retro (Tesseract)
- 🌐 **Tradução em tempo real** entre **FR, PT, EN, ES** (Google Translate ou DeepL)
- 💬 **Quick input**: escreve no teu idioma, manda no idioma do servidor
- 🕵️ **Modo Lurker**: somente leitura, bloqueia auto-send
- 📜 **Histórico persistente** de até 500 mensagens (cross-session)
- 🎨 **Identidade visual Dofus Retro** (tema bege/dourado)
- 🌍 **Interface do app em 4 idiomas**: PT-BR, EN, FR, ES
- 🎮 **Multi-monitor** com posicionamento por monitor
- 🔄 **Auto-update** via GitHub Releases (a partir da v1.1.0)

### Como instalar

1. Vai em [Releases](https://github.com/afkdino/dofusinator/releases) e baixa o **`Dofusinator-Setup.exe`** mais recente
2. Roda o instalador (não pede admin/UAC)
3. App abre automaticamente após instalar
4. Configura o **caminho do Tesseract** e o **perímetro de captura** (botão F2)

> ⚠️ **Pré-requisito**: precisa ter o [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) instalado no Windows com o pacote do idioma que tu vai capturar do chat (`fra`, `eng`, `spa` ou `por`).

### Como usar (básico)

1. Abre o Dofus Retro
2. Abre o Dofusinator
3. Aperta **F2** e desenha um retângulo cobrindo a área do chat in-game
4. A janela overlay vai aparecer com as traduções
5. Pra mandar mensagem traduzida: **Ctrl+Shift+T** abre o popup de input rápido

### Stack técnica

- **Python 3.x** + **CustomTkinter** + **Tk**
- **Tesseract OCR** pra captura de texto
- **Google Translate** (gratuito) ou **DeepL** (premium) pra tradução
- **PyInstaller** pra empacotar
- **Velopack** pra installer + auto-update (a partir da v1.1.0)

### Contribuindo

Issues e Pull Requests são bem-vindos! Mas atenção:
- Comentários em PT-BR (mantemos esse padrão no código)
- Cada mudança de versão tem comentário tipo `# v1.x.x: descrição`
- Strings novas devem ser adicionadas ao `i18n.py` em PT/EN/FR/ES

### Licença

Apache License 2.0 — veja [LICENSE](LICENSE) pra detalhes.

### Créditos

- Desenvolvido por [@afkdino](https://github.com/afkdino) (Guilherme G. Ferreira)
- Coffee fueled by **Cra de equipamento sair na primeira tentativa**

---

## 🇬🇧 English

### What is it

Dofusinator is a Windows desktop app that captures **Dofus Retro** chat in real time and translates between its 4 supported languages — **French, Portuguese, English and Spanish** — using OCR (Tesseract). It displays translations in an overlay window on top of the game, and lets you send messages in your own language that are automatically translated to the server's language and typed into the in-game chat.

You can freely set the reading combo (e.g. FR → PT) and the writing combo (e.g. PT → FR) independently, so the app works on any Dofus Retro server.

### Key features

- 🔍 **Live OCR** of Dofus Retro chat (Tesseract)
- 🌐 **Real-time translation** between **FR, PT, EN, ES** (Google Translate or DeepL)
- 💬 **Quick input**: type in your language, send in the server's language
- 🕵️ **Lurker mode**: read-only, blocks auto-send
- 📜 **Persistent history** of up to 500 messages (cross-session)
- 🎨 **Dofus Retro visual identity** (beige/gold theme)
- 🌍 **App interface in 4 languages**: PT-BR, EN, FR, ES
- 🎮 **Multi-monitor** support with per-monitor positioning
- 🔄 **Auto-update** via GitHub Releases (from v1.1.0)

### How to install

1. Go to [Releases](https://github.com/afkdino/dofusinator/releases) and download the latest **`Dofusinator-Setup.exe`**
2. Run the installer (no admin/UAC required)
3. App opens automatically after install
4. Configure the **Tesseract path** and **capture area** (F2 button)

> ⚠️ **Prerequisite**: requires [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) installed on Windows with the language pack of the chat you're capturing (`fra`, `eng`, `spa` or `por`).

### Basic usage

1. Open Dofus Retro
2. Open Dofusinator
3. Press **F2** and draw a rectangle covering the in-game chat area
4. The overlay window appears with translations
5. To send a translated message: **Ctrl+Shift+T** opens the quick input popup

### Tech stack

- **Python 3.x** + **CustomTkinter** + **Tk**
- **Tesseract OCR** for text capture
- **Google Translate** (free) or **DeepL** (premium) for translation
- **PyInstaller** for packaging
- **Velopack** for installer + auto-update (from v1.1.0)

### Contributing

Issues and Pull Requests are welcome! Some notes:
- Code comments in Portuguese-BR (we keep this convention)
- Each version change has a comment like `# v1.x.x: description`
- New strings should be added to `i18n.py` in PT/EN/FR/ES

### License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

### Credits

- Built by [@afkdino](https://github.com/afkdino) (Guilherme G. Ferreira)
- Coffee fueled by **Cra getting his exo on the first try**

---

<div align="center">

⚔️ Made for the Dofus Retro community ⚔️

</div>
