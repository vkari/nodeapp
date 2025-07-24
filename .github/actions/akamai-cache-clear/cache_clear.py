#!/usr/bin/env python3
import os
import sys
import json
from akamai_purge import purge_content


def main():
    if len(sys.argv) < 2:
        print('Usage: cache_clear.py <environment>')
        sys.exit(1)

    env = sys.argv[1]
    cp_codes_str = os.environ.get('AKAMAI_CP_CODES', '').strip()

    if not cp_codes_str:
        print('AKAMAI_CP_CODES environment variable not set. No CP codes to purge.')
        return

    try:
        cp_codes = json.loads(cp_codes_str)
        if not isinstance(cp_codes, list):
            cp_codes = [str(cp_codes)]
    except json.JSONDecodeError:
        cp_codes = [c.strip() for c in cp_codes_str.split(',') if c.strip()]

    if not cp_codes:
        print('No CP codes provided.')
        return

    purge_content('production', cp_codes, ['delete'])


if __name__ == '__main__':
    main()
