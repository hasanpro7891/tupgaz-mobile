[app]

title = Tüpçüler Kralı
package.name = tupcularkrali
package.domain = com.tupgaz.app

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 2.0.1

requirements = python3,kivy

orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.1.0

fullscreen = 0

android.api = 33
android.minapi = 21
android.ndk = 25c
android.sdk = 33
android.gradle_dependencies = []
android.enable_p4a_flags = --window

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

android.primary_color = 8B0000
android.accent_color = FFD700

win.debug = 0

[buildozer]

log_level = 2
warn_on_root = 1

android.archs = arm64-v8a
