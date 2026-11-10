
from mcp.server.fastmcp import FastMCP


mcp = FastMCP('network-utils-server')



# ---------------- Tools ----------------
@mcp.tool()
def check_url_status(url: str, timeout: int = 10) -> str:
    """Performs a comprehensive HTTP/HTTPS request analysis including:
    - HTTP status code and reason
    - Response time
    - Content length and type
    - Server information
    - SSL certificate info (for HTTPS)
    - Redirect chain
    Returns a detailed connectivity report."""
    import urllib.request
    import urllib.error
    import time
    import ssl
    from datetime import datetime
    
    try:
        # Track redirects
        class RedirectHandler(urllib.request.HTTPRedirectHandler):
            def __init__(self):
                self.redirects = []
            
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                self.redirects.append((code, newurl))
                return urllib.request.HTTPRedirectHandler.redirect_request(
                    self, req, fp, code, msg, headers, newurl
                )
        
        redirect_handler = RedirectHandler()
        opener = urllib.request.build_opener(redirect_handler)
        
        # Make request
        start_time = time.time()
        request = urllib.request.Request(url)
        request.add_header('User-Agent', 'MCP-Network-Utils/1.0')
        
        response = opener.open(request, timeout=timeout)
        elapsed_time = (time.time() - start_time) * 1000  # milliseconds
        
        # Gather information
        status_code = response.getcode()
        headers = dict(response.headers)
        content_length = headers.get('Content-Length', 'Unknown')
        content_type = headers.get('Content-Type', 'Unknown')
        server = headers.get('Server', 'Unknown')
        
        report = f"""
URL Status Check: {url}
{'='*70}
Connection:
  Status: {status_code} (Success)
  Response Time: {elapsed_time:.2f} ms
  
Headers:
  Content-Type: {content_type}
  Content-Length: {content_length} bytes
  Server: {server}
"""
        
        # Add redirect information
        if redirect_handler.redirects:
            report += f"\nRedirects: {len(redirect_handler.redirects)}"
            for i, (code, redir_url) in enumerate(redirect_handler.redirects, 1):
                report += f"\n  {i}. [{code}] -> {redir_url}"
        
        # SSL information for HTTPS
        if url.startswith('https://'):
            try:
                import socket
                from urllib.parse import urlparse
                
                parsed = urlparse(url)
                hostname = parsed.hostname
                
                context = ssl.create_default_context()
                with socket.create_connection((hostname, 443), timeout=timeout) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        
                        report += f"\n\nSSL Certificate:"
                        report += f"\n  Subject: {dict(x[0] for x in cert['subject'])}"
                        report += f"\n  Issuer: {dict(x[0] for x in cert['issuer'])}"
                        report += f"\n  Valid from: {cert['notBefore']}"
                        report += f"\n  Valid until: {cert['notAfter']}"
                        report += f"\n  Version: {cert['version']}"
            except Exception as ssl_err:
                report += f"\n\nSSL Info: Unable to fetch ({ssl_err})"
        
        # Additional useful headers
        interesting_headers = ['Cache-Control', 'Set-Cookie', 'Last-Modified', 'ETag', 'X-Powered-By']
        found_headers = {k: v for k, v in headers.items() if k in interesting_headers}
        if found_headers:
            report += f"\n\nAdditional Headers:"
            for k, v in found_headers.items():
                report += f"\n  {k}: {v[:100]}{'...' if len(v) > 100 else ''}"
        
        return report.strip()
        
    except urllib.error.HTTPError as e:
        return f"HTTP Error: {e.code} {e.reason}\nURL: {url}"
    except urllib.error.URLError as e:
        return f"URL Error: {e.reason}\nURL: {url}"
    except Exception as e:
        return f"Failed to check URL: {e}"


@mcp.tool()
def dns_lookup(hostname: str, record_type: str = 'A') -> str:
    """Performs DNS lookup and returns comprehensive DNS information:
    - A/AAAA records (IPv4/IPv6 addresses)
    - MX records (Mail servers)
    - NS records (Name servers)
    - TXT records (Text records)
    - CNAME records (Aliases)
    - SOA records (Start of Authority)
    
    Args:
        hostname: The domain name to lookup
        record_type: DNS record type (A, AAAA, MX, NS, TXT, CNAME, SOA, ALL)
    
    Returns detailed DNS information."""
    import socket
    import subprocess
    import re
    
    try:
        report = f"""
DNS Lookup: {hostname}
{'='*70}
"""
        
        # Basic A record lookup using socket
        if record_type in ['A', 'ALL']:
            try:
                ip_addresses = socket.getaddrinfo(hostname, None, socket.AF_INET)
                unique_ips = list(set([addr[4][0] for addr in ip_addresses]))
                report += f"\nA Records (IPv4):"
                for ip in unique_ips:
                    report += f"\n  {ip}"
            except Exception as e:
                report += f"\nA Records: Error - {e}"
        
        # Try AAAA (IPv6)
        if record_type in ['AAAA', 'ALL']:
            try:
                ipv6_addresses = socket.getaddrinfo(hostname, None, socket.AF_INET6)
                unique_ipv6 = list(set([addr[4][0] for addr in ipv6_addresses]))
                report += f"\n\nAAAA Records (IPv6):"
                for ip in unique_ipv6:
                    report += f"\n  {ip}"
            except Exception:
                report += f"\n\nAAAA Records: None found"
        
        # Use nslookup for other record types
        if record_type in ['MX', 'NS', 'TXT', 'CNAME', 'SOA', 'ALL']:
            types_to_check = [record_type] if record_type != 'ALL' else ['MX', 'NS', 'TXT', 'CNAME', 'SOA']
            
            for rtype in types_to_check:
                try:
                    result = subprocess.run(
                        ['nslookup', '-type=' + rtype, hostname],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    output = result.stdout
                    
                    # Parse the output
                    if 'answer:' in output.lower() or rtype.lower() in output.lower():
                        # Extract relevant lines
                        lines = [line.strip() for line in output.split('\n') 
                                if line.strip() and not line.startswith('Server:') 
                                and not line.startswith('Address:') 
                                and not line.startswith('Non-authoritative')]
                        
                        relevant_lines = []
                        capture = False
                        for line in lines:
                            if hostname in line or rtype.lower() in line.lower():
                                capture = True
                            if capture and line:
                                relevant_lines.append(line)
                        
                        if relevant_lines:
                            report += f"\n\n{rtype} Records:"
                            for line in relevant_lines[:10]:  # Limit output
                                report += f"\n  {line}"
                    else:
                        report += f"\n\n{rtype} Records: None found"
                        
                except subprocess.TimeoutExpired:
                    report += f"\n\n{rtype} Records: Timeout"
                except FileNotFoundError:
                    report += f"\n\n{rtype} Records: nslookup not available"
                except Exception as e:
                    report += f"\n\n{rtype} Records: Error - {e}"
        
        # Reverse DNS lookup
        if record_type in ['A', 'ALL']:
            try:
                ip_addresses = socket.getaddrinfo(hostname, None, socket.AF_INET)
                if ip_addresses:
                    first_ip = ip_addresses[0][4][0]
                    reverse_name = socket.gethostbyaddr(first_ip)[0]
                    report += f"\n\nReverse DNS (PTR):"
                    report += f"\n  {first_ip} -> {reverse_name}"
            except Exception:
                pass
        
        return report.strip()
        
    except Exception as e:
        return f"Failed to perform DNS lookup: {e}"


if __name__ == "__main__":
    mcp.run()
