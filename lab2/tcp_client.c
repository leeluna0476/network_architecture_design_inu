#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <stdio.h>

#define IP_ADDR "10.96.98.202"
#define PORT 4242
#define MAX_CONN 1

int create_connection(const char *ip_addr, int port) {
	int sockfd = socket(PF_INET, SOCK_STREAM, 0);
	if (sockfd < 0) {
		perror("socket");
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
	if (connect(sockfd, (struct sockaddr *)&sockaddr, sizeof(sockaddr)) < 0) {
		fprintf(stderr, "[%s:%d]", ip_addr, port);
		perror("connect");
		return -1;
	}
	return sockfd;
}

#define BUFSIZE 1024
int chat(int sockfd) {
	char buf[BUFSIZE];
	while (1) {
		int readlen = read(STDIN_FILENO, buf, BUFSIZE - 1);
		if (readlen < 1) {
			return readlen;
		}
		buf[readlen] = '\0';
		int sendlen = send(sockfd, buf, readlen + 1, 0);
		if (sendlen < 0) {
			perror("send");
			return -1;
		}

		int recvlen = recv(sockfd, buf, BUFSIZE - 1, 0);
		if (recvlen < 1) {
			perror("recv");
			return recvlen;
		}
		buf[recvlen] = '\0';
		int writelen = write(STDOUT_FILENO, buf, recvlen + 1);
		if (writelen < 0) {
			return -1;
		}
	}
}

int main(void) {
	int sockfd = create_connection(IP_ADDR, PORT);
	if (sockfd < 0) {
		return 1;
	}
	int ret = chat(sockfd);
	close(sockfd);
	return ret;
}
