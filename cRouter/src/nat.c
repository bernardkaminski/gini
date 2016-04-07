/* nat.c (source file for the NAT module)
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

// Includes for obtaining the source ip address for the SNAT operation
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netdb.h>
#include <ifaddrs.h>
#include <unistd.h>

#define MAX_NAT_ENTRIES 20 // Only the most recent 20 NAT calls will be stored (circular buffer)

typedef struct{
	int icmp_id;
	unsigned char ip_src[4];
} nat_entry;

int nat_table_index = 0;
nat_entry nat_table[MAX_NAT_ENTRIES] = {0};

/*
	Returns the IP address of eth0. Only works on ubuntu machine. Used to determine what the source
	ip address should be used for SNAT operation.
*/
char* getIp(void){
    struct ifaddrs *ifaddr, *ifa;
    int family, s;
    char *host  = malloc(NI_MAXHOST);
   
    if (getifaddrs(&ifaddr) == -1){
    	return NULL;
    }

    for (ifa = ifaddr; ifa != NULL; ifa = ifa->ifa_next){
        if (ifa->ifa_addr == NULL)
            continue;  

        s=getnameinfo(ifa->ifa_addr,sizeof(struct sockaddr_in),host, NI_MAXHOST, NULL, 0, NI_NUMERICHOST);

        if((strcmp(ifa->ifa_name,"eth0")==0)&&(ifa->ifa_addr->sa_family==AF_INET)){
            if (s != 0){
		return NULL;
            }
	    return host;
        }
    }

    freeifaddrs(ifaddr);
    return NULL;
}

/*
	Takes in 172.31.44.65 --> 65.44.31.172
*/
void toNetworkByteOrder(char *ip, char *result){
	int len = strlen(ip);
	int ip_index = len - 1;
	int result_index = 0;
	while(ip_index > 0){
		int index_dot = ip_index;
		// Find index of dot
		while(ip[index_dot] != '.' && index_dot >= 0) index_dot--;  
		// Copy each character before the dot to the result
		int k;
		for(k = 0; k < (ip_index - index_dot); k++){
			printf("%c", ip[index_dot + k + 1]);
			result[result_index++] = ip[index_dot + k + 1];
		}
		if(result_index < len)
			result[result_index++] =  '.';
		ip_index = index_dot - 1;
	}
}

void applySNAT(char *new_src, ip_packet_t *raw_ip, int id){
	
	char buf[40];

	if(getSrcFromNAT(id) == NULL){
		// Save the NAT entry if the ping id is not already saved
		addToNAT(id, raw_ip->ip_src);
	}
	// Apply the new source
	Dot2IP(new_src, raw_ip->ip_src);
	
	// Recompute the checksum
	raw_ip->ip_cksum = 0;
	raw_ip->ip_cksum = htons(checksum((unsigned char *) raw_ip, raw_ip->ip_hdr_len *2));
}

int applyDNAT(ip_packet_t *raw_ip, int id){

	char *src = getSrcFromNAT(id);
	if(src == NULL) return -1; // No dnat to be applied, wasn't snatted in the first place
	char buf[40];

	// Apply new destination 
	Dot2IP(src, raw_ip->ip_dst);

	// Recompute the checksum
	raw_ip->ip_cksum = 0;
	raw_ip->ip_cksum = htons(checksum((unsigned char *) raw_ip, raw_ip->ip_hdr_len *2));
	return 0;
}

void addToNAT(int id, unsigned char *src){
	nat_table[nat_table_index].icmp_id = id;
	nat_table[nat_table_index].ip_src[0] = src[0];
	nat_table[nat_table_index].ip_src[1] = src[1];
	nat_table[nat_table_index].ip_src[2] = src[2];
	nat_table[nat_table_index].ip_src[3] = src[3];		
	nat_table_index = (nat_table_index + 1) % MAX_NAT_ENTRIES; // Circular buffer
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
	char tmp[40], tmp2[40];
	printf("\n\n NAT TABLE: \n\n");
	for(i = 0; i < MAX_NAT_ENTRIES; i++){
		IP2Dot(tmp, nat_table[i].ip_src);
//		toNetworkByteOrder(tmp, tmp2);
		printf("ICMP ID: %d IP: %s\n", nat_table[i].icmp_id, tmp);
		memset(tmp, 0, sizeof(tmp));
		memset(tmp2, 0, sizeof(tmp2));
	}
}


