#pragma once
#include "Arduino.h"
using esp_err_t=int;
constexpr int ESP_OK=0,ESP_FAIL=-1,ESP_ERR_NO_MEM=0x101;
constexpr int LEDC_CHANNEL_0=0,LEDC_TIMER_0=0,PIXFORMAT_JPEG=1,FRAMESIZE_QVGA=5,FRAMESIZE_VGA=8,CAMERA_FB_IN_PSRAM=1,CAMERA_FB_IN_DRAM=0,CAMERA_GRAB_WHEN_EMPTY=0;
struct camera_config_t{int ledc_channel,ledc_timer,pin_d0,pin_d1,pin_d2,pin_d3,pin_d4,pin_d5,pin_d6,pin_d7,pin_xclk,pin_sccb_sda,pin_sccb_scl,pin_vsync,pin_href,pin_pclk,pin_pwdn,pin_reset,xclk_freq_hz,pixel_format,frame_size,jpeg_quality,fb_count,fb_location,grab_mode;};
static camera_config_t lastConfig{};static int fakeInitResult=ESP_OK,fakeFramesReturned=0;static bool fakeCaptureFail=false,fakeSensorFail=false;
static esp_err_t esp_camera_init(camera_config_t*c){lastConfig=*c;return fakeInitResult;}
struct camera_fb_t{uint8_t*buf;unsigned len;int format;};
static camera_fb_t*esp_camera_fb_get(){static uint8_t data[]={0xff,0xd8,0xff,0xd9};static camera_fb_t fb{data,4,PIXFORMAT_JPEG};return fakeCaptureFail?nullptr:&fb;}
static void esp_camera_fb_return(camera_fb_t*){++fakeFramesReturned;}
struct sensor_t{struct{int framesize,quality;}status;int(*set_framesize)(sensor_t*,int);int(*set_quality)(sensor_t*,int);};
static int setSize(sensor_t*s,int v){if(fakeSensorFail)return -1;s->status.framesize=v;return 0;}
static int setQuality(sensor_t*s,int v){if(fakeSensorFail)return -1;s->status.quality=v;return 0;}
static sensor_t*esp_camera_sensor_get(){static sensor_t sensor{{FRAMESIZE_QVGA,14},setSize,setQuality};return &sensor;}
