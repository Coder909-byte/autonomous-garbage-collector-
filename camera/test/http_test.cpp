// Compile the real camera firmware/HTTP handlers against host boundary mocks.
#define CAMERA_HOST_TEST 1
#include "../src/main.cpp"
#include <assert.h>
static void reset(){ready=true;configOK=true;hasPSRAM=true;streaming=false;fakeLockAvailable=true;fakeFramesReturned=0;fakeCaptureFail=false;fakeSensorFail=false;fakePeerIP="192.168.50.20";fakePeerLookupFail=false;fakePeerFamily=AF_INET;fakePeerLength=sizeof(sockaddr_in);fakeOnTaskDelay=nullptr;WiFi.state=WL_CONNECTED;WiFi.ip=IPAddress(192,168,50,10);assert(trustedNetwork.configure("192.168.50.0","255.255.255.0"));cameraLock=xSemaphoreCreateMutex();}
static void hotspot(){reset();assert(trustedNetwork.configure("172.20.10.0","255.255.255.240"));WiFi.ip=IPAddress(172,20,10,2);fakePeerIP="172.20.10.3";}
static void rejectAll(){
 const int returned=fakeFramesReturned,oldWidth=width,oldQuality=quality;
 for(auto handler:{statusHandler,snapshotHandler,streamHandler,settingsHandler}){
  httpd_req_t req;req.query="width=320&quality=14";
  assert(handler(&req)==ESP_FAIL);assert(req.status=="403");
  assert(req.headers.count("Cache-Control")==0);
 }
 assert(fakeFramesReturned==returned&&width==oldWidth&&quality==oldQuality&&!streaming);
}
static void networkTests(){
 hotspot();httpd_req_t req;assert(statusHandler(&req)==ESP_OK);assert(req.headers["Cache-Control"]=="no-store");
 req={};assert(snapshotHandler(&req)==ESP_OK);assert(req.type=="image/jpeg");
 req={};req.query="width=320&quality=14";assert(settingsHandler(&req)==ESP_OK);
 req={};assert(streamHandler(&req)==ESP_FAIL);assert(req.type==cam::STREAM_TYPE&&fakeFramesReturned==3);
 for(const char *ip:{"172.20.10.0","172.20.10.15","172.20.10.16","172.20.10.255","172.20.11.3","192.168.50.3","8.8.8.8","127.0.0.1","169.254.10.3","224.0.0.1","0.0.0.0","255.255.255.255"}){
  hotspot();fakePeerIP=ip;rejectAll();
  hotspot();assert(WiFi.ip.fromString(ip));rejectAll();
 }
 // Both the camera and client must be usable hosts of the same configured subnet.
 hotspot();WiFi.ip=IPAddress(172,20,10,14);fakePeerIP="172.20.10.1";req={};assert(statusHandler(&req)==ESP_OK);
 hotspot();WiFi.state=0;rejectAll();
 hotspot();configOK=false;rejectAll();
 hotspot();fakePeerLookupFail=true;rejectAll();
 hotspot();fakePeerFamily=AF_INET6;rejectAll();
 hotspot();fakePeerLength=0;rejectAll();
 // ESP-IDF 4.4's HTTP listener is dual-stack: mapped IPv4 must use the same policy.
 hotspot();fakePeerFamily=AF_INET6;fakePeerLength=sizeof(sockaddr_in6);fakePeerIP="::ffff:172.20.10.3";
 for(auto handler:{statusHandler,snapshotHandler,streamHandler,settingsHandler}){
  req={};req.query="width=320&quality=14";handler(&req);assert(req.status=="200 OK");
 }
 for(const char *ip:{"::ffff:172.20.10.0","::ffff:172.20.10.15","::ffff:172.20.10.16","::ffff:192.168.50.3","::ffff:127.0.0.1","::ffff:169.254.1.1","::ffff:224.0.0.1","::ffff:8.8.8.8","::","::1","fe80::1","fd00::1","ff02::1","::172.20.10.3","2001:db8::ac14:a03"}){
  hotspot();fakePeerFamily=AF_INET6;fakePeerLength=sizeof(sockaddr_in6);fakePeerIP=ip;rejectAll();
 }
 hotspot();fakePeerFamily=AF_INET6;fakePeerLength=sizeof(sockaddr_in6)-1;fakePeerIP="::ffff:172.20.10.3";rejectAll();
 reset();fakePeerFamily=AF_INET6;fakePeerLength=sizeof(sockaddr_in6);fakePeerIP="::ffff:192.168.50.254";req={};assert(statusHandler(&req)==ESP_OK);
 fakePeerIP="::ffff:192.168.51.3";rejectAll();
 hotspot();assert(!trustedNetwork.configure("172.20.10.0","255.255.255.241"));rejectAll();
 hotspot();assert(!trustedNetwork.configure("172.20.10.3","255.255.255.240"));rejectAll();
 // Shifted /28 verifies the real IPAddress/socket conversion, not just a .0 special case.
 hotspot();assert(trustedNetwork.configure("172.20.10.16","255.255.255.240"));WiFi.ip=IPAddress(172,20,10,17);fakePeerIP="172.20.10.30";req={};assert(statusHandler(&req)==ESP_OK);fakePeerIP="172.20.10.31";rejectAll();
 reset();WiFi.ip=IPAddress(192,168,50,254);fakePeerIP="192.168.50.1";req={};assert(statusHandler(&req)==ESP_OK);
 for(const char *ip:{"192.168.50.0","192.168.50.255","192.168.51.1"}){
  reset();fakePeerIP=ip;rejectAll();reset();assert(WiFi.ip.fromString(ip));rejectAll();
 }
 // A live stream stops and returns its frame if Wi-Fi drops or the station leaves the subnet.
 hotspot();req={};req.failAfter=100;fakeOnTaskDelay=[](){WiFi.state=0;};
 assert(streamHandler(&req)==ESP_FAIL);assert(fakeFramesReturned==1&&!streaming&&fakeLockAvailable);
 hotspot();req={};req.failAfter=100;fakeOnTaskDelay=[](){WiFi.ip=IPAddress(172,20,10,16);};
 assert(streamHandler(&req)==ESP_FAIL);assert(fakeFramesReturned==1&&!streaming&&fakeLockAvailable);
 fakeOnTaskDelay=nullptr;
 // Setup uses the actual production validator and never enables an AP.
 fakeCameraSSID="host-test";fakeCameraPassword="test-only-password";
 for(const char *mask:{"255.255.255.240","255.255.255.0"}){
  fakeCameraMask=mask;WiFi.modeCalls=0;setup();
  assert(configOK&&WiFi.modeCalls==1&&WiFi.lastMode==WIFI_STA&&!WiFi.autoReconnect);
 }
 for(const char *mask:{"255.255.255.241","255.255.255.248","0.0.0.0",""}){
  fakeCameraMask=mask;WiFi.modeCalls=0;setup();assert(!configOK&&WiFi.modeCalls==0);rejectAll();
 }
 fakeCameraMask="255.255.255.240";
 for(const char *base:{"172.20.10.3","127.0.0.0","169.254.10.0","224.0.0.0","8.8.8.0","172.20.10.0/28"}){
  fakeCameraNetwork=base;WiFi.modeCalls=0;setup();assert(!configOK&&WiFi.modeCalls==0);rejectAll();
 }
 fakeCameraNetwork="172.20.10.0";fakeCameraSSID="";fakeCameraPassword="";
 WiFi.modeCalls=0;setup();assert(!configOK&&WiFi.modeCalls==0);rejectAll();
}
int main(){
 reset();httpd_req_t status;assert(statusHandler(&status)==ESP_OK);assert(status.type=="application/json");assert(status.body.find("\"ready\":true")!=std::string::npos);
 httpd_req_t snap;assert(snapshotHandler(&snap)==ESP_OK);assert(snap.type=="image/jpeg");assert(snap.body.size()==4&&fakeFramesReturned==1);
 snap={};snap.failSend=true;assert(snapshotHandler(&snap)==ESP_FAIL);assert(fakeFramesReturned==2&&fakeLockAvailable);
 fakeCaptureFail=true;snap={};snapshotHandler(&snap);assert(snap.status.find("503")==0&&fakeFramesReturned==2);fakeCaptureFail=false;
 httpd_req_t stream;assert(streamHandler(&stream)==ESP_FAIL);assert(stream.type==cam::STREAM_TYPE);assert(stream.body.find("--roverframe\r\nContent-Type: image/jpeg\r\nContent-Length: 4")!=std::string::npos);assert(!streaming&&fakeLockAvailable&&fakeFramesReturned==4);
 streaming=true;stream={};streamHandler(&stream);assert(stream.status.find("503")==0);streaming=false;
 WiFi.state=0;stream={};assert(streamHandler(&stream)==ESP_FAIL);assert(stream.status=="403");WiFi.state=WL_CONNECTED;
 fakePeerIP="192.168.51.20";status={};assert(statusHandler(&status)==ESP_FAIL);assert(status.status=="403");fakePeerIP="192.168.50.20";
 httpd_req_t setting;setting.query="width=640&quality=12";assert(settingsHandler(&setting)==ESP_OK);assert(width==640&&quality==12);
 for(const char*q:{"width=800&quality=12","width=320&quality=1","width=abc&quality=14","width=320"}){setting={};setting.query=q;settingsHandler(&setting);assert(setting.status=="400");}
 hasPSRAM=false;setting={};setting.query="width=640&quality=12";settingsHandler(&setting);assert(setting.status=="400");hasPSRAM=true;
 streaming=true;setting={};setting.query="width=320&quality=14";settingsHandler(&setting);assert(setting.status.find("503")==0);streaming=false;
 fakeSensorFail=true;setting={};setting.query="width=320&quality=14";settingsHandler(&setting);assert(setting.status=="500");fakeSensorFail=false;
 fakeLockAvailable=false;snap={};snapshotHandler(&snap);assert(snap.status.find("503")==0);fakeLockAvailable=true;
 controlServer=streamServer=nullptr;fakeServerFail=true;servers();assert(!controlServer&&!streamServer);fakeServerFail=false;servers();assert(controlServer&&streamServer&&registeredRoutes==4);
 fakeMutexFail=true;setup();assert(!ready&&!configOK);fakeMutexFail=false;fakePSRAM=false;fakeInitResult=ESP_FAIL;setup();assert(!ready&&lastConfig.fb_count==1&&lastConfig.fb_location==CAMERA_FB_IN_DRAM);fakeInitResult=ESP_OK;fakePSRAM=true;setup();assert(ready&&lastConfig.fb_count==2&&lastConfig.frame_size==FRAMESIZE_VGA);assert(!configOK); // empty template never exposes Wi-Fi
 networkTests();
 puts("camera real-handler HTTP mocks: PASS (/24 and /28 station/peer checks on all endpoints, mapped IPv4/native IPv6/socket failures, setup validation, disconnected Wi-Fi, stream disconnect/subnet loss, status/snapshot/stream/settings, frame cleanup, PSRAM, station-only mode, empty credentials)");
}
