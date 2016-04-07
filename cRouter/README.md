## cRouter

Modified version of the [gRouter](https://github.com/anrl/gini/tree/master/backend/src/grouter) which is used on either end point of a TCP tunnel between a local gini network and a AWS cloud instance. The use of the TCP tunnel allows the traversal of a NAT (allowing 2 way communication with a public ip address and a private ip address behind a NAT). The cRouter also contains a NAT used to SNAT and DNAT ICMP packets that leave the local gini network and reach the amazon cloud network. For example with cRouter's running both locally and on an instance, a ttun0 device can be used to set up the TCP tunnel between the two, and then the user is able to ping other amazon instances and the amazon cloud router from the local cRouter.

## Installation

For example:

cd cRouter/src
make clean && make
./crouter --interactive=1 Cloud

## Usage

Usage is the same as the [gRouter](https://github.com/anrl/gini/tree/master/backend/src/grouter) except for the new CLI commands, namely the creation of a TCP tunnel. For example:

Cloud Endpoint (after running "./crouter --interactive=1 Cloud" on the AWS instance)
	GINI-Cloud $ ifconfig add ttun0 -dstip <Tunnel machines public IP> -dstport < Some port >50000 && <65000 > -addr <A made up private IP address for the interface> -hwaddr < A made up private MAC address > -s 1

Local Endpoint (after running "./crouter --interactive=1 Tunnel" on the local machine)
	GINI-Tunnel $ ifconfig add ttun0 -dstip <Amazons public IP> -dstport < port matching above> -addr <A made up private IP address for the interface> -hwaddr < A made up private MAC address -s 0 

- Replace the parameters <\> with approriate values
- Now you should be able to ping running Amazon instance address's (172.0.0.0/24)

Note the "crouter" is an executable file and if you pass it --interactive=1 you will enter the command line mode. "Tunnel' and "Cloud" are aribtrary names for the routers and used to name the metadata files that are created while the process is running. 
