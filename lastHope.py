from socket import socket, getfqdn, AF_INET, SOCK_STREAM, htons, INADDR_ANY, gethostbyname, gethostname
import time
import datetime

import hashlib
import sys
import uuid

ts = socket(AF_INET, SOCK_STREAM)
ts.bind(('0.0.0.0', 0))

serverAddress = '192.168.1.27'
macAddress = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0, 8*6, 8)][::-1])

IP = gethostbyname(gethostname())
ID = 'Istos Client'
PSPH = 'mitchIsDaddy'
server = (serverAddress, htons(8900))

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
maxIndex = 49

while True:
    queryMessage = 'QUERY\t03\t' + ID + '\t' + '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + '\t0'
    time.sleep(3.5)
    ts.send(queryMessage)
    data = ts.recv(1024)
    outData = dataProcess(data)

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
    if len(toDisplay) != 0 and (outVal[0] == toDisplay[0][0] or outVal[1] == toDisplay[0][1] or outVal[2] == toDisplay[0][2]):
        continue
    
    if len(toDisplay) >= maxIndex:
        toDisplay.pop()
    
    toDisplay.insert(0, outVal)
    print(outVal)
