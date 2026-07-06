#!/bin/bash
# Tüpçüler Kralı APK Build Script
# WSL/Linux üzerinde çalıştırın

echo "=== Tüpçüler Kralı APK Builder ==="
echo ""

# Gerekli paketler
sudo apt-get update -qq
sudo apt-get install -y -qq git zip unzip python3-pip openjdk-11-jdk

# Buildozer kurulumu
pip install --user buildozer cython

# APK build
buildozer android debug

echo ""
echo "APK oluşturuldu: bin/"
echo "Dosyayı telefonunuza göndermek için:"
echo "  - WhatsApp Web: https://web.whatsapp.com"
echo "  - Veya 'python -m http.server 8000' ile tarayıcıdan indirin"
