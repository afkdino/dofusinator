<div align="center">

<img src="https://raw.githubusercontent.com/afkdino/dofusinator/main/assets/dofusinator.png" alt="Dofusinator" width="200"/>

# Dofusinator

**Read every whisper in Amakna.**
Real-time chat translator for Dofus Retro using OCR.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078d6)](https://github.com/afkdino/dofusinator/releases)
[![Made with Python](https://img.shields.io/badge/Made%20with-Python-3776AB)](https://www.python.org/)

[🇧🇷 Português](#-português) · [🇬🇧 English](#-english)

</div>

---

## 🇧🇷 Português

### O que é

Dofusinator é um app de desktop pra Windows que captura o chat do **Dofus Retro** em tempo real e traduz **francês → português** usando OCR (Tesseract). Mostra a tradução numa janela overlay sobreposta ao jogo, e ainda permite que tu envie mensagens em PT que são automaticamente traduzidas pra FR e digitadas no chat in-game.

Feito por e pra brasileiros que jogam em servidores franceses (Boune, Crocabulia, etc.) e cansaram de não entender 70% da comunidade.

### Features principais

- 🔍 **OCR ao vivo** do chat do Dofus Retro (Tesseract)
- 🌐 **Tradução em tempo real** FR→PT (Google Translate ou DeepL)
- 💬 **Quick input**: escreve em PT, manda em FR no chat
- 🕵️ **Modo Lurker**: somente leitura, bloqueia auto-send
- 📜 **Histórico persistente** de até 500 mensagens (cross-session)
- 🎨 **Identidade visual Dofus Retro** (tema bege/dourado)
- 🌍 **App em 4 idiomas**: PT-BR, EN, FR, ES
- 🎮 **Multi-monitor** com posicionamento por monitor
- 🔄 **Auto-update** via GitHub Releases (a partir da v1.1.0)

### Como instalar

1. Vai em [Releases](https://github.com/afkdino/dofusinator/releases) e baixa o **`Dofusinator-Setup.exe`** mais recente
2. Roda o instalador (não pede admin/UAC)
3. App abre automaticamente após instalar
4. Configura o **caminho do Tesseract** e o **perímetro de captura** (botão F2)

> ⚠️ **Pré-requisito**: precisa ter o [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) instalado no Windows com o pacote de idioma francês (`fra`).

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

Dofusinator is a Windows desktop app that captures **Dofus Retro** chat in real time and translates **French → Portuguese** using OCR (Tesseract). It displays translations in an overlay window on top of the game, and lets you send messages in Portuguese that are automatically translated to French and typed into the in-game chat.

Built by and for Brazilians who play on French servers (Boune, Crocabulia, etc.) and got tired of not understanding 70% of the community chatter.

### Key features

- 🔍 **Live OCR** of Dofus Retro chat (Tesseract)
- 🌐 **Real-time translation** FR→PT (Google Translate or DeepL)
- 💬 **Quick input**: type in Portuguese, send in French to the chat
- 🕵️ **Lurker mode**: read-only, blocks auto-send
- 📜 **Persistent history** of up to 500 messages (cross-session)
- 🎨 **Dofus Retro visual identity** (beige/gold theme)
- 🌍 **App in 4 languages**: PT-BR, EN, FR, ES
- 🎮 **Multi-monitor** support with per-monitor positioning
- 🔄 **Auto-update** via GitHub Releases (from v1.1.0)

### How to install

1. Go to [Releases](https://github.com/afkdino/dofusinator/releases) and download the latest **`Dofusinator-Setup.exe`**
2. Run the installer (no admin/UAC required)
3. App opens automatically after install
4. Configure the **Tesseract path** and **capture area** (F2 button)

> ⚠️ **Prerequisite**: requires [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) installed on Windows with the French language pack (`fra`).

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
