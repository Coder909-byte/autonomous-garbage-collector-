#include <Arduino.h>
#include <WiFi.h>
#include <ESPmDNS.h>
#include <esp_camera.h>
#include <esp_http_server.h>
#include <atomic>
#include <lwip/sockets.h>
#include "board_ai_thinker.h"
#include "camera_policy.h"
#if __has_include("secrets.h")
#include "secrets.h"
#else
#include "config.example.h"
#endif

static bool ready=false, hasPSRAM=false, configOK=false;
static std::atomic<bool> streaming{false};
static SemaphoreHandle_t cameraLock=nullptr;
static httpd_handle_t controlServer=nullptr, streamServer=nullptr;
static cam::Retry retry;
static IPAddress trusted,mask;
static int width=320,quality=14;
static bool networkAllowed(IPAddress ip) { return (uint32_t(ip)&uint32_t(mask))==uint32_t(trusted); }
static bool allowed(httpd_req_t *req) {
  struct sockaddr_in peer={};socklen_t len=sizeof(peer);
  if (!configOK || WiFi.status()!=WL_CONNECTED || !networkAllowed(WiFi.localIP()) ||
      getpeername(httpd_req_to_sockfd(req),reinterpret_cast<sockaddr*>(&peer),&len)!=0 ||
      !networkAllowed(IPAddress(peer.sin_addr.s_addr))) {
    httpd_resp_send_err(req,HTTPD_403_FORBIDDEN,"Trusted WLAN only");return false;
  }
  httpd_resp_set_hdr(req,"Cache-Control","no-store");return true;
}
static esp_err_t unavailable(httpd_req_t *req,const char *reason) {
  httpd_resp_set_status(req,"503 Service Unavailable");return httpd_resp_sendstr(req,reason);
}
struct FrameIO {
  httpd_req_t *req;
  camera_fb_t *get() { return esp_camera_fb_get(); }
  void unavailable() { ::unavailable(req,"Camera capture unavailable"); }
  bool send(camera_fb_t *fb,bool multipart) {
    if (fb->format!=PIXFORMAT_JPEG) return false;
    if (!multipart) { httpd_resp_set_type(req,"image/jpeg");return httpd_resp_send(req,reinterpret_cast<char*>(fb->buf),fb->len)==ESP_OK; }
    char header[120];int n=cam::partHeader(header,sizeof(header),fb->len);
    return n>0 && n<static_cast<int>(sizeof(header)) && httpd_resp_send_chunk(req,header,n)==ESP_OK &&
      httpd_resp_send_chunk(req,reinterpret_cast<char*>(fb->buf),fb->len)==ESP_OK;
  }
  void release(camera_fb_t *fb) { esp_camera_fb_return(fb); }
};
static esp_err_t statusHandler(httpd_req_t *req) {
  if (!allowed(req)) return ESP_FAIL;
  char body[300];snprintf(body,sizeof(body),"{\"v\":1,\"board\":\"AI_THINKER_SUPPORTED_UNVERIFIED\",\"ready\":%s,\"streaming\":%s,\"psram\":%s,\"width\":%d,\"quality\":%d,\"ip\":\"%s\"}",
    ready?"true":"false",streaming?"true":"false",hasPSRAM?"true":"false",width,quality,WiFi.localIP().toString().c_str());
  httpd_resp_set_type(req,"application/json");return httpd_resp_sendstr(req,body);
}
static esp_err_t snapshotHandler(httpd_req_t *req) {
  if (!allowed(req)) return ESP_FAIL;
  if (!ready || xSemaphoreTake(cameraLock,pdMS_TO_TICKS(250))!=pdTRUE) {
    return ::unavailable(req,"Camera busy or unavailable");
  }
  FrameIO io{req};bool ok=cam::frame(io,false);xSemaphoreGive(cameraLock);return ok?ESP_OK:ESP_FAIL;
}
static esp_err_t streamHandler(httpd_req_t *req) {
  if (!allowed(req)) return ESP_FAIL;
  if (!ready || streaming.exchange(true)) return ::unavailable(req,"Camera busy or unavailable");
  httpd_resp_set_type(req,cam::STREAM_TYPE);
  bool ok=true;
  while (ok && WiFi.status()==WL_CONNECTED && networkAllowed(WiFi.localIP())) {
    if (xSemaphoreTake(cameraLock,pdMS_TO_TICKS(500))!=pdTRUE) break;
    FrameIO io{req};ok=cam::frame(io,true);xSemaphoreGive(cameraLock);vTaskDelay(pdMS_TO_TICKS(20));
  }
  streaming=false;return ESP_FAIL; // closes failed/disconnected socket; frame always returned
}
static bool decimal(const char *s,int &v) {
  if (!*s) return false;
  v=0;
  for (;*s;++s) { if (*s<'0'||*s>'9'||v>1000) return false;v=v*10+(*s-'0'); }return true;
}
static esp_err_t settingsHandler(httpd_req_t *req) {
  if (!allowed(req)) return ESP_FAIL;
  char query[80],sizeValue[12],qValue[12];int w=0,q=0;
  if (httpd_req_get_url_query_str(req,query,sizeof(query))!=ESP_OK ||
      httpd_query_key_value(query,"width",sizeValue,sizeof(sizeValue))!=ESP_OK ||
      httpd_query_key_value(query,"quality",qValue,sizeof(qValue))!=ESP_OK ||
      !decimal(sizeValue,w)||!decimal(qValue,q)||!cam::settings(w,q,hasPSRAM)) {
    return httpd_resp_send_err(req,HTTPD_400_BAD_REQUEST,"width=320 or PSRAM 640; quality=10..40");
  }
  if (!ready || streaming || xSemaphoreTake(cameraLock,0)!=pdTRUE)
    return ::unavailable(req,"Disconnect stream before changing settings");
  sensor_t *sensor=esp_camera_sensor_get();bool ok=sensor && sensor->set_framesize(sensor,w==640?FRAMESIZE_VGA:FRAMESIZE_QVGA)==0 && sensor->set_quality(sensor,q)==0;
  if (sensor) { width=sensor->status.framesize==FRAMESIZE_VGA?640:320;quality=sensor->status.quality; }
  xSemaphoreGive(cameraLock);
  if (!ok) return httpd_resp_send_err(req,HTTPD_500_INTERNAL_SERVER_ERROR,"Sensor rejected settings; reconnect/reboot and inspect");
  return statusHandler(req);
}
static void add(httpd_handle_t server,const char *uri,httpd_method_t method,esp_err_t (*handler)(httpd_req_t*)) {
  httpd_uri_t route={};route.uri=uri;route.method=method;route.handler=handler;
  if (httpd_register_uri_handler(server,&route)!=ESP_OK) Serial.printf("FAULT HTTP route %s\n",uri);
}
static void servers() {
  if (controlServer && streamServer) return;
  httpd_config_t cfg=HTTPD_DEFAULT_CONFIG();cfg.server_port=80;cfg.ctrl_port=32768;cfg.stack_size=8192;cfg.send_wait_timeout=3;cfg.recv_wait_timeout=3;cfg.lru_purge_enable=true;
  if (!controlServer && httpd_start(&controlServer,&cfg)==ESP_OK) {
    add(controlServer,"/status",HTTP_GET,statusHandler);add(controlServer,"/snapshot",HTTP_GET,snapshotHandler);add(controlServer,"/settings",HTTP_POST,settingsHandler);
  }
  cfg.server_port=81;cfg.ctrl_port=32769;
  if (!streamServer && httpd_start(&streamServer,&cfg)==ESP_OK) add(streamServer,"/stream",HTTP_GET,streamHandler);
  if (!controlServer||!streamServer) Serial.println("FAULT HTTP allocation/start; retry on subsequent loop");
}
void setup() {
  Serial.begin(115200);Serial.println("CAMERA supported AI-Thinker configuration; VERIFY actual hardware before upload");
  cameraLock=xSemaphoreCreateMutex();hasPSRAM=psramFound();width=hasPSRAM?640:320;quality=hasPSRAM?12:14;
  camera_config_t c={};c.ledc_channel=LEDC_CHANNEL_0;c.ledc_timer=LEDC_TIMER_0;
  c.pin_d0=camera_board::D0;c.pin_d1=camera_board::D1;c.pin_d2=camera_board::D2;c.pin_d3=camera_board::D3;
  c.pin_d4=camera_board::D4;c.pin_d5=camera_board::D5;c.pin_d6=camera_board::D6;c.pin_d7=camera_board::D7;
  c.pin_xclk=camera_board::XCLK;c.pin_sccb_sda=camera_board::SIOD;c.pin_sccb_scl=camera_board::SIOC;
  c.pin_vsync=camera_board::VSYNC;c.pin_href=camera_board::HREF;c.pin_pclk=camera_board::PCLK;c.pin_pwdn=camera_board::PWDN;c.pin_reset=camera_board::RESET;
  c.xclk_freq_hz=20000000;c.pixel_format=PIXFORMAT_JPEG;c.frame_size=hasPSRAM?FRAMESIZE_VGA:FRAMESIZE_QVGA;
  c.jpeg_quality=quality;c.fb_count=hasPSRAM?2:1;c.fb_location=hasPSRAM?CAMERA_FB_IN_PSRAM:CAMERA_FB_IN_DRAM;c.grab_mode=CAMERA_GRAB_WHEN_EMPTY;
  esp_err_t result=cameraLock?esp_camera_init(&c):ESP_ERR_NO_MEM;ready=result==ESP_OK;
  Serial.printf("Camera init=0x%x PSRAM=%d heap=%u width=%d quality=%d ready=%d\n",result,hasPSRAM,ESP.getFreeHeap(),width,quality,ready);
  configOK=cam::credentials(CAMERA_WIFI_SSID,CAMERA_WIFI_PASSWORD) && trusted.fromString(CAMERA_TRUSTED_NETWORK) && mask.fromString(CAMERA_TRUSTED_MASK);
  // Explicit /24 trusted subnet; reject wildcard/public/ambiguous networks.
  configOK=configOK && mask==IPAddress(255,255,255,0) && trusted[3]==0 &&
    (trusted[0]==10 || (trusted[0]==192 && trusted[1]==168) || (trusted[0]==172 && trusted[1]>=16 && trusted[1]<=31));
  if (!configOK) { Serial.println("FAULT configure secrets.h: trusted RFC1918 /24 and WPA2 password required; Wi-Fi disabled");return; }
  WiFi.mode(WIFI_STA);WiFi.setAutoReconnect(false);WiFi.setHostname(CAMERA_HOSTNAME);
}
void loop() {
  if (!configOK) { delay(100);return; }
  bool connected=WiFi.status()==WL_CONNECTED;
  static bool wasConnected=false;
  if (retry.tick(millis(),connected)) {
    WiFi.disconnect();WiFi.begin(CAMERA_WIFI_SSID,CAMERA_WIFI_PASSWORD);Serial.printf("Wi-Fi connect attempt %u/5\n",retry.attempts);
  }
  if (connected && !wasConnected) {
    Serial.printf("Camera IP %s; trusted=%d; /status /snapshot :81/stream\n",WiFi.localIP().toString().c_str(),networkAllowed(WiFi.localIP()));
    if (networkAllowed(WiFi.localIP())) { MDNS.begin(CAMERA_HOSTNAME);MDNS.addService("http","tcp",80); }
  }
  if (connected && networkAllowed(WiFi.localIP())) servers();
  if (!connected && wasConnected) { MDNS.end();Serial.println("Wi-Fi disconnected; streaming closes; bounded reconnect begins"); }
  wasConnected=connected;delay(100);
}
