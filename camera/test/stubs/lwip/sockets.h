#pragma once
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
static const char* fakePeerIP="192.168.50.20";
static int camera_mock_getpeername(int,struct sockaddr*address,socklen_t*){auto peer=reinterpret_cast<sockaddr_in*>(address);inet_pton(AF_INET,fakePeerIP,&peer->sin_addr);return 0;}
#define getpeername camera_mock_getpeername
