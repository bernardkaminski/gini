import xmlrpclib
import boto3
import time
import sys
import keys

s = xmlrpclib.ServerProxy('http://localhost:8000')

# could use sys.argv to get the keys from the command line
#note add your keys before running the test client
s.configure_aws(AWS_KEY,AWS_SECRET)

# Print list of available methods
print(s.system.listMethods())

while True:
	key = raw_input(">>> ")
	if key == 'create':
		s.create_instance()
	if key == 'list':
		s.list_instances()
	if key == 'ip':
		print(s.get_ip())
	if key == 'private_ip':
		print(s.get_private_ip())
	if key == 'route':
		s.print_routes()
	if key == 'create_cloud_config':
		s.create_tunnel_cloud_config_file()
	if key == 'create_local_config':
		s.create_tunnel_local_config_file()
	if key == 'create_tunnel':
		s.create_tunnel()
	if key == 'terminate':
		ip = raw_input(">>> ip address? ")
		s.terminate_instance(ip)
	if key == 'killall':
		s.terminate_all_instances()
	if key == 'get_running':
		s.get_running_instance()
	if key == 'exit':
		sys.exit(0)
