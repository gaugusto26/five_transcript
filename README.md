# Five Transcript

Aplicativo Windows instalável para transcrever áudio e vídeo localmente, usando `faster-whisper` e FFmpeg. A interface permite selecionar o arquivo, transcrever, copiar o resultado e salvar em TXT.

## Requisitos para gerar a entrega

- Windows 10/11 64 bits
- Python 3.11 64 bits no computador de build
- [Inno Setup 6](https://jrsoftware.org/isdl.php)
- `ffmpeg.exe` 64 bits em `assets/ffmpeg/bin/ffmpeg.exe`

O modelo multilíngue `medium` do faster-whisper é baixado pelo script na primeira geração e passa a integrar o instalador, permitindo uso offline depois da instalação. Ele oferece qualidade superior para entrevistas em português, em troca de um instalador maior e maior tempo de transcrição. Reserve alguns GB de espaço durante o build.

## Gerar o Setup.exe

No PowerShell, dentro desta pasta:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build.ps1
```

O script instala as dependências de build, baixa o modelo local (quando necessário), gera a pasta de distribuição com PyInstaller e cria `output/Five-Transcript-Setup.exe` com o Inno Setup.

Para gerar novamente sem baixar o modelo, desde que ele já exista:

```powershell
.\build.ps1 -SkipModelDownload
```

## Personalização antes da geração

- Em `app.py`, altere o valor de `SUPPORT_CONTACT` para o canal definitivo de suporte.
- Para exibir a logo no aplicativo, coloque uma imagem PNG em `assets/logo.png` (preferencialmente com fundo transparente e até 64 pixels de altura).
- Para o ícone do aplicativo, do atalho e do instalador, coloque uma versão `.ico` em `assets/icon.ico`. O arquivo ICO deve conter, idealmente, os tamanhos 16, 32, 48 e 256 pixels.

## Teste de aceitação sugerido

1. Instale `output/Five-Transcript-Setup.exe` em uma máquina sem Python.
2. Abra pelo atalho criado pelo instalador.
3. Selecione um MP3 e um MP4 com fala em português.
4. Confirme que a transcrição aparece, pode ser copiada e é salva em UTF-8 como TXT.
5. Desconecte da internet e repita com um arquivo curto para confirmar a operação local.

## Contato de suporte

O rodapé atualmente mostra `Suporte: contato a confirmar`, conforme solicitado. Atualize essa frase em `app.py` quando o contato definitivo estiver disponível.

## Atualizações do aplicativo

O aplicativo verifica, em segundo plano, a versão mais recente publicada nas [GitHub Releases](https://github.com/gaugusto26/five_transcript/releases). Quando encontra uma versão maior, ele avisa a pessoa usuária e oferece abrir a página de download. Sem internet, o aplicativo abre e funciona normalmente.

> Importante: o instalador `1.0.0` gerado antes da inclusão desse recurso não possui a verificação de atualizações. A versão `1.1.0` já inclui esse mecanismo, a barra de progresso e o modelo de transcrição `medium`.

### Publicar uma atualização

1. Em `app.py`, aumente `APP_VERSION` (por exemplo, de `1.0.1` para `1.0.2`).
2. Em `installer/FiveTranscript.iss`, atualize `MyAppVersion` para a mesma versão.
3. Gere novamente o instalador com `./build.ps1 -SkipModelDownload`.
4. No GitHub, crie uma Release com a tag `v<versão>` e anexe `output/Five-Transcript-Setup.exe`.

O aplicativo compara a versão instalada com a tag da Release. Ele apenas notifica: o download só é aberto após confirmação da pessoa usuária.
