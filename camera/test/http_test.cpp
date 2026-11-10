// Compile the real camera firmware/HTTP handlers against host boundary mocks.
#include "../src/main.cpp"
#include <assert.h>
static void reset(){ready=true;configOK=true;hasPSRAM=true;streaming=false;fakeLockAvailable=true;fakeFramesReturned=0;fakeCaptureFail=false;fakeSensorFail=false;fakePeerIP="192.168.50.20";WiFi.state=WL_CONNECTED;trusted=IPAddress(192,168,50,0);mask=IPAddress(255,255,255,0);cameraLock=xSemaphoreCreateMutex();}
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
 puts("camera real-handler HTTP mocks: PASS (status/snapshot/stream/settings, auth, busy, network/capture/send/init/mutex/server failures, PSRAM allocation, empty secrets)");
}
