import requests
import base64
import re
import sys

URLS = {
    'direct': 'https://raw.githubusercontent.com/Loyalsoldier/clash-rules/release/direct.txt',
    'apple': 'https://raw.githubusercontent.com/Loyalsoldier/clash-rules/release/apple.txt',
    'icloud': 'https://raw.githubusercontent.com/Loyalsoldier/clash-rules/release/icloud.txt',
    'proxy': 'https://raw.githubusercontent.com/Loyalsoldier/clash-rules/release/proxy.txt',
    'gfw': 'https://raw.githubusercontent.com/Loyalsoldier/clash-rules/release/gfw.txt',
    'gfwlist': 'https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt',
}

DOMESTIC_FILE = 'domestic.conf'
OVERSEA_FILE = 'oversea.conf'

CUSTOM_DOMESTIC = {'speedtest.net', 'ookla.net'}

CLEAN_RE = re.compile(r'^(?:(?:DOMAIN-SUFFIX|DOMAIN|HOST|IP-CIDR|GEOIP|URL-REGEX|FINAL),?|\|\|?|@@|\/|\^|!|\[|\]|\$|#|\*)', re.IGNORECASE)
SUFFIX_RE = re.compile(r',.*$') 

def fetch_content(url):
    """Fetch content from URL and handle errors."""
    print(f"Fetching: {url}")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return ""

def clean_and_extract_domains(content):
    """Clean content, extract pure domains, handle deduplication and formatting."""
    domains = set()
    
    if content.startswith('AAECA'):
        try:
            content = base64.b64decode(content).decode('utf-8')
        except Exception as e:
            print(f"Base64 decode failed: {e}", file=sys.stderr)
            return set()
            
    lines = content.splitlines()
    for line in lines:
        line = line.strip().lower()

        if not line or line.startswith(('#', '[', 'ip-cidr', 'geoip', 'url-regex')):
            continue

        line = CLEAN_RE.sub('', line)
        line = SUFFIX_RE.sub('', line)

        line = re.sub(r'[^a-z0-9\.]', '', line)
        line = line.lstrip('.') 
        
        if '.' in line and line:
            domains.add(line)
            
    return domains

def generate_lists():
    """Download all lists and generate domestic.conf and oversea.conf."""
    domestic_domains = set(CUSTOM_DOMESTIC)
    oversea_domains = set()

    domestic_sources = ['direct', 'apple', 'icloud']
    for key in domestic_sources:
        content = fetch_content(URLS[key])
        domains = clean_and_extract_domains(content)
        domestic_domains.update(domains)

    oversea_sources = ['proxy', 'gfw', 'gfwlist']
    for key in oversea_sources:
        content = fetch_content(URLS[key])
        domains = clean_and_extract_domains(content)
        oversea_domains.update(domains)

    oversea_domains.difference_update(domestic_domains)
    
    final_domestic = sorted(list(domestic_domains))
    final_oversea = sorted(list(oversea_domains))

    try:
        with open(DOMESTIC_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(final_domestic) + '\n')
            
        with open(OVERSEA_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(final_oversea) + '\n')
            
    except IOError as e:
        print(f"Error writing files: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\n--- Results ---")
    print(f"Domestic domains written to {DOMESTIC_FILE}: {len(final_domestic)}")
    print(f"Oversea domains written to {OVERSEA_FILE}: {len(final_oversea)}")


if __name__ == "__main__":
    generate_lists()
