import socket
import requests
import sys

def check_dns(hostname):
    print(f"\nChecking DNS resolution for {hostname}...")
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✓ DNS resolution successful: {hostname} resolves to {ip}")
        return True
    except socket.gaierror as e:
        print(f"✗ DNS resolution failed: {e}")
        return False

def check_http_connection(url):
    print(f"\nChecking HTTP connection to {url}...")
    try:
        response = requests.get(url, timeout=10)
        print(f"✓ HTTP connection successful: Status code {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ HTTP connection failed: {e}")
        return False

def main():
    print("=== Network Connectivity Test ===\n")
    
    # Test DNS resolution
    hosts_to_check = [
        "api.telegram.org",
        "www.google.com",
        "www.microsoft.com"
    ]
    
    dns_results = {host: check_dns(host) for host in hosts_to_check}
    
    # Test HTTP connections
    urls_to_check = [
        "https://api.telegram.org",
        "https://www.google.com",
        "https://www.microsoft.com"
    ]
    
    http_results = {url: check_http_connection(url) for url in urls_to_check}
    
    # Summary
    print("\n=== Test Summary ===\n")
    print("DNS Resolution:")
    for host, result in dns_results.items():
        print(f"{host}: {'✓ Success' if result else '✗ Failed'}")
    
    print("\nHTTP Connections:")
    for url, result in http_results.items():
        print(f"{url}: {'✓ Success' if result else '✗ Failed'}")
    
    # Recommendations
    print("\n=== Recommendations ===\n")
    if not dns_results.get("api.telegram.org", False):
        print("- DNS resolution for api.telegram.org is failing. This could be due to:")
        print("  * Network connectivity issues")
        print("  * DNS server configuration")
        print("  * Firewall blocking DNS requests")
        print("  * VPN or proxy settings")
    
    if not http_results.get("https://api.telegram.org", False):
        print("- HTTP connection to api.telegram.org is failing. This could be due to:")
        print("  * Network connectivity issues")
        print("  * Firewall blocking outbound connections")
        print("  * VPN or proxy settings")
        print("  * SSL/TLS issues")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error running tests: {e}")
