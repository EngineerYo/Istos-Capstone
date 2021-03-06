import blynklib
import random
from socket import socket, getfqdn, AF_INET, SOCK_STREAM, htons, INADDR_ANY, gethostbyname, gethostname
import time
import datetime

import adafruit_ads1x15
from  adafruit_ads1x15.analog_in import AnalogIn
from  adafruit_ads1x15 import ads1115
import board
import busio

import uuid
import hashlib
import sys
    
# Blynk
BLYNK_AUTH = '0f9ee012060d4790adf6ccae57a73494'
#BLYNK_AUTH = '6c94ec9d2385423b924e410be8e83faf'
blynk = blynklib.Blynk(BLYNK_AUTH)

ts = socket(AF_INET, SOCK_STREAM)
ts.bind(('0.0.0.0', 0))
# timeout?

serverAddress = 'team-istos.com' #change later
macAddress = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0,8*6,8)][::-1])

print('Powered by J. Siao')


READ_PRINT_MSG = "[READ_VIRTUAL_PIN_EVENT] Pin: V{}"

# register handler for virtual pin V12 reading
@blynk.handle_event('read V12')
def read_virtual_pin_handler(pin):
    print(READ_PRINT_MSG.format(pin))
    blynk.virtual_write(pin, 'Connected')
    blynk.virtual_write(0, power0)
    blynk.virtual_write(1, power1)
    blynk.virtual_write(2, power2)
    

def ack_process(message, sha):
    args = message.split('\t')
    if args[0] == "QUERY":
        return False
    if args[-1].endswith("\0"):
        args[-1] = args[-1][:-1]
    if len(args) < 5:
        print("Too few arguments")
        return False
    if args[4] != sha:
        print(args[4] + " != " + sha)
        return False
    return args[1]


IP = gethostbyname(gethostname())
ID = 'Istos PI'
PSPH = 'mitchIsDaddy'
server = (serverAddress, 8900)

try:
    ts.connect(server)
    
except:
    print('Failed to connect\nExiting program')
    sys.exit(1)

def ack_process(message, sha):
    args = message.split('\t')
    if args[0] == "QUERY":
        return False
    if args[-1].endswith("\0"):
        args[-1] = args[-1][:-1]
    if len(args) < 5:
        #print("Too few arguments")
        return False
    if args[4] != sha:
        #print(args[4] + " != " + sha)
        return False
    return args[1]

def data_process(message):
    args = message.split('\t')
    if args[-1].endswith("\0"):
        args[-1] = args[-1][:-1]
    if len(args) < 6:
        return False
    return (args[1], args[5])

#    #    #    #

regMessage = "REGISTER\t" + ID + "\t" + PSPH + "\t" + macAddress + "\0"
sendMessage = regMessage.encode('ascii')

ts.send(sendMessage)
sha = hashlib.sha256(sendMessage).hexdigest()

for x in range(3):
    try:
        data = ts.recv(1024)
        rcv = data.decode('ascii')
        print("ACK recv")
        break
    except:
        if x == 2:
            print("Failed to recv message. Logging")
            now = datetime.datetime.now()
            msg = '{0:%Y-%m-%d %H:%M:%S}'.format(now) + " >> failed to register\n"
            sys.exit(1)
        else:
            print("Failed to recv message count: %d" % x)
            sys.exit(1)

loginMessage = "LOGIN\t" + ID + "\t" + PSPH + "\t" + IP + "\t" + "%d" % 0
send_msg = loginMessage.encode('ascii')

ts.send(send_msg)
sha = hashlib.sha256(send_msg).hexdigest()
data = ts.recv(1024)
rcv = data.decode('ascii')

result = ack_process(rcv, sha)

if result == "70":
    print("Successfully logged on")
else:
    print("Login failed")
    sys.exit(1)

#import antigravity
i2c = busio.I2C(board.SCL, board.SDA)

# Create an ADS1115 ADC (16-bit) instance.
ads = ads1115.ADS1115(i2c)

VOLTAGE = 120
GAIN = 2
startTime = datetime.datetime.now()

file = open("./Data/{0:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now()),"w")
print('Reading ADS1x15 values, press Ctrl-C to quit...')
# Print nice channel column headers.
header='dt [s]\tP0 [W]\tP1 [W]\tP2 [W]'
header2='_' * 35
print(header)
print(header2)
file.write(header + "\n")
file.write(header2 + "\n")

sen0 = AnalogIn(ads, ads1115.P0)
sen1 = AnalogIn(ads, ads1115.P1)
sen2 = AnalogIn(ads, ads1115.P2)

curr0 = False
curr1 = False
curr2 = False

datapoint = 0

try:
	while True:
		
		datapoint = datapoint + 1
		n = 80
		
		val0 = [0]*n
		val1 = [0]*n
		val2 = [0]*n
		
		sq0 = [0]*n
		sq1 = [0]*n
		sq2 = [0]*n
		
		for i in range(n):
			
			val0[i] = sen0.voltage
			val1[i] = sen1.voltage
			val2[i] = sen2.voltage
			
			sq0[i] = val0[i]**2
			sq1[i] = val1[i]**2
			sq2[i] = val2[i]**2
				
		curr0 = ((sum(sq0)/n)**0.5)/6.0*1000.0/1.087
		curr1 = ((sum(sq1)/n)**0.5)/6.0*1000.0/1.087
		curr2 = ((sum(sq2)/n)**0.5)/6.0*1000.0/1.087
		
		power0 = curr0*120
		power1 = curr1*120
		power2 = curr2*120
		
		newTime = datetime.datetime.now()
		dt = (newTime - startTime)
		dt = dt.seconds + dt.microseconds/1000000.0
		startTime = newTime 
		
		message = '%0.2f\t%0.2f\t%0.2f\t%0.2f' % (dt, power0, power1, power2)
		
		blynk.run()

		if datapoint == 10:
			
			print(header)
			print(header2)
			datapoint = 0
			
		print(message)
		file.write(message + "\n")
		
		# outStr = '%f %f %f %f %f' % (dt, 1000.0*current, power, 1000.0*newCurrent, newPower)
		outStr = '%f %f %f' % (power0, power1, power2)
		
		sendMsg = "DATA\t00\t" + ID + "\t" + '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + "\t" + '%d' % len(outStr) + "\t" + outStr + "\0"
		sendMsgEncode = sendMsg.encode('ascii')
		ts.send(sendMsgEncode)
		sha = hashlib.sha256(sendMsgEncode).hexdigest()
		
		recvMsg = ts.recv(1024)
		recv = recvMsg.decode('ascii')
		result = ack_process(recv, sha)
		   

		if result == '50':
			pass
		
		else:
			pass
			# cry
				
except:
	print("Current broken")
    
    

logoffMessage = "LOGOFF\t" + ID
send_msg = logoffMessage.encode('ascii')
ts.send(send_msg)
sha = hashlib.sha256(send_msg).hexdigest()
data = ts.recv(1024)
rcv = data.decode('ascii')
result = ack_process(rcv, sha)
if result == "80":
    print("Successfully logged on")
    
else:
    print("Login failed")
