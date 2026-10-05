[app]

title = Hesabddary
package.name = hesabddary
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,db

version = 1.0

requirements = python3,kivy

orientation = portrait

fullscreen = 0

[buildozer]

log_level = 2
warn_on_root = 1

[buildozer:android]

android.api = 35
android.minapi = 21
android.archs = arm64-v8a
