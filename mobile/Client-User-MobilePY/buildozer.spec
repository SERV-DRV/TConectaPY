[app]
title = T-Conecta Ciudadano
package.name = tconecta
package.domain = com.tconecta
version = 1.0.0
source.dir = app
source.include_exts = py,png,jpg,kv,atlas,ttf
requirements = python3,flet,flet-map,httpx,python-jose[cryptography]
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.accept_sdk_license = True
orientation = portrait
fullscreen = false
