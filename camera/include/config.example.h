#pragma once
// Copy to camera/include/secrets.h (ignored). Never commit real credentials.
#define CAMERA_WIFI_SSID ""
#define CAMERA_WIFI_PASSWORD ""
// Explicit canonical RFC1918 /24 or /28 only; use the actual WLAN subnet.
// Verified iPhone hotspot example: network 172.20.10.0, mask 255.255.255.240.
#define CAMERA_TRUSTED_NETWORK "192.168.50.0"
#define CAMERA_TRUSTED_MASK "255.255.255.0"
#define CAMERA_HOSTNAME "rover-camera"
