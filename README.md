Whisper Speech-to-Text
Python tool that transcribes audio and video into text and .srt subtitles using OpenAI Whisper. Supports 99+ languages, runs fully offline on CPU or GPU. Optional Telegram bot mode.

Stack: Python 3.9+, faster-whisper, ffmpeg, aiogram



faster-whisper>=1.0.0
ctranslate2>=4.0.0
av>=10.0.0

# 1. Chocolaty installation

  ``Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))``

  ``choco install ffmpeg``
   
# 2. FFmpeg in PATH on Windows
   
  ``where.exe ffmpeg -----  find out and copy the path``

# 3. Change the path to your own.
   
  ``$ffmpegPath = "C:\ffmpeg\bin"``

  ``[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$ffmpegPath", "Machine")``
