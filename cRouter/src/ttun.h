/*
 * This is the low level driver for the tun interface. 
 * It hooks up a UDP socket to the mesh interface.
 * 
 * Copyright (C) 2015 Ahmed Youssef (ahmed.youssef@mail.mcgill.ca)
 * Licensed under the GPL.
 */

#ifndef TTUN_H
#define	TTUN_H

#include "vpl.h"
#include "grouter.h"

void *toTtunDev(void *arg);
void* fromTtunDev(void *arg);
vpl_data_t *ttun_connect(short int src_port, uchar* src_IP,
                        short int dst_port, uchar* dst_IP, short int is_server);


#endif	/* TUN_H */