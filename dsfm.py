import threading
import sys
from netmiko import ConnectHandler
import netmiko
import getpass
import argparse
import os

uname = pwd = cmd = oFile = delayFactor = None

maxConnections = 5
semaphore = None
muxwrite = threading.BoundedSemaphore()


def getCredentials():
	global uname, pwd
	uname = input('login: ').rstrip()
	pwd = getpass.getpass('pass: ')

def getParam(): 
	global maxConnections, cmd, delayFactor
	try:
		maxConnections = int(input('max connect[default 5]: '))
	except ValueError:
		maxConnections = 5	
	try:
		delayFactor = float(input('delay factor[default 0.4]: '))	
	except:
		delayFactor = 0.4
	cmd = input('command: ')

def getHostList():
	hostList = []
	print('Input host List ending blank line')
	for line in sys.stdin:
		if(line == '\n'):
			return hostList
		hostList.append(line.rstrip('\n'))

def sshExchange(host):
	global uname, pwd, cmd, semaphore, oFile, muxwrite, delayFactor
	try:
		net_connect = ConnectHandler(device_type='cisco_ios', ip=host, username=uname, password=pwd)
		prompt = net_connect.find_prompt().rstrip('#\n')
		output = net_connect.send_command(cmd, delay_factor=delayFactor)
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

	poutput = '%s(%s):\n%s\n----------------------------------------\n' % (prompt, host, output)

	if(oFile != None):
		muxwrite.acquire()
		with open(oFile, 'a') as f:
			f.write(poutput)
		muxwrite.release()

	print(poutput)

def main():
	global maxConnections, semaphore, oFile
	parser = argparse.ArgumentParser()
	parser.add_argument("--out", dest='outFile', help="Output File")
	args = parser.parse_args()

	oFile = args.outFile

	getCredentials()
	getParam()
	hostList = getHostList()
	semaphore = threading.BoundedSemaphore(value=maxConnections)


	print('In progress...')
	for host in hostList:
		semaphore.acquire()
		t = threading.Thread(target=sshExchange, args=(host,))
		t.start()

if(__name__ == '__main__'):
	main()