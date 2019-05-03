from google.cloud import storage
import sys

from socket import socket, getfqdn, AF_INET, SOCK_DGRAM, SOCK_STREAM, INADDR_ANY
from threading import Thread, Lock
from _thread import *
import datetime
import hashlib

if len(sys.argv) < 2:
    print("error: give the key file")
    sys.exit(0)

clients = 0
client_lock = Lock()

registry = []          #stores tuples of (ID, MAC, IP, PSPH, PORT)
registry_lock = Lock()

data_msg = ""
data_msg_lock = Lock()

j = open(sys.argv[1], "r")
if not j:
     print("Error, invalid JSON file")
     sys.exit(0)
j_str = j.read()


f = open("Activity.log", "a")

def register_device(args, addr): #args = (REGISTER, ID, PSPH, MAC)
    if args[3].endswith("\0"):
        args[3] = args[3][:-1]
    registry_lock.acquire()
    for x in range(len(registry)):
        if registry[x][0] == args[1]:  #match ID
            if registry[x][2] == addr[0]:  #and matches IP
                registry_lock.release()
                return "12"      #ACK of 12: IP reused
            elif registry[x][1] == args[3]: #matches MAC, updates IP
                registry[x] = (registry[x][0], registry[x][1], addr[0], registry[x][3], registry[x][4])
                registry_lock.release()
                return "02"
            else:
                registry_lock.release()
                return "01"                 #ID already exists
        elif registry[x][1] == args[3]:  #Match MAC but different ID
            registry_lock.release()
            return "13"
    registry.append((args[1], args[3], addr[0], args[2], "-65535"))
    print(registry)
    registry_lock.release()
    return "00"

def deregister(args, addr): #args = (DEREGISTER, ID, PSPH, MAC)
    if args[3].endswith("\0"):
        args[3] = args[3][:-1]
    registry_lock.acquire()
    for x in range(len(registry)):
        if registry[x][0] == args[1]:
            if registry[x][1] != args[3]:
                registry_lock.release()
                return "30"
            else:
                registry.pop(x)
                registry_lock.release()
                return "20"
    else:
        registry_lock.release()
        return "21"

def login(args, addr): #args = (LOGIN, ID, PSPH, MAC)
    registry_lock.acquire()
    for x in range(len(registry)):
        if registry[x][0] == args[1] and registry[x][3] == args[2]:
            registry[x] = (registry[x][0], registry[x][1], registry[x][2], registry[x][3], args[4])
            print(registry)
            registry_lock.release()
            return "70"
    return "31"

def logoff(args, addr): #args = (LOGOFF, ID)
    registry_lock.acquire()
    for x in range(len(registry)):
        if registry[x][0] == args[1]:
            registry[x] = (registry[x][0], registry[x][1], registry[x][2], registry[x][3], "-65535")
            registry_lock.release()
            return "80"
    return "32"

def query(args, addr): #args = (QUERY, QCODE, ID, TIME, PARAM)
    if args[4].endswith("\0"):
        args[4] = args[4][:-1]
    if args[1] == "01":                   # PARAM = Dev ID to search
        registry_lock.acquire()
        for x in registry:
            if x[0] == args[4]:
                if x[4] != "-65535":
                    registry_lock.release()
                    return ("01", x[0], x[2]+"\n"+x[4])
                else:
                    registry_lock.release()
                    return ("11", x[0], x[4])
        registry_lock.release()
        return ("11", args[4], "-65535")
    elif args[1] == "02":                 # PARAM = TOKEN
        registry_lock.acquire()
        for x in registry:
            if x[0] == args[2]:
                if x[4] != "-65535":
                    registry_lock.release()
                    return ("01", x[0], x[2]+"\n"+j_str)
                else:
                    registry_lock.release()
                    return ("11", x[0], x[4])
        registry_lock.release()
        return ("11", args[4], "-65535")
    elif args[1] == "03":                 # PARAM = TOKEN
        registry_lock.acquire()
        for x in registry:
            if x[0] == args[2]:
                if x[4] != "-65535":
                    registry_lock.release()
                    data_msg_lock.acquire()
                    value = data_msg
                    print("out value: " + value)
                    data_msg_lock.release()
                    return ("01", x[0], x[2]+"\n"+value)
                else:
                    registry_lock.release()
                    return ("11", x[0], x[4])
        registry_lock.release()
        return ("11", args[4], "-65535")
                
def data(args, addr): #args = (DATA, QCODE, ID, TIME, LENGTH, MESSAGE)
    global data_msg
    registry_lock.acquire()
    for x in range(len(registry)):
        if registry[x][0] == args[2]:
            now = datetime.datetime.now()
            out = "{0:%Y-%m-%d %H:%M:%S}".format(now) + " Logged data: " + args[5][:-1] + "\n"
            f.write(out)
            registry_lock.release()
            data_msg_lock.acquire()
            data_msg = args[5][:-1]
            # print("Data = %s" % data_msg)
            data_msg_lock.release()
            return "50"
    return "51"

def process_ack(msg, addr):
    new_msg = msg.split('\t')
    if new_msg[0] == 'REGISTER':
        if not len(new_msg) == 4:
            return False
        else:
            return (register_device(new_msg, addr) , new_msg[1], datetime.datetime.now(), "ACK")
    elif new_msg[0] == 'DEREGISTER':
        if len(new_msg) != 4:
            return False
        else:
            return (deregister(new_msg, addr), new_msg[1], datetime.datetime.now(), "ACK")
    elif new_msg[0] == "LOGIN":
        if len(new_msg) != 5:
            return False
        else:
            return (login(new_msg, addr), new_msg[1], datetime.datetime.now(), "ACK")
    elif new_msg[0] == "LOGOFF":
        if len(new_msg) != 2:
            return False
        else:
            return (logoff(new_msg, addr), new_msg[1], datetime.datetime.now(), "ACK")
    elif new_msg[0] == "QUERY":
        if len(new_msg) != 5:
            return False
        else:
            return (query(new_msg, addr), new_msg[2], datetime.datetime.now(), "DATA")
    elif new_msg[0] == "DATA":
        if len(new_msg) != 6:
            return False
        else:
            return (data(new_msg, addr), new_msg[2], datetime.datetime.now(), "ACK")

def getmac(msg):
    args = msg.split('\t')
    registry_lock.acquire()
    for x in registry:
        if x[0] == args[1]:
            ret_mac = x[1]
            registry_lock.release()
            return ret_mac

def client_handler(client, addr, number):
    while True:
        data = client.recv(1024)
        if not data:
            print("client[", number, "] has exited")
            break
        msg = data.decode('ascii')
        sha = hashlib.sha256(data).hexdigest()
        print("From client[", number, "]:", msg)
        ack = process_ack(msg, addr)
        if ack[3] == "ACK":
            if ack[0] == "30":
                ret_mac = getmac(msg)
                send_msg = "ACK\t" + ack[0]  + "\t" + ack[1] + "\t{0:%Y-%m-%d %H:%M:%S}\t".format(ack[2]) + sha + "\t" + ret_mac + "\0"
            else:
                send_msg = "ACK\t" + ack[0]  + "\t" + ack[1] + "\t{0:%Y-%m-%d %H:%M:%S}\t".format(ack[2]) + sha + "\0"
        elif ack[3] == "DATA":
            if ack[0][2] == "-65535":
                send_msg = "DATA\t" + ack[0][0] + "\t" + ack[1] + "\t{0:%Y-%m-%d %H:%M:%S}\t".format(ack[2]) + "%d" % len(ack[0][1]) + "\t" + ack[0][1] + "\0"
            else:
                send_msg = "DATA\t" + ack[0][0] + "\t" + ack[1] + "\t{0:%Y-%m-%d %H:%M:%S}\t".format(ack[2]) + "%d" % (len(ack[0][1])+len(ack[0][2]) + 1) + "\t" + ack[0][1] + "\n" + ack[0][2] + "\0"
                print(send_msg)
        client.send(send_msg.encode('ascii'))
        if ack[3] == "ACK" and ack[0] == "70":
            send_msg = "QUERY\t00\t" + ack[0] + "\t" + "\t{0:%Y-%m-%d %H:%M:%S}\t".format(ack[2]) + "msg\0"
            client.send(send_msg.encode('ascii'))
    c.close()

def cloud_handler(cloud, dummy):
    cloud = storage.Client.from_service_account_json('Key.json')
    bucket = cloud.get_bucket('triple-circle-237521.appspot.com')
    old_blobs_time=False
    while 1:
        blobs_time = []
        blobs1 = bucket.list_blobs()
        blobs = [a for a in blobs1]
        for x in range(len(blobs)):
            blobs_time.append(blobs[x].updated)
        if old_blobs_time != False:
            for x in range(len(blobs)):
                if blobs_time[x] != old_blobs_time[x]:
                    data = blobs[x].download_as_string().decode('utf-8')
                    print("%s Hass been updated" % blobs[x].public_url)
                    # print(data)                                              # Technically where it should process this data, but this doesn't matter to me that much.
        old_blobs_time = blobs_time
            

s = socket(AF_INET, SOCK_STREAM)
s.bind(('0.0.0.0',  8900))
s.listen(5)
print("server at %s" % getfqdn(''))

start_new_thread(cloud_handler, (0,0))

while True:
    c, addr = s.accept()
    print("Connection from: ", addr[0], ":", addr[1])
    client_lock.acquire()
    start_new_thread(client_handler, (c, addr, clients))
    clients = clients + 1
    client_lock.release()
s.close()
