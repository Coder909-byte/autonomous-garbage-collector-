#pragma once
#include "esp_camera.h"
#include <map>
struct httpd_req_t{std::string type,body,status="200 OK",query;int chunks=0,failAfter=2;bool failSend=false;std::map<std::string,std::string>headers;};
using httpd_handle_t=void*;using httpd_method_t=int;
constexpr int HTTP_GET=0,HTTP_POST=1,HTTPD_403_FORBIDDEN=403,HTTPD_400_BAD_REQUEST=400,HTTPD_500_INTERNAL_SERVER_ERROR=500;
struct httpd_config_t{int server_port=80,ctrl_port=32768,stack_size=4096,send_wait_timeout=5,recv_wait_timeout=5;bool lru_purge_enable=false;};
#define HTTPD_DEFAULT_CONFIG() httpd_config_t{}
struct httpd_uri_t{const char*uri;int method;esp_err_t(*handler)(httpd_req_t*);};
static bool fakeServerFail=false;static int registeredRoutes=0;
static int httpd_start(httpd_handle_t*h,httpd_config_t*){if(fakeServerFail)return ESP_FAIL;*h=reinterpret_cast<void*>(1);return ESP_OK;}
static int httpd_register_uri_handler(httpd_handle_t,httpd_uri_t*){++registeredRoutes;return ESP_OK;}
static int httpd_req_to_sockfd(httpd_req_t*){return 5;}
static int httpd_resp_set_status(httpd_req_t*r,const char*s){r->status=s;return ESP_OK;}
static int httpd_resp_set_type(httpd_req_t*r,const char*s){r->type=s;return ESP_OK;}
static int httpd_resp_set_hdr(httpd_req_t*r,const char*k,const char*v){r->headers[k]=v;return ESP_OK;}
static int httpd_resp_send(httpd_req_t*r,const char*b,int n){if(r->failSend)return ESP_FAIL;r->body.append(b,n);return ESP_OK;}
static int httpd_resp_sendstr(httpd_req_t*r,const char*b){return httpd_resp_send(r,b,strlen(b));}
static int httpd_resp_send_err(httpd_req_t*r,int code,const char*b){r->status=std::to_string(code);return httpd_resp_sendstr(r,b);}
static int httpd_resp_send_chunk(httpd_req_t*r,const char*b,int n){if(r->chunks++>=r->failAfter)return ESP_FAIL;return httpd_resp_send(r,b,n);}
static int httpd_req_get_url_query_str(httpd_req_t*r,char*b,unsigned n){if(r->query.size()>=n)return ESP_FAIL;strcpy(b,r->query.c_str());return ESP_OK;}
static int httpd_query_key_value(char*q,const char*k,char*b,unsigned n){std::string s=q,key=std::string(k)+"=";auto at=s.find(key);if(at==std::string::npos)return ESP_FAIL;auto end=s.find('&',at);auto v=s.substr(at+key.size(),end==std::string::npos?end:end-at-key.size());if(v.size()>=n)return ESP_FAIL;strcpy(b,v.c_str());return ESP_OK;}
