from socket import *
from dns import resolver, message, name, rdatatype, query, rrset
import time
# 192.168.31.1
host = '127.0.0.1'
port = 53
host_addr = (host, port)
cache = {}
ROOT_SERVERS = (["198.41.0.4",
                    "199.9.14.201",
                    "192.33.4.12",
                    "199.7.91.13",
                    "192.203.230.10",
                    "192.5.5.241",
                    "192.112.36.4",
                    "198.97.190.53",
                    "192.36.148.17",
                    "192.58.128.30",
                    "193.0.14.129",
                    "199.7.83.42",
                    "202.12.27.33"],
                [])
                

def get_IP(domains_list, cur_idx = -1):
    domain_name = ".".join(domains_list)
    to_look_up = ".".join(domains_list[cur_idx:])
    if to_look_up in cache.keys(): # and time.time() < cache[to_look_up][1]:
        print('Found IP adress for ' + to_look_up + ' in cache!')
        print(cache)
        if cur_idx + len(domains_list) == 0:
            return cache[to_look_up]
        else:
            return get_IP(domains_list, cur_idx - 1)

    try_IPs = ([], [])
    if cur_idx == -1:
        try_IPs = ROOT_SERVERS
    else:
        try_IPs = cache[".".join(domains_list[cur_idx + 1:])]

    # IPv4
    received_IPs = ([], [])
    for ip in try_IPs[0] + try_IPs[1]:
        try:
            IPv4_query = message.make_query(name.from_text(domain_name), rdatatype.A)
            response = query.udp(IPv4_query, ip, 3)
            print(response.to_text())
            if response.answer:
                print('Wooo!')
                for received_IP in response.answer:
                    if received_IP.rdtype == rdatatype.A:
                        received_IPs[0].append(received_IP.to_text().split('IN A ')[1].split('\n')[0])

                break
            elif response.additional:
                print('Eeeh')
                for received_IP in response.additional:
                    if received_IP.rdtype == rdatatype.A:
                        received_IPs[0].append(received_IP.to_text().split('IN A ')[1].split('\n')[0])
                    elif received_IP.rdtype == rdatatype.AAAA:
                        received_IPs[1].append(received_IP.to_text().split('IN AAAA ')[1].split('\n')[0])

                break
            elif response.authority:
                print('UUUGH')
                for authority_address in response.authority:
                    authority_name = authority_address.to_text().split('IN NS')[1].split('\n')[0]
                    authority_domain_list = authority_name.split('.')[:-2]
                    try_more_IPs = get_IP(authority_domain_list)
                    try_IPs[0] += try_more_IPs[0]
                    try_IPs[1] += try_more_IPs[1]

            '''
            IPv6_query = message.make_query(name.from_text(domains_list[0]), rdatatype.AAAA)
            response = query.udp(IPv6_query, ip, 3)
            if response.answer:
                for received_IP in response.answer:
                    if received_IP.rdtype == rdatatype.AAAA:
                        received_IPs[1].append(received_IP.to_text().split('IN AAAA ')[1].split('\n')[0])

                break
            elif response.additional:
                for received_IP in response.additional:
                    print(received_IP.rdtype)
                    if received_IP.rdtype == rdatatype.A:
                        received_IPs[0].append(received_IP.to_text().split('IN A ')[1].split('\n')[0])
                    elif received_IP.rdtype == rdatatype.AAAA:
                        received_IPs[1].append(received_IP.to_text().split('IN AAAA ')[1].split('\n')[0])

                break
            '''
            
        except:
            continue

    if len(received_IPs[0]) + len(received_IPs[1]) > 0:
        cache[to_look_up] = received_IPs
    else:
        return ([], [])

    print(to_look_up)
    print(cache[to_look_up])
    if cur_idx + len(domains_list) == 0:
        return received_IPs
    else:
        return get_IP(domains_list, cur_idx - 1)

def main():
    try:
        while True:
            print('awaiting query...')
            # msgB, addr = udp_socket.recvfrom(1024)
            udp_socket = socket(AF_INET, SOCK_DGRAM)
            udp_socket.bind(host_addr)
            msg, t, addr = query.receive_udp(udp_socket)
            print('got query')
            # msg = message.from_wire(msgB)
            # print('received "' + msg.to_text() + '" query from ' + addr[0] + ':' + str(addr[1]))
            request = msg.question[0]
            domains_list = request.to_text()[0:-6].split('.')
            domains_list = ['fclmnews', 'ru']
            domain_name = ".".join(domains_list)

            IP_list = get_IP(domains_list)
            print(IP_list[0])
            print(IP_list[1])
            break

            response = message.make_response(msg)
            response_txt = response.to_text().split(';ANSWER\n')
            response_str = response_txt[0] + ';ANSWER\n'
            if (len(IP_list[0]) + len(IP_list[1])) == 0:
                print('found nothing!')
            else:
                response.answer = []
                for ip in IP_list[0]:
                    response_str += domain_name + '. IN A ' + ip + '\n'
                for ip in IP_list[1]:
                    response_str += domain_name + '. IN AAAA ' + ip + '\n'
        
            response_str = response_str + response_txt[1]
            # print('answer "' + response_str + '" given for the query')
            msg_response = message.from_text(response_str)
            print('trying to send response')
            query.send_udp(udp_socket, msg_response, addr)
            udp_socket.close()
            print('response sent')
            # udp_socket.sendto(msg_response.to_wire('me'), addr)
    
        udp_socket.close()
        print('shutting down server')
    except Exception as e:
        print(str(e))
        print('emergency shutdown!')
        udp_socket.close()
        raise e

main()
