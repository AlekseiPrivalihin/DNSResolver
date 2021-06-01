from socket import *

host = 'localhost'
host_port = 53
send_port = 2002
host_addr = (host, host_port)
send_addr = (host, send_port)
udp_socket = socket(AF_INET, SOCK_DGRAM)
udp_socket.bind(send_addr)
udp_socket.settimeout(10)

while True:
    print('Please input query or Q to quit')
    msg = input().rstrip()
    if msg == 'Q':
        break
    else:
        udp_socket.sendto(msg.encode(), host_addr)

    msgB, addr = udp_socket.recvfrom(1024)
    msg = msgB.decode()
    msg = "".join(msg)
    print('received "' + msg + '" answer from ' + addr[0] + ':' + str(addr[1]))

udp_socket.close()
print('Shutting down client')
