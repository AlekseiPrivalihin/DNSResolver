from socket import *
from dns import resolver, message
import time

host = 'localhost'
port = 53
host_addr = (host, port)

#socket - функция создания сокета 
#первый параметр socket_family может быть AF_INET или AF_UNIX
#второй параметр socket_type может быть SOCK_STREAM(для TCP) или SOCK_DGRAM(для UDP)
udp_socket = socket(AF_INET, SOCK_DGRAM)
#bind - связывает адрес и порт с сокетом
udp_socket.bind(host_addr)
my_resolver = resolver.Resolver()
cache = {}

while True:
    print('awaiting query...')
    msgB, addr = udp_socket.recvfrom(1024)
    msg = msgB.decode()
    msg = "".join(msg)
    print('received ' + msg + ' query from ' + addr[0] + ':' + str(addr[1]))
    if msg == 'KYS':
        udp_socket.sendto(b'server shutting down', addr)
        break
    
    ans_found = False
    if (msg in cache.keys()):
        rec_ans, exp_time = cache[msg]
        if time.time() < exp_time:
            print('cached answer found')
            ans_found = True

    if not ans_found:
        print('cached answer not found or expired, requesting new answer')
        full_ans = resolver.query(msg)
        expiration_time = full_ans.expiration
        print('new answer is valid by: ' + str(expiration_time))
        ans = full_ans.response.to_text()
        cache[msg] = (ans, expiration_time)

    udp_socket.sendto(cache[msg][0].encode(), addr)
    print('answer "' + cache[msg][0] + '" given for the query')
    
udp_socket.close()
print('shutting down server')
