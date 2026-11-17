#pragma once
// Deterministic synthetic configuration, selected only by CAMERA_HOST_TEST.
// Host tests never include the operator's local Wi-Fi configuration.
static const char *fakeCameraSSID="";
static const char *fakeCameraPassword="";
static const char *fakeCameraNetwork="172.20.10.0";
static const char *fakeCameraMask="255.255.255.240";
#define CAMERA_WIFI_SSID fakeCameraSSID
#define CAMERA_WIFI_PASSWORD fakeCameraPassword
#define CAMERA_TRUSTED_NETWORK fakeCameraNetwork
#define CAMERA_TRUSTED_MASK fakeCameraMask
#define CAMERA_HOSTNAME "rover-camera-test"
