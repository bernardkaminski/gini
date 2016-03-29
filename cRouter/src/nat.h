/*
 * nat.h (header file for the NAT module)
 * AUTHOR: Connor Stein
 * VERSION: Beta
 */

#ifndef __NAT_H
#define __NAT_H

int applyDNAT(ip_packet_t *raw_ip, int id);

void applySNAT(char *new_src, ip_packet_t *raw_ip, int id);
void addToNAT(int id, unsigned char *src);
char* getSrcFromNAT(int id);
void printNAT(void);

#endif
