#!/usr/bin/env python3
import os
import sys
from akamai_purge import purge_content


def main():
    if len(sys.argv) < 2:
        print('Usage: cache_clear.py <environment>')
        sys.exit(1)

    env = sys.argv[1]
    cp_code = os.environ.get('AEM_ENV', '').strip()

    if not cp_code:
        print('AEM_ENV environment variable not set. No CP code to purge.')
        return

    purge_content('production', [cp_code], ['delete'])


if __name__ == '__main__':
    main()
