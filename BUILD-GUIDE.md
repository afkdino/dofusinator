# 🛠️ Dofusinator — Build Guide

Como gerar o `.exe` final + instalador pra distribuir pros amigos.

---

## 📋 Pré-requisitos (fazer 1x só)

### 1. Python 3.10+ no PATH

Você já tem (já que tá rodando o app). Confere com:
```bash
python --version
```

### 2. PyInstaller

O `build.bat` instala automático na primeira vez. Mas se quiser fazer manual:
```bash
pip install pyinstaller
```

### 3. Inno Setup 6.1+

Baixa e instala: **https://jrsoftware.org/isdl.php**

Recomendo a versão **Inno Setup 6.x** (6.1 ou superior — precisa do `TDownloadWizardPage` pra download do Tesseract).

> Local default da instalação: `C:\Program Files (x86)\Inno Setup 6\` — o `build.bat` procura nesse caminho.

### 4. (Opcional) UPX

Reduz o tamanho final do `.exe` em ~30%. Baixa em: https://upx.github.io/

Coloca o `upx.exe` no PATH ou na pasta do projeto. Sem UPX o build segue normal, só fica maior.

---

## 📁 Estrutura esperada

Antes de buildar, o projeto deve estar assim:

```
dofusbr-translator/
├── src/                     ← código (com app_info.py)
├── assets/
│   └── icon.ico             ← OBRIGATÓRIO pra ter ícone
├── sounds/                  ← seus pop1.wav, pop2.wav, pop3.wav
├── slang_dictionary.json
├── requirements.txt
├── build_system/
│   ├── Dofusinator.spec
│   ├── installer.iss
│   ├── tesseract_install.iss
│   ├── version_info.txt
│   └── build.bat            ← roda esse
└── BUILD-GUIDE.md           ← este arquivo
```

---

## 🚀 Buildar (modo simples)

Abre um cmd na pasta `build_system/`:

```bash
cd build_system
build.bat
```

Ele faz tudo automático:
1. ✅ Verifica pré-requisitos
2. ✅ Compila o `.exe` com PyInstaller (1-3 min)
3. ✅ Gera o instalador com Inno Setup
4. ✅ Output em `dist/`

### Saída esperada

```
dist/
├── Dofusinator.exe                 ← o app sozinho (~120 MB)
└── DofusinatorSetup_1.0.0.exe      ← instalador pra distribuir (~70 MB)
```

---

## 🎯 Comandos avançados

```bash
build.bat clean       # Limpa builds antigos
build.bat exe         # Só gera o .exe (sem instalador)
build.bat installer   # Só gera o instalador (assume .exe existe)
```

---

## 🐛 Troubleshooting

### "PyInstaller falhou"
- Roda `pip install --upgrade pyinstaller`
- Verifica se todas as deps de `requirements.txt` estão instaladas: `pip install -r requirements.txt`

### "Inno Setup não encontrado"
- Confirma que instalou em `C:\Program Files (x86)\Inno Setup 6\`
- Se instalou em outro lugar, edita o `build.bat` linha que define `ISCC_PATH`

### ".exe gerado mas não abre"
- Roda no cmd pra ver erro: `dist\Dofusinator.exe`
- Se aparecer "missing module X", adiciona X em `hidden_imports` no `Dofusinator.spec`

### "ANTIVÍRUS marca como vírus"
- **Esperado!** Apps Python empacotados com `keyboard`/`mouse`/`pystray` são frequentemente falsos positivos.
- Soluções:
  1. Adiciona exceção no Windows Defender
  2. Submete pra Microsoft em https://www.microsoft.com/wdsi/filesubmission
  3. Pra distribuição séria: assinar com certificado pago (~$200/ano)

### "App abre mas tray icon não aparece"
- Confirma que `assets/icon.ico` existe e foi incluído no spec
- Verifica `debug.log` (raiz do `%LocalAppData%\Dofusinator\`)

### "Tesseract não foi instalado"
- O instalador oferece baixar, mas se internet falhar, instala manual em https://github.com/UB-Mannheim/tesseract/wiki
- Importante: **incluir os language packs** `fra`, `por`, `spa`, `eng`

---

## 📦 Como distribuir

Depois de buildar, você tem `dist/DofusinatorSetup_1.0.0.exe`.

1. **Pra amigos próximos:** manda o `.exe` direto pelo Discord/WhatsApp/Drive
2. **Pra Discord do servidor:** sobe num drive (Google Drive, MEGA, Mediafire) e cola o link

### Mensagem sugerida pra mandar

```
Galera, Dofusinator (tradutor de chat PT↔FR pro Dofus Retro):

📥 Download: [LINK]
🛡️ Antivírus pode reclamar — falso positivo (libs Python pra hotkey global).
   Adicione exceção no Windows Defender se reclamar.
📋 Tesseract: o instalador baixa automático (~50MB extra)
🎮 Hotkey padrão pra abrir tradutor: Ctrl+Shift+T
```

---

## 🔄 Atualizando versões futuras

Pra release v1.1 (exemplo):

1. Atualiza `src/app_info.py` → `APP_VERSION = "1.1.0"`
2. Atualiza `build_system/installer.iss` → `#define APP_VERSION "1.1.0"`
3. Atualiza `build_system/version_info.txt` → `filevers=(1, 1, 0, 0)`
4. Roda `build.bat`

---

## 📚 Documentação das ferramentas

- [PyInstaller docs](https://pyinstaller.org/en/stable/)
- [Inno Setup docs](https://jrsoftware.org/ishelp/)
- [Tesseract Windows builds](https://github.com/UB-Mannheim/tesseract/wiki)

Boa sorte e bora distribuir! 🎮🚀
