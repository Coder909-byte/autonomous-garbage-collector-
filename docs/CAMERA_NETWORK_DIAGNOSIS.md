# ESP32-CAM network diagnosis

Checked at: 2026-11-17T17:50:35+05:30 (Asia/Kolkata).

This is a snapshot of the network at the recorded time; addresses and connectivity may change after reconnecting or restarting devices.

## Observed

- Active Wi-Fi interface: en0.
- Interface IPv4: 192.0.0.1/32; CLAT46 active, NAT64 prefix 64:ff9b::/96.
- Wi-Fi has global IPv6 addresses and an IPv6 default router.
- No normal DHCPv4 lease/address, subnet-mask option or router option was returned by ipconfig.
- No connected 172.20.10.0/28 network route was present. A cached neighbor entry for 172.20.10.3 does not establish the camera's identity or a working IPv4 connection.
- User confirms successful Arduino IDE upload on the Dell and a subsequent serial message: `Camera IP 172.20.10.3; trusted=1; /status /snapshot :81/stream`. This is the last confirmed address, not a fresh serial reading.
- Targeted follow-up: two IPv4 pings to 172.20.10.3 received no replies; Wi-Fi-bound curl failed before obtaining any HTTP response.
- The IPv6 link-local default router answered a ping (approximately 13 ms), confirming a working local IPv6 path.
- Direct HTTP GET /status to each address 172.20.10.1 through 172.20.10.14 timed out (three-second timeout per request; no HTTP proxy).
- TCP connections to port 81 at those same addresses did not succeed (two-second timeout).
- rover-camera.local returned no IPv4 answer during the bounded lookup.
- No USB UART /dev/cu device was present; Bluetooth serial devices were not opened.

## Interpretation and limits

At the time of diagnosis, the Mac connection used an IPv6 transition configuration instead of the previously documented native private IPv4 address 172.20.10.3/28. 192.0.0.1 is a local CLAT service-continuity address; it is outside the camera's trusted 172.20.10.0/28 subnet. The present setup does not demonstrate a usable trusted IPv4 path to the camera.

This does not prove that the iPhone universally lacks DHCPv4 or blocks all client communication. The user has confirmed a successful camera upload and subsequent Wi-Fi connection at 172.20.10.3 with trusted=1. Its current power/initialization/association and DHCP address have not been freshly established by these diagnostics. No camera HTTP service was positively identified from the Mac. Reconfirm the current IP in the Dell Serial Monitor (without re-uploading). If the Dell has a usable 172.20.10.1–14 address, test http://<current-camera-ip>/status there. Success from the Dell would distinguish the Mac IPv4 configuration problem from a blanket hotspot peer restriction. Firmware compilation and upload need not be repeated for this diagnosis.

If the hotspot cannot provide a usable local IPv4 connection or permits no peer traffic, use a private 2.4 GHz Wi-Fi router with DHCPv4 and peer communication enabled. Confirm both devices have usable private IPv4 addresses in the camera's configured trusted subnet. A different router subnet or credentials would require a separate camera configuration/build and later authorized upload; do not widen the existing hotspot allowlist as a workaround.

## Preservation

This diagnosis did not modify firmware, Wi-Fi credentials, the ZIP archive, routes, interface configuration, firewall settings or tracked source files. No serial ports were opened and no firmware was uploaded. Only this non-secret documentation summary is retained in Git; raw network diagnostics remain in ignored local artifacts.

References: [RFC 7335](https://www.rfc-editor.org/rfc/rfc7335.html), [RFC 6877](https://www.rfc-editor.org/rfc/rfc6877.html).

Camera configuration and setup: [camera README](../camera/README.md) and [Dell Arduino guide](ESP32_CAM_ARDUINO_WINDOWS.md).
