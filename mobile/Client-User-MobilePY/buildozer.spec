[app]
title = T-Conecta Ciudadano
package.name = tconecta
package.domain = com.tconecta
source.dir = app
source.include_exts = py,png,jpg,kv,atlas,ttf
requirements = python3,flet,httpx,python-jose[cryptography]
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
orientation = portrait
fullscreen = false
