[app]
title = WordListen
package.name = wordlisten
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt
source.exclude_dirs = tests, __pycache__, .git, .buildozer
version = 1.0
requirements = python3,kivy==2.3.0,plyer,android

[buildozer]
log_level = 2

[buildozer:android]
android.permissions = INTERNET
android.archs = arm64-v8a, armeabi-v7a
android.api = 31
android.minapi = 21
android.ndk = 25b
android.gradle_dependencies = 'com.google.android.material:material:1.4.0'
p4a.version = 2024.06.0
android.meta_data = android.hardware.audio.output=true

