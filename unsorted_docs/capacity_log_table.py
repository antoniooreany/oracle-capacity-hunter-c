import csv
import re

log = '''Trying region=eu-milan-1 ad=awQc:EU-MILAN-1-AD-1 shape=VM.Standard.A1.Flex (4 OCPUs, 24 GB RAM). Console: https://cloud.oracle.com/compute/instances?region=eu-milan-1&compartmentId=ocid1.tenancy.oc1..aaaaaaaahr5jbcayzsdxdovs7saoaacfzgmfaue7xrm5t6cj5hokkan3wddq url=https://cloud.oracle.com/compute/instances?region=eu-milan-1&compartmentId=ocid1.tenancy.oc1..aaaaaaaahr5jbcayzsdxdovs7saoaacfzgmfaue7xrm5t6cj5hokkan3wddq;cpu=4 OCPUs;ram=24 GB RAM;shape=VM.Standard.A1.Flex;region=eu-milan-1;code=LimitExceeded;status=400 No capacity anywhere this round. Sleeping 30s. Console (first region): https://cloud.oracle.com/compute/instances?region=eu-milan-1&compartmentId=ocid1.tenancy.oc1..aaaaaaaahr5jbcayzsdxdovs7saoaacfzgmfaue7xrm5t6cj5hokkan3wddq Trying region=eu-milan-1 ad=awQc:EU-MILAN-1-AD-1 shape=VM.Standard.A1.Flex (4 OCPUs, 24 GB RAM). Console: https://cloud.oracle.com/compute/instances?region=eu-milan-1&compartmentId=ocid1.tenancy.oc1..aaaaaaaahr5jbcayzsdxdovs7saoaacfzgmfaue7xrm5t6cj5hokkan3wddq url=https://cloud.oracle.com/compute/instances?region=eu-milan-1&compartmentId=ocid1.tenancy.oc1..aaaaaaaahr5jbcayzsdxdovs7saoaacfzgmfaue7xrm5t6cj5hokkan3wddq;cpu=4 OCPUs;ram=24 GB RAM;shape=VM.Standard.A1.Flex;region=eu-milan-1;code=TooManyRequests;status=429 No capacity anywhere this round. Sleeping 63s. Console (first region): https://cloud.oracle.com/compute/instances?region=eu-milan-1&compartmentId=ocid1.tenancy.oc1..aaaaaaaahr5jbcayzsdxdovs7saoaacfzgmfaue7xrm5t6cj5hokkan3wddq '''

# For brevity, we'll assume the pattern repeats similarly; in a real case, you'd paste the full log.

entries = []
pattern_try = re.compile(r"Trying region=(?P<region>[^ ]+) ad=(?P<ad>[^ ]+) shape=(?P<shape>[^ ]+) \((?P<cpu_text>[^,]+), (?P<ram_text>[^)]+)\). Console: (?P<console_url>\S+)")
pattern_detail = re.compile(r"url=(?P<url>[^;]+);cpu=(?P<cpu>[^;]+);ram=(?P<ram>[^;]+);shape=(?P<shape2>[^;]+);region=(?P<region2>[^;]+);code=(?P<code>[^;]+);status=(?P<status>[^ ]+) .*?Sleeping (?P<sleep>\d+)s")

# Split on 'Trying region=' to find blocks
parts = log.split('Trying region=')
for part in parts[1:]:
    # reconstruct leading keyword
    chunk = 'Trying region=' + part
    m1 = pattern_try.search(chunk)
    m2 = pattern_detail.search(chunk)
    if m1 and m2:
        row = {
            'region': m1.group('region'),
            'availability_domain': m1.group('ad'),
            'shape': m1.group('shape'),
            'cpu_declared': m1.group('cpu_text'),
            'ram_declared': m1.group('ram_text'),
            'console_url': m1.group('console_url'),
            'api_url': m2.group('url'),
            'cpu_param': m2.group('cpu'),
            'ram_param': m2.group('ram'),
            'shape_param': m2.group('shape2'),
            'region_param': m2.group('region2'),
            'error_code': m2.group('code'),
            'http_status': m2.group('status'),
            'sleep_seconds': m2.group('sleep'),
        }
        entries.append(row)

import os
os.makedirs('output', exist_ok=True)
filepath = 'output/oci_log_parsed.csv'
with open(filepath, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(entries[0].keys()))
    writer.writeheader()
    writer.writerows(entries)

filepath