from socket import *
from dns import resolver, message, name, rdatatype, query, rrset
import time

host = '127.0.0.1'
port = 53
host_addr = (host, port)
default_rdclass = 1
default_timeout_sec = 3
response_timeout_sec = 60
current_request_expiration = 0
dns_cache = resolver.LRUCache()
ROOT_SERVERS = ("198.41.0.4",
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
                "202.12.27.33"
                )


def get_response(dname, rdtype, ip_stack = []):
    cache_key = (dname, rdtype, default_rdclass)
    cached_ans = dns_cache.get(cache_key)
    if cached_ans != None:
        if time.time() < cached_ans.expiration:
            print('cache hit!')
            return cached_ans.response
        
    if ip_stack == []:
        ip_stack = list(ROOT_SERVERS)

    been_there = set()
    while len(ip_stack) > 0:
        if time.time() > current_request_expiration:
            print(current_request_expiration)
            print(time.time())
            break
        cur_ip = ip_stack.pop()
        if (cur_ip in been_there):
            continue

        been_there.add(cur_ip)
        dns_query = message.make_query(dname, rdtype)
        try:
            response = query.udp(dns_query, cur_ip, default_timeout_sec)
        except:
            continue

        if response.answer:
            res_def = set()
            for res in response.answer:
                res_def.add(res.name.to_text())

            all_resolved = True
            for res in response.answer:
                if res.rdtype == rdatatype.CNAME and res[0].to_text() not in res_def:
                    res_response = get_response(name.from_text(res[0].to_text()), rdtype)
                    if res_response == None:
                        all_resolved = False
                        break
                    for res_res in res_response.answer:
                        if res_res.rdtype == rdatatype.A or res_res.rdtype == rdatatype.AAAA:
                            res_def.add(res_res.name)
                    response.answer += res_response.answer
                    response.authority += res_response.authority
                    response.additional += res_response.additional

            if not all_resolved:
                continue
            ans = resolver.Answer(dname, rdtype, default_rdclass, response)
            dns_cache.put(cache_key, ans)
            return response
        elif response.additional:
            for add in response.additional:
                    if add.rdtype == rdatatype.A or add.rdtype == rdatatype.AAAA:
                        for add_ip in add:
                            ip_stack.append(str(add_ip))
        elif response.authority:
            for auth in response.authority:
                if auth.rdtype == rdatatype.NS:
                    for auth_name in auth:
                        auth_resp = get_response(name.from_text(auth_name.to_text()), rdatatype.A)
                        if auth_resp != None and auth_resp.answer:
                            for auth_ans in auth_resp.answer:
                                if auth_ans.rdtype == rdatatype.A or auth_ans.rdtype == rdatatype.AAAA:
                                    for auth_ip in auth_ans:
                                        ip_stack.append(str(auth_ip))
                            break
                elif auth.rdtype == rdatatype.SOA:
                    ans = resolver.Answer(dname, rdtype, default_rdclass, response)
                    dns_cache.put(cache_key, ans)
                    return response

    # negative caching
    dummy_msg = message.make_query(dname, rdtype)
    dummy_response = message.make_response(dummy_msg)
    ans = resolver.Answer(dname, rdtype, default_rdclass, dummy_response)
    dns_cache.put(cache_key, ans)
    return None
            
        
def main():
    global current_request_expiration
    udp_socket = query._make_socket(af=AF_INET, type=SOCK_DGRAM, source=host_addr)
    time.sleep(3)
    try:
        while True:
            try:
                msg, t, addr = query.receive_udp(udp_socket)
            except:
                udp_socket.close()
                udp_socket = query._make_socket(af=AF_INET, type=SOCK_DGRAM, source=host_addr)
                time.sleep(3)
                msg, t, addr = query.receive_udp(udp_socket)
            request = msg.question[0]
            request_name = request.name
            print(request_name)
            requested_rdtype = request.rdtype
            current_request_expiration = time.time() + response_timeout_sec
            response_data = get_response(request_name, requested_rdtype)
            response = message.make_response(msg)
            if response_data == None:
                print('found nothing')
                pass
            else:
                response.answer = response_data.answer
                response.authority = response_data.authority
                response.additional = response_data.additional
                print(response)
            query.send_udp(udp_socket, response, addr)
        udp_socket.close()
    except Exception as e:
        udp_socket.close()
        print(str(e))
        raise e

if __name__ == "__main__":
    main()
