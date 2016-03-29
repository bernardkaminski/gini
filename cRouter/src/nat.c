/*
 * nat.c (source file for the NAT module)
 * AUTHOR: Connor Stein
 * VERSION: Beta, only supports ICMP
 */

#include "grouter.h"
#include "message.h"

#include "ip.h"
#include "nat.h"
#include "message.h"

#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <endian.h>

#define MAX_NAT_ENTRIES 20

typedef struct{
	int icmp_id;
	unsigned char ip_src[4];
} nat_entry;

int nat_table_index = 0;
nat_entry nat_table[MAX_NAT_ENTRIES] = {0};

void applySNAT(char *new_src, ip_packet_t *raw_ip, int id){
	
	char buf[40];
	printf("\nOld IP %s\n", IP2Dot(buf, raw_ip->ip_src)); 

	// Save the NAT entry
	addToNAT(id, raw_ip->ip_src);

	// Apply the new source
	Dot2IP(new_src, raw_ip->ip_src);
	
	// Recompute the checksum
	raw_ip->ip_cksum = 0;
	raw_ip->ip_cksum = htons(checksum((unsigned char *) raw_ip, raw_ip->ip_hdr_len *2));
	printf("\nNew IP %s\n", IP2Dot(buf, raw_ip->ip_src));
	printf("\nNew checksum computed: %d\n", IPVerifyPacket(raw_ip));
}

int applyDNAT(ip_packet_t *raw_ip, int id){

	char *src = getSrcFromNAT(id);
	if(src == NULL) return -1; // No dnat to be applied, wasn't snatted in the first place
	char buf[40];
	printf("\nOld dst %s\n", IP2Dot(buf, raw_ip->ip_dst));

	// Apply new destination 
	Dot2IP(src, raw_ip->ip_dst);

	// Recompute the checksum
	raw_ip->ip_cksum = 0;
	raw_ip->ip_cksum = htons(checksum((unsigned char *) raw_ip, raw_ip->ip_hdr_len *2));
	printf("\nNew dst %s\n", IP2Dot(buf, raw_ip->ip_dst));
	printf("\nNew checksum computed: %d\n", IPVerifyPacket(raw_ip));
	return 0;
}

void addToNAT(int id, unsigned char *src){
	nat_table[nat_table_index].icmp_id = id;
	nat_table[nat_table_index].ip_src[0] = src[0];
	nat_table[nat_table_index].ip_src[1] = src[1];
	nat_table[nat_table_index].ip_src[2] = src[2];
	nat_table[nat_table_index].ip_src[3] = src[3];		
	nat_table_index++; // TODO: make a circular buffer
}

/*
	Given an ICMP Packet ID, look up the corresponding source address from the NAT table
*/
char* getSrcFromNAT(int id){
	int i = 0;
	while(i < MAX_NAT_ENTRIES && nat_table[i].icmp_id != id) i++;
	if(i == MAX_NAT_ENTRIES) return NULL; // No NAT hit
	char *result = malloc(sizeof(char)*40);
	IP2Dot(result, nat_table[i].ip_src);
	return result;
}

void printNAT(void){
	int i;
	char tmp[40];
	printf("\n NAT TABLE \n");
	for(i = 0; i < MAX_NAT_ENTRIES; i++){
		IP2Dot(tmp, nat_table[i].ip_src);
		printf("ICMP ID: %d, SRC IP: %s\n", nat_table[i].icmp_id, tmp);
	}
}







