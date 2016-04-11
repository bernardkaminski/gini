from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from urllib2 import urlopen
import os
import shutil
import boto3
import time
import sys
import multiprocessing
# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
	rpc_paths=('/RPC2',)

# Create server
server = SimpleXMLRPCServer(("localhost", 8000),requestHandler=RequestHandler, allow_none=True)
server.register_introspection_functions()

#Server dependencies awscli, boto3, python3
class AmazonCloudFunctions:
	
	def __init__(self):
		self.key_pair = None
		self.key_name = "GINI"
		self.ec2 = None
		self.new_instance_ip = None # just for debugging
		self.new_instance_private_ip = None
	def print_routes(self):
		string = os.popen('ssh -i GINI.pem ubuntu@'+self.new_instance_ip+" 'arp -a'").read()
		print string
	def configure_aws(self,key,secret_key):
		#Create the .aws directory with the users keys (same functionality as aws configure)
		path=os.path.join(os.environ['HOME'],".aws")
		if os.path.exists(path):
			print("Directory exists, removing")
			shutil.rmtree(path)
		os.makedirs(path)
		creds=open(os.path.join(path,"credentials"),'w')
		config=open(os.path.join(path,"config"),'w')
		config.write('[default]\nregion = us-west-2\n'); # default region
		creds.write('[default]\naws_access_key_id = '+key+'\naws_secret_access_key = '+secret_key+'\n');
		creds.close()
		config.close()
		self.ec2=boto3.resource('ec2') # ec2 now available for the other methods
		if self.ec2.instances == None:
			print "Unable to authenticate"
			sys.exit(1)
	def get_ip(self):
		return self.new_instance_ip
	def get_private_ip(self):
		return self.new_instance_private_ip
	def list_instances(self):
		for inst in self.ec2.instances.all():
			if inst.public_ip_address != None:
				print("ID: "+inst.id+" TYPE: "+inst.instance_type+" STATE: "+inst.state['Name']+" Public DNS: "+inst.public_dns_name+" Public IP "+inst.public_ip_address)
	def create_instance(self):
		# If the GINI key does not exist, create it
		found_key = 0
		for key_info in self.ec2.key_pairs.all():
			if key_info.key_name == self.key_name:
				found_key = 1
				break
		if not found_key:
			self.key_gen()
		# This image ID is a special image that has the yRouter installed on it
		new_instance = self.ec2.create_instances(ImageId="ami-4021c620", MinCount=1, MaxCount=1, InstanceType='t2.micro', KeyName = self.key_name, SecurityGroups = ['GINI',])	
		# Chill for that instance to be crafted
		while(new_instance[0].public_ip_address == None):
			new_instance[0].load()  # Get current status
			print("ID: "+new_instance[0].id+" State: "+new_instance[0].state['Name']+" No IP Address")
			time.sleep(5)
		# Need this newly created instances public IP address to set up the tunnel
		self.new_instance_ip = new_instance[0].public_ip_address 
		self.new_instance_private_ip = new_instance[0].private_ip_address
	def stop_all_instances(self):
		for inst in self.ec2.instances.all():
			inst.stop()
	def terminate_all_instances(self):
		for inst in self.ec2.instances.all():
			inst.terminate()
	def terminate_instance(self, ip):
		for inst in self.ec2.instances.all():
			if inst.public_ip_address == ip:
				inst.terminate()
	def get_running_instance(self):
		for inst in self.ec2.instances.all():
			if (inst.public_ip_address != None) and (inst.private_ip_address != None):
				self.new_instance_ip = inst.public_ip_address
				self.new_instance_private_ip = inst.private_ip_address
				break;
	def key_gen(self):
		# False means make the key for real
		self.key_pair = self.ec2.create_key_pair(DryRun = False, KeyName = self.key_name)
		if os.path.exists(slf.key_name+".pem"):
			os.chmod(self.key_name+".pem",0777)
		f = open(self.key_name+".pem",'w')
		f.write(self.key_pair.key_material)
		f.close()
		os.chmod(f.name,0400)
	def get_port_number(self, interface_id, router_number):
		return 60000+interface_id+router_number*100
	def cloud_shell(self):
			#login as root in order to create the raw socket
			os.system("xterm -e ssh -i GINI.pem -o StrictHostKeyChecking=no -t ubuntu@"+self.new_instance_ip+" 'export GINI_HOME=/home/ubuntu; sudo -E /home/ubuntu/yRouter/src/yrouter --interactive=1 --confpath=/home/ubuntu --config=cloud_tunnel Router_2;exec bash'")
	def local_shell(self):
			os.system("xterm -e cRouter/src/yrouter --interactive=1 --verbose=2 --confpath="+os.getcwd()+" --config=local_tunnel Router_1")
	def create_tunnel(self):
		# need to copy the yRouter to the cloud
		print("Creating tunnel")
		# copy the cloud configuration file to the instance
		os.system("scp -i "+self.key_name+".pem -o StrictHostKeyChecking=no cloud_tunnel ubuntu@"+self.new_instance_ip+":/home/ubuntu")
		#start the cloud router
		# Note you have to delete the files it creates on the cloud after if you want to run it again
		print("attempting "+ "xterm -e ssh -R "+str(self.get_port_number(0, 1))+":localhost:"+str(self.get_port_number(0,1))+" -i GINI.pem -o StrictHostKeyChecking=no ubuntu@"+self.new_instance_ip+" 'source ~/.profile; sudo -E yRouter/src/yrouter --interactive=1 --verbose=2 --confpath=/home/ubuntu --config=cloud_tunnel Router_1;exec bash'")
		#os.system("xterm -e ssh -R "+str(self.get_port_number(0, 1))+":localhost:"+str(self.get_port_number(0,1))+"-i GINI.pem -o StrictHostKeyChecking=no ubuntu@"+self.new_instance_ip+" 'source ~/.profile; sudo -E yRouter/src/yrouter --interactive=1 --verbose=2 --confpath=/home/ubuntu --config=cloud_tunnel Router_1;exec bash'")
		p1 = multiprocessing.Process(target=self.cloud_shell)
		p1.start()
		p2 = multiprocessing.Process(target=self.local_shell)
		print("opening local router")
		p2.start()
		
		#Note if you get "unable to connect to tun0" try a different Router number i.e. Router_2 instead
		#60000+interface_id+router_number*100 
		# dstport should be the same as the interface id
		#Name of router is Router_1 where in this case 1 is the router number
		#start the local router ...
	def create_tunnel_cloud_config_file(self):
		f = open("cloud_tunnel","w")
		print("Trying to get public ip")
		local_ip = urlopen('http://ip.42.pl/raw').read() # Get local public IP
		print("Got public ip")
		ifconfig = "ifconfig add tun0 -dstip "+local_ip+" -dstport 0 -addr 10.10.10.10 -hwaddr a0:a0:a0:a0:a0\n"
		f.write(ifconfig)
		route = "route add -dev tun0 -net 20.20.20.20 -netmask 255.255.255.255\n"
		f.write(route)
		#raw socket commands for injecting packets into the kernel
		ifconfig_raw = "ifconfig add raw1 -addr "+self.new_instance_private_ip+"\n"
		f.write(ifconfig_raw)
		#for some reason unable to get the default gateway ip address from boto3
		#have to do it this way
		cloud_arp_table = os.popen('ssh -i GINI.pem ubuntu@'+self.new_instance_ip+" 'arp -a'").read()
		default_gateway = cloud_arp_table[cloud_arp_table.find("(")+1:cloud_arp_table.find(")")]
		route_raw = "route add -dev raw1 -net 172.0.0.0 -netmask 255.0.0.0 -gw "+default_gateway+"\n"
		f.write(route_raw)
		f.close()

	def create_tunnel_local_config_file(self):
		if self.new_instance_ip == None:
			print("Create an instance first!")
			return
		f = open("local_tunnel","w")
		ifconfig = "ifconfig add tun0 -dstip "+self.new_instance_ip+" -dstport 0 -addr 20.20.20.20 -hwaddr a1:a1:a1:a1:a1\n"
		f.write(ifconfig)
		route = "route add -dev tun0 -net 10.10.10.10 -netmask 255.255.255.255\n"
		f.write(route)
		f.close()
	def add_udp_rules(self):

		security_group = self.ec2.create_security_group(
			DryRun=False,
			GroupName='test',
			Description='this is a test'
		)

		response = security_group.authorize_ingress(
			DryRun=False,
			GroupName='test',
			IpProtocol='udp',
			FromPort=0,
			ToPort=65000,
			CidrIp='0.0.0.0/0'
		)

server.register_instance(AmazonCloudFunctions())

print("Serving on 8000")
# Run the server's main loop
server.serve_forever()



