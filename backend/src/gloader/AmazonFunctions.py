from urllib2 import urlopen
import os
import shutil
import boto3
import time
import sys
import subprocess

# Server dependencies awscli, boto3, python3
class AmazonCloudFunctions:

    def __init__(self):
        self.key_pair = None
        self.key_name = "GINI"
        self.key_path = os.environ["GINI_ROOT"]+"/"+self.key_name+".pem"
        self.ec2 = None
        self.new_instance_ip = None  # just for debugging
        self.new_instance_private_ip = None

    def print_routes(self):
        string = os.popen('ssh -i '+self.key_path+' ubuntu@' + self.new_instance_ip + " 'arp -a'").read()
        print string

    def configure_aws(self, key, secret_key):
        # Create the .aws directory with the users keys (same functionality as aws configure)
        path = os.path.join(os.environ['HOME'], ".aws")
        if os.path.exists(path):
            print("Directory exists, removing")
            shutil.rmtree(path)
        os.makedirs(path)
        creds = open(os.path.join(path, "credentials"), 'w')
        config = open(os.path.join(path, "config"), 'w')
        config.write('[default]\nregion = us-west-2\n');  # default region
        creds.write('[default]\naws_access_key_id = ' + key + '\naws_secret_access_key = ' + secret_key + '\n');
        creds.close()
        config.close()
        self.ec2 = boto3.resource('ec2')  # ec2 now available for the other methods
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
                print("ID: " + inst.id + " TYPE: " + inst.instance_type + " STATE: " + inst.state[
                    'Name'] + " Public DNS: " + inst.public_dns_name + " Public IP " + inst.public_ip_address)

    def create_instance(self):
        # If the GINI key does not exist, create it
        found_key = 0
        for key_info in self.ec2.key_pairs.all():
            if key_info.key_name == self.key_name and os.path.exists(self.key_path):
                found_key = 1
                print("Key already exists")
                os.chmod(self.key_path, 0400)
                break
        if not found_key:
            self.key_gen()
        # This image ID is a special image that has the yRouter installed on it
        new_instance = self.ec2.create_instances(ImageId="ami-7e84701e", MinCount=1, MaxCount=1,
                                                 InstanceType='t2.micro', KeyName=self.key_name,
                                                 SecurityGroups=['GINI', ])
        # Chill for that instance to be crafted
        while (new_instance[0].public_ip_address == None):
            new_instance[0].load()  # Get current status
            print("ID: " + new_instance[0].id + " State: " + new_instance[0].state['Name'] + " No IP Address")
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

    def get_running_instance(self, ip ):
        for inst in self.ec2.instances.all():
            if (inst.private_ip_address == ip):
                self.new_instance_ip = inst.public_ip_address
                self.new_instance_private_ip = inst.private_ip_address
                break

    def key_gen(self):
        if os.path.exists(self.key_path):
            os.remove(self.key_path)
        print("Creating a new key")
        self.key_pair = self.ec2.create_key_pair(DryRun=False, KeyName=self.key_name)
        f = open(self.key_path, 'w')
        f.write(self.key_pair.key_material)
        f.close()
        os.chmod(self.key_path, 0400)
        

    def create_tunnel(self,cloud_config_file,tunnel_config_file,cloud_name,tunnel_name):
       # need to copy the yRouter to the cloud
        print("Creating tunnel")
        # Copy the cloud configuration file to the instance
        os.system(
            "scp -i " + self.key_path + " -o StrictHostKeyChecking=no "
            +cloud_config_file+" ubuntu@" + self.new_instance_ip + ":/home/ubuntu")
        
        # Create cloud router (server for tcp)
        p2 = subprocess.Popen("export DISPLAY=:0; xterm -e ssh -X -i "+self.key_path
            +" -o StrictHostKeyChecking=no -t ubuntu@" + self.new_instance_ip 
            +" 'export GINI_HOME=/home/ubuntu; sudo -E /home/ubuntu/cRouter/src/crouter --interactive=1 --confpath=/home/ubuntu --config=grouter.conf "
            +cloud_name+";exec bash'", shell=True)
        print("Started cloud router on instance")
        time.sleep(5) # Give the local router time to setup the tcp tunnel before the cloud tries to connect 

        # Create local router (client for tcp)
        conf_path = tunnel_config_file.strip("/grouter.conf")

        oldDir = os.getcwd()
        os.chdir("/"+conf_path+"/")
        #print command
        command = "screen -d -m -L -S %s " % (tunnel_name)
        startOut = open("startit.sh", "w")
        startOut.write(command+os.environ["GINI_ROOT"]+"/cRouter/src/crouter --interactive=1 --verbose=2 --confpath=/" + conf_path + " --config=grouter.conf "+tunnel_name)
        startOut.close()
        os.chmod("startit.sh",0755)
        os.system("./startit.sh")
        print "[OK]"
        os.chdir(oldDir)
        # Wait after starting router so they have time to create sockets
        time.sleep(2)

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
