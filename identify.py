#!/usr/bin/env python3

# Included packages
import socket
import re
import csv
import sys

# Pip packages
import ipinfo
from prettytable import PrettyTable

# This section was assisted with ChatGPT, I really know nothing whenever it comes to DNS queries
def domain_info(address):
    domain = ""

    try:
        domain = socket.gethostbyaddr(address)[0]
    except socket.herror:
        domain = ""
    except socket.gaierror:
        print("Unable to perform rDNS lookup. Are you connected to the internet?")
        domain = ""
    
    return domain

# Section assisted with ChatGPT.
# Should only be carried out if a token for ipinfo.io is provided
def isp_info(address, token):
    if token == "":
        print("No token provided, data will be limited")
    
    if token == "--IGNORE-WARNING--":
        token = ""
    
    handler = ipinfo.getHandler(token)
    query = handler.getDetails(address)

    return query

def main():
    headers = ["Address", "Try count"]
    ipv4_addresses = []
    deduplicated_ipv4_addresses = []
    log_file = ""
    ipinfo_token = "--IGNORE--"
    query_rdns = True
    query_isp = True

    # Argument checks
    # Check for a provided log file to use
    if "--log" in sys.argv or "--log-file" in sys.argv:
        if "--log" in sys.argv:
            argument = sys.argv.index("--log")
        else:
            argument = sys.argv.index("--log-file")
        log_file = sys.argv[ argument + 1 ]
    else:
        print("Error: A log file has not been provided.")
        print(f"Syntax: {sys.argv[0]} --log-file logfile.log")
        print()
        print("Possible logs to use:")
        print("\tSSH server logs")
        print("\tjournalctl logs")
        exit()
    
    # Check if an ipinfo.io token was provided.
    # If no token was used, give a warning about limited results.
    if "--ipinfo-token" in sys.argv:
        pointer = sys.argv.index("--ipinfo-token")
        try:
            ipinfo_token = sys.argv[ pointer + 1 ]
        except IndexError:
            print("A token for ipinfo.io has not been provided. Limited IP information queries will be performed.")
            print("If you're looking for more information than what's provided, provide your access token using the argument --ipinfo-token {token}")
    
    elif '--no-isp-queries' not in sys.argv:
        print("A token for ipinfo.io has not been provided. Limited IP information queries will be performed.")
        print("If you're looking for more information than what's provided, provide your access token using the argument --ipinfo-token {token}")
    
    # Opt out of rDNS queries
    if "--no-rdns" in sys.argv:
        query_rdns = False
    else:
        headers.append('rDNS result')
    
    # Opt out of ISP queries
    if "--no-isp-queries" in sys.argv:
        query_isp = False
    else:
        headers.append('City')
        headers.append('Region')
        headers.append('Country')
        headers.append('ISP')

    # Import the text file and add all potential references to an IPv4 address
    with open(log_file, "r") as filp:
        lines = filp.readlines()

        for line in lines:
            ipv4_addresses.append( re.findall( "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", line ) )

    # Go through and remove lists with more than one entry in it
    for address in ipv4_addresses:
        if len(address) > 1:
            while len(address) > 1:
                ipv4_addresses.append([address[0]])
                address.pop(0)

    # Text document may have blank lines so remove those.
    while [] in ipv4_addresses:
        pointer = ipv4_addresses.index([])
        ipv4_addresses.pop(pointer)

    # Remove duplicate addresses
    for addr in ipv4_addresses:
        if addr not in deduplicated_ipv4_addresses:
            deduplicated_ipv4_addresses.append(addr)
    
    # Remove non-publically accessible addresses
    for addr in deduplicated_ipv4_addresses:
        delimited_ips = addr[0].split('.')

        # Check if it's in the 10.0.0.0/8 subnet
        if int(delimited_ips[0]) == 10:
            deduplicated_ipv4_addresses.remove(addr)
        
        # Check if it's in the 172.16.0.0/12 subnet
        elif int(delimited_ips[0]) == 172 and ( int(delimited_ips[1]) >= 16 and int(delimited_ips[1]) <= 31):
            deduplicated_ipv4_addresses.remove(addr)
        
        # Check if it's in the 192.168.0.0/16 subnet
        elif int(delimited_ips[0]) == 192 and int(delimited_ips[1]) == 168:
            deduplicated_ipv4_addresses.remove(addr)
        
        # Check if the address is in the 169.254.0.0/16 subnet, in which it is a link-local address
        elif int(delimited_ips[0]) == 169 and int(delimited_ips[1]) == 254:
            deduplicated_ipv4_addresses.remove(addr)
        
        # Check if the address is in the 0.0.0.0/8, in which the address is unusable
        elif int(delimited_ips[0]) == 0:
            deduplicated_ipv4_addresses.remove(addr)
        
        # Check if the address is in the 127.0.0.0/8 subnet, in which the address is itself
        elif int(delimited_ips[0]) == 127:
            deduplicated_ipv4_addresses.remove(addr)

    # Add repeated IP addresses to the deduplicated list
    for dedup_addr in deduplicated_ipv4_addresses:
        count = 0

        for orig_addr in ipv4_addresses:
            if dedup_addr == orig_addr:
                count += 1
        
        dedup_addr.append(count)
    
    # If the user requested the rDNS query, append the rDNS result to the table and JSON
    if query_rdns:
        print("Beginning rDNS lookup...")
        for addr in deduplicated_ipv4_addresses:
            result = domain_info(addr[0])
            addr.append(result)
    
    # If the user requested the ISP info, append select ISP results to the table and the entire results to the JSON
    # Table format: ['City', 'Region', 'Country', 'ISP']
    if query_isp:
        print("Beginning ISP queries")
        for addr in deduplicated_ipv4_addresses:
            results = isp_info(addr[0], ipinfo_token)
            try:
                addr.append(results.city)
            except AttributeError:
                addr.append("")
            try:
                addr.append(results.region)
            except AttributeError:
                addr.append("")
            try:
                addr.append(results.country)
            except AttributeError:
                addr.append("")
            try:
                addr.append(results.org)
            except AttributeError:
                addr.append("")
    # Create a report of the queried IP addresses:
    with open("report_ips.csv", "w") as filp:
        writer = csv.writer(filp)
        writer.writerow(headers)
        writer.writerows(deduplicated_ipv4_addresses)
    
    # Print out a table
    table = PrettyTable()
    table.field_names = headers
    table.add_rows(deduplicated_ipv4_addresses)
    print(table)

if __name__ == '__main__':
    main()
