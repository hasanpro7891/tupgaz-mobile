"""
Tüpçüler Kralı v2.0m - APK Build Script

Google Colab'da APK oluşturmak için:
1. https://colab.research.google.com/ → File > New notebook
2. Aşağıdaki TEK hücreyi kopyalayıp yapıştırın ▶
3. Zip seçin: C:\\Users\\212\\AppData\\Local\\Temp\\tupgaz_mobile.zip
4. ~20-30 dk bekleyin, APK otomatik inecek
5. https://web.whatsapp.com → APK'yı kendinize gönderin

==============================
COLAB KODU (tek hücre):
==============================
from google.colab import files
!sudo apt-get update -qq 2>/dev/null
!sudo apt-get install -y -qq python3-pip openjdk-11-jdk-headless unzip wget autoconf automake libtool pkg-config 2>/dev/null
!pip install -q buildozer Cython 2>/dev/null
uploaded = files.upload()
import zipfile, os, glob
for fn in uploaded.keys():
    with zipfile.ZipFile(fn, 'r') as zf:
        zf.extractall('/content/tupgaz')
    os.remove(fn)
for root, dirs, files in os.walk('/content/tupgaz'):
    if 'main.py' in files:
        os.chdir(root); break
!buildozer --debug android debug 2>&1 | tee /tmp/build.log
apk = glob.glob('bin/*.apk') or glob.glob('/content/**/*.apk', recursive=True)
if apk:
    files.download(apk[0])
else:
    !tail -80 /tmp/build.log
"""

if __name__ == '__main__':
    print(__doc__)
