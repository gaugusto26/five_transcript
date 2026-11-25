param(
    [switch]$SkipModelDownload
)

$ErrorActionPreference = 'Stop'
$env:HF_HUB_DISABLE_PROGRESS_BARS = '1'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Python = Get-Command py -ErrorAction SilentlyContinue
if (-not $Python) {
    throw 'Python Launcher nao encontrado. Instale o Python 3.11 de 64 bits.'
}

if (-not (Test-Path 'assets/ffmpeg/bin/ffmpeg.exe')) {
    $SystemFfmpeg = Get-Command ffmpeg.exe -ErrorAction SilentlyContinue
    if (-not $SystemFfmpeg) {
        throw 'FFmpeg ausente. Instale-o (winget install -e --id Gyan.FFmpeg) e execute este script novamente.'
    }
    New-Item -ItemType Directory -Force -Path 'assets/ffmpeg/bin' | Out-Null
    Copy-Item $SystemFfmpeg.Source 'assets/ffmpeg/bin/ffmpeg.exe'
}

& py -3.11 -m pip install --upgrade pip
& py -3.11 -m pip install -r requirements.txt pyinstaller huggingface_hub

if (-not $SkipModelDownload -and -not (Test-Path 'models/faster-whisper-small/model.bin')) {
    & py -3.11 -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Systran/faster-whisper-small', local_dir='models/faster-whisper-small')"
}

if (-not (Test-Path 'models/faster-whisper-small/model.bin')) {
    throw 'Modelo ausente. Execute sem -SkipModelDownload ou coloque o modelo em models/faster-whisper-small.'
}

& py -3.11 -m PyInstaller --noconfirm --clean five_transcript.spec

$Iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $Iscc) {
    $KnownIsccPaths = @(
        'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
        'C:\Program Files\Inno Setup 6\ISCC.exe',
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    )
    foreach ($KnownIscc in $KnownIsccPaths) {
        if (Test-Path $KnownIscc) {
            $Iscc = Get-Item $KnownIscc
            break
        }
    }
}
if (-not $Iscc) {
    throw 'Inno Setup nao encontrado. Instale-o e execute novamente para gerar o Setup.exe.'
}
& $Iscc.Source 'installer/FiveTranscript.iss'
Write-Host "Instalador gerado em: $Root/output/Five-Transcript-Setup.exe"
