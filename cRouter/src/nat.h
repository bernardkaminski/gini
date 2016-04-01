#ifndef __NAT_H
#define __NAT_H


void toNetworkByteOrder(char *ip, char *result);
char* getIp(void);
int applyDNAT(ip_packet_t *raw_ip, int id);
void applySNAT(char *new_src, ip_packet_t *raw_ip, int id);
void addToNAT(int id, unsigned char *src);
char* getSrcFromNAT(int id);
void printNAT(void);

#endif
