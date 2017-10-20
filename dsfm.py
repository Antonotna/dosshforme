import threading
import sys
from netmiko import ConnectHandler
import netmiko
import getpass

uname = pwd = cmd = None

maxConnections = 5
semaphore = None
muxwrite = threading.BoundedSemaphore()


def getCredentials():
	global uname, pwd
	uname = input('login: ').rstrip()
	pwd = getpass.getpass('pass: ')

def getParam(): 
	global maxConnections, cmd
	maxConnections = int(input('max connect: '))
	cmd = input('command: ')

def getHostList():
	hostList = []
	print('Input host List ending blank line')
	for line in sys.stdin:
		if(line == '\n'):
			return hostList
		hostList.append(line.rstrip('\n'))

def sshExchange(host):
	global uname, pwd, cmd, semaphore
	try:
		net_connect = ConnectHandler(device_type='cisco_ios', ip=host, username=uname, password=pwd)
		prompt = net_connect.find_prompt().rstrip('#\n')
		output = net_connect.send_command(cmd, delay_factor=0.4)
		net_connect.disconnect()
	except netmiko.ssh_exception.NetMikoTimeoutException:
		print('%s Timeout' % host)
		semaphore.release()
		return
	except netmiko.ssh_exception.NetMikoAuthenticationException:
		print('%s Auth Fail' % host)
		semaphore.release()
		return
	except:
		print('%s Unknown' % host)
		semaphore.release()
		return

	semaphore.release()

	print('%s:\n%s\n----------------------------------------' % (prompt, output))

def main():
	global maxConnections, semaphore
	getCredentials()
	getParam()
	hostList = getHostList()
	semaphore = threading.BoundedSemaphore(maxConnections)

	print('In progress...')
	for host in hostList:
		semaphore.acquire()
		t = threading.Thread(target=sshExchange, args=(host,))
		t.start()

if(__name__ == '__main__'):
	main()