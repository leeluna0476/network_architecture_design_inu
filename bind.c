#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <stdio.h>
#include <sys/errno.h>

#define ERROR(rv, fname) if (rv == -1) { perror(fname); printf("errno=%d", errno); return 1; }

//IPPROTO_TCP == 6
//#define TCP 6

#define MAX_CONNECTIONS 1
#define PORT 4242
//#define IP_ADDR "192.168.219.64"
//#define IP_ADDR "127.0.0.1"
//#define IP_ADDR "172.30.1.26"
#define IP_ADDR "0.0.0.0"
//#define IP_ADDR "125.188.177.54" // must fail when the socket is bound to this address

// when the socket is unbound to any address, (TCP: RFC 9293)
// If the parameter is unspecified, a passive OPEN will await an incoming connection request to any local IP address and then bind the local IP address of the connection(the client socket) to the particular address that is used.
// => the accepted client socket will be bound to the address of the connection in its local network
// => very reasonable
// => same as binding to 0.0.0.0

void print_sockinfo(struct sockaddr_in *sockaddr) {
	printf("SOCKET INFO=>domain: %d, port: %d, ip: %s\n", \
			sockaddr->sin_family, ntohs(sockaddr->sin_port), inet_ntoa(sockaddr->sin_addr));
}

int	main(void) {
	int socket_tcp = socket(PF_INET, SOCK_STREAM, IPPROTO_TCP);
	ERROR(socket_tcp, "socket")
//	struct sockaddr_in sockaddr = { \
//		sizeof(struct sockaddr_in), PF_INET, htons(PORT), { inet_addr(IP_ADDR) }, 0\
//	};
//	print_sockinfo(&sockaddr);
//	ERROR(bind(socket_tcp, (struct sockaddr *)&sockaddr, sizeof(sockaddr)), "bind")
	ERROR(listen(socket_tcp, MAX_CONNECTIONS), "listen")
	
	struct sockaddr_in recvsock;
	socklen_t recvlen = sizeof(recvsock);
	int clsock = accept(socket_tcp, (struct sockaddr *)&recvsock, &recvlen);
	ERROR(clsock, "accept")
	print_sockinfo(&recvsock);

	while(42);
	close(clsock);
	close(socket_tcp);
	return 0;
}
// check why the other host in the same network as mine cannot access to this process through public ip:forwarded port
