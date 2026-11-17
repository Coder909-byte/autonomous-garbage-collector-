#pragma once
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
static const char* fakePeerIP="192.168.50.20";
static bool fakePeerLookupFail=false;
static int fakePeerFamily=AF_INET;
static socklen_t fakePeerLength=sizeof(sockaddr_in);
static int camera_mock_getpeername(int,struct sockaddr*address,socklen_t *length){
 if(fakePeerLookupFail)return -1;
 address->sa_family=fakePeerFamily;*length=fakePeerLength;
 if(fakePeerFamily==AF_INET)inet_pton(AF_INET,fakePeerIP,&reinterpret_cast<sockaddr_in*>(address)->sin_addr);
 if(fakePeerFamily==AF_INET6)inet_pton(AF_INET6,fakePeerIP,&reinterpret_cast<sockaddr_in6*>(address)->sin6_addr);
 return 0;
}
#define getpeername camera_mock_getpeername
