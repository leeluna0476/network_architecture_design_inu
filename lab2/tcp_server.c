#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <unistd.h>

int create_endpoint(const char *ip_addr, int port) {
	int sockfd = socket(PF_INET, SOCK_STREAM, 0);
	if (sockfd < 0) {
		return -1;
	}
	struct sockaddr_in sockaddr = {\
		sizeof(struct sockaddr_in),\
		PF_INET,\
		htons(port),\
		(struct in_addr){\
			inet_addr(ip_addr),
		},\
		0,\
	};
	if (bind(sockfd, (struct sockaddr *)&sockaddr, sizeof(sockaddr)) < 0) {
		return -1;
	}
	return sockfd;
}

int accept_client(int server_sockfd) {
	struct sockaddr_in recvsockaddr;
	socklen_t recvlen = sizeof(struct sockaddr_in);
	int client_sockfd = accept(server_sockfd, (struct sockaddr *)&recvsockaddr, &recvlen);
	if (client_sockfd < 0) {
		return -1;
	}
	return client_sockfd;
}

#define BUFSIZE 1024
int echo(int client_sockfd) {
	char buf[BUFSIZE];
	while (1) {
		int recvlen = recv(client_sockfd, buf, BUFSIZE - 1, 0);
		if (recvlen < 1) {
			return recvlen;
		}
		buf[recvlen] = '\0';
		write(STDOUT_FILENO, buf, recvlen + 1);
		int sendlen = send(client_sockfd, buf, recvlen + 1, 0);
		if (sendlen < 0) {
			return -1;
		}
		sleep(2);
	}
}

#define IP_ADDR "10.96.98.202"
#define PORT 4242
#define MAX_CONN 1

int main(void) {
	int server_sockfd = create_endpoint(IP_ADDR, PORT);
	if (server_sockfd < 0 || listen(server_sockfd, MAX_CONN) < 0) {
		return 1;
	}
	int client_sockfd = accept_client(server_sockfd);
	if (client_sockfd < 0) {
		return 1;
	}
	int ret = echo(client_sockfd);
	sleep(5);
	close(client_sockfd);
	sleep(5);
	close(server_sockfd);
	return ret;
}
