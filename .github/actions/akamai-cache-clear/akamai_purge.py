#!/usr/bin/env python3

import sys
import requests
from akamai.edgegrid import EdgeGridAuth, EdgeRc
from urllib.parse import urljoin

edgerc = EdgeRc('~/.edgerc.txt')
section = 'default'
baseurl = 'https://%s' % edgerc.get(section, 'host')

session = requests.Session()
session.auth = EdgeGridAuth.from_edgerc(edgerc, section)

PURGE_TYPE_INVALIDATE = 'invalidate'
PURGE_TYPE_DELETE = 'delete'
VALID_PURGE_TYPES = [PURGE_TYPE_INVALIDATE, PURGE_TYPE_DELETE]


def get_cpcode_description(cpcode):
    path = f'/cprg/v1/cpcodes/{cpcode}'
    headers = {
        "Accept": "application/json"
    }

    result = session.get(urljoin(baseurl, path), headers=headers)

    if result.status_code == 200:
        cpcode_details = result.json()
        description = cpcode_details.get('description', 'No description available')
        print(f"CP Code: {cpcode} - Description: {description}")
    else:
        print(f"Failed to retrieve CP code details. Status: {result.status_code}")
        print(result.json())


def purge_content(network, cpcodes, purge_methods):
    for cpcode in cpcodes:
        for purge_method in purge_methods:
            path = f'/ccu/v3/{purge_method}/cpcode/{network}'
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            payload = {
                "objects": [
                    cpcode
                ]
            }

            result = session.post(urljoin(baseurl, path), headers=headers, json=payload)

            if result.status_code == 201:
                response_data = result.json()
                print(f"Successfully sent {purge_method} purge request for CP Code {cpcode}. Status: {result.status_code}")
                print(f"HTTP Status: {response_data['httpStatus']}")
                print(f"Detail: {response_data['detail']}")
                print(f"Purge Type: {purge_method}")
                print(f"Purge ID: {response_data['purgeId']}")
                print(f"Estimated Time for Completion: {response_data['estimatedSeconds']} seconds")
            else:
                print(f"Failed to purge content using {purge_method} for CP Code {cpcode}. Status: {result.status_code}")
                print(result.json())

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python akamai_purge.py <cpcode1> [<cpcode2> ...] [purge_method1] [purge_method2] ...")
        sys.exit(1)

    # The first argument(s) are the CP codes
    cpcodes = []
    purge_methods = []

    # Separate CP codes from purge methods
    for arg in sys.argv[1:]:
        if arg in VALID_PURGE_TYPES:
            purge_methods.append(arg)
        else:
            cpcodes.append(arg)

    if not cpcodes:
        print("You must specify at least one CP code.")
        sys.exit(1)

    # Default to "delete" if no purge methods are specified
    if not purge_methods:
        purge_methods = [PURGE_TYPE_DELETE]

    # Validate purge methods
    invalid_methods = [method for method in purge_methods if method not in VALID_PURGE_TYPES]
    if invalid_methods:
        print(f"Invalid purge methods: {', '.join(invalid_methods)}. Choose from {VALID_PURGE_TYPES}.")
        sys.exit(1)

    network = "production"

    purge_content(network, cpcodes, purge_methods)
