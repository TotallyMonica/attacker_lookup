#!/usr/bin/env python3
import socket
import re
import csv
import sys
import ipinfo

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
    
    elif '--no-isp' not in sys.argv:
        print("A token for ipinfo.io has not been provided. Limited IP information queries will be performed.")
        print("If you're looking for more information than what's provided, provide your access token using the argument --ipinfo-token {token}")
    
    # Opt out of rDNS queries
    if "--no-rdns" in sys.argv:
        query_rdns = False
    else:
        headers.append('rDNS result')
    
    # Opt out of ISP queries
    if "--no-isp-queries" in sys.argv:
        query_isp = True
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

    # Add repeated IP addresses to the deduplicated list
    for dedup_addr in deduplicated_ipv4_addresses:
        count = 0

        for orig_addr in ipv4_addresses:
            if dedup_addr == orig_addr:
                count += 1
        
        dedup_addr.append(count)
    
    # If the user requested the rDNS query, append the rDNS result to the table and JSON
    if query_rdns:
        for addr in deduplicated_ipv4_addresses:
            result = domain_info(addr[0])
            addr.append(result)
    
    # If the user requested the ISP info, append select ISP results to the table and the entire results to the JSON
    # Table format: ['City', 'Region', 'Country', 'ISP']
    if query_isp:
        for addr in deduplicated_ipv4_addresses:
            results = isp_info(addr[0], ipinfo_token)
            addr.append(results.city)
            addr.append(results.region)
            addr.append(results.country)
            addr.append(results.org)
    
    # Create a report of the queried IP addresses:
    with open("report_ips.csv", "w") as filp:
        writer = csv.writer(filp)
        writer.writerow(headers)
        writer.writerows(deduplicated_ipv4_addresses)

if __name__ == '__main__':
    main()