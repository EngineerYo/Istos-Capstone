from socket import socket, getfqdn, AF_INET, SOCK_STREAM, htons, INADDR_ANY, gethostbyname, gethostname
import time
import datetime

import hashlib
import sys
import uuid

import numpy as np
import matplotlib

from matplotlib import pyplot as plt
from matplotlib import animation as animation


ts = socket(AF_INET, SOCK_STREAM)
ts.bind(('0.0.0.0', 0))

serverAddress = 'team-istos.com'
macAddress = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0, 8*6, 8)][::-1])

IP = gethostbyname(gethostname())
ID = 'Istos Client'
PSPH = 'mitchIsDaddy'
server = (serverAddress, 8900)

def ackProcess(message, sha):
    args = message.split('\t')
    if args[0] == 'QUERY':
        return False
    if args[-1].endswith('\0'):
        args[-1] = args[-1][:-1]
    if len(args) < 5:
        print('Too few arguments')
        return False
    if args[4] != sha:
        print(args[4] + ' != ' + sha)
    return args[1]

def dataProcess(message):
    args = message.split('\t')
    if args[-1].endswith('\0'):
        args[-1] = args[-1][:-1]
    if len(args) < 6:
        return False
    return (args[1], args[5])

try:
    ts.connect(server)
except:
    print('Failed to connect\nExiting program')
    sys.exit(1)

regMessage = 'REGISTER\t' + ID + '\t' + PSPH + '\t' + macAddress + '\0'
sendMessage = regMessage.encode('ascii')

ts.send(sendMessage)
sha = hashlib.sha256(sendMessage).hexdigest()

for x in range(3):
    try:
        data = ts.recv(1024)
        rcv = data.decode('ascii')
        print('\tREGISTER')
        break
    except:
        if x == 2:
            print('Failed to receive message. Logging')
            now = datetime.datetime.now()
            msg = '{0:%Y-%m-%d %H:%M:%S}'.format(now) + ' >> Failed to register\n'
            sys.exit(1)
        else:
            print('Failed to receive message count: %d' % x)
            sys.exit(1)

loginMessage = 'LOGIN\t' + ID + '\t' + PSPH + '\t' + IP + '\t' + '%d' % 0
sendMessage = loginMessage.encode('ascii')

ts.send(sendMessage)
sha = hashlib.sha256(sendMessage).hexdigest()

data = ts.recv(1024)
rcv = data.decode('ascii')

result = ackProcess(rcv, sha)
if result == '70':
    print('\tLOGIN')
else:
    print('\tFAILURE TO LOGIN')
    sys.exit(1)

toDisplay = []

val0 = []
val1 = []
val2 = []

index = []
count = 0
maxIndex = 501

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

while True:
    queryMessage = 'QUERY\t03\t' + ID + '\t' + '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + '\t0'
    time.sleep(0.5)
    ts.send(queryMessage.encode('ascii'))
    data = ts.recv(1024)
    outData = dataProcess(data.decode('ascii'))

    if outData[1] == 'msg':
        continue

    if len(outData) < 2:
        continue

    if len(outData[1].split('\n')) < 3:
        continue
    
    interVal = outData[1].split('\n')[2]
    if len(interVal) < 2:
        print('interVal invalid')
        continue

    outVal = interVal.split(' ')
    outVal[0] = float(outVal[0])
    outVal[1] = float(outVal[1])
    outVal[2] = float(outVal[2])

    if len(toDisplay) >= maxIndex:
        toDisplay.pop(0)
        val0.pop(0)
        val1.pop(0)
        val2.pop(0)
        
    if len(toDisplay) == 0:
        toDisplay.insert(0, outVal[0])
        val0.append(outVal[0])
        val1.append(outVal[1])
        val2.append(outVal[2])

        
        if len(index) < maxIndex:
            index.append(len(index))
        
        ax.clear()
        ax.plot(index, val0, linestyle='-')
        ax.plot(index, val1, linestyle='-')
        ax.plot(index, val2, linestyle='-')

        plt.xlim(0, maxIndex)
        plt.draw()
        plt.pause(0.5)
        print(outVal)

    elif not (outVal[0] == val0[-1] or outVal[1] == val1[-1] or outVal[2] == val2[-1]):
        print('%f' % outVal[0] + '\t' + '%f' % val0[-1])
        print('%f' % outVal[1] + '\t' + '%f' % val1[-1])
        print('%f' % outVal[2] + '\t' + '%f' % val2[-1])
        toDisplay.append(outVal[0])
        val0.append(outVal[0])
        val1.append(outVal[1])
        val2.append(outVal[2])
        
        if len(index) < maxIndex:
            index.append(len(index))
        
        ax.clear()
        ax.plot(index, val0, linestyle='-')
        ax.plot(index, val1, linestyle='-')
        ax.plot(index, val2, linestyle='-')

        plt.xlim(0, maxIndex)
        plt.draw()  
        plt.pause(0.5)
        print(outVal)
