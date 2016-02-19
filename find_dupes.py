#! /usr/bin/env python
'''find_dups.py

This program looks at one or more databases of file information and generates
a list of duplicated files as identified by the stored hash and size.
'''

import file_dup
import sys
import argparse

#parser = argparse.ArgumentParser(usage=__doc__)
parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose',
    action='store_true',
    help='Print extra debugging output,' )
parser.add_argument('db',
                    nargs='+',
                    help='Database(s) in which file information is stored')

def main(argv=None):
    if argv is None:
        argv = sys.argv

    args = parser.parse_args()

    print(args.db)
    for group in file_dup.find_dupes(args.db):
        print('# ' + '-'*78)
        for f in group:
            print(f.filename)
    
if __name__ =='__main__':
    sys.exit(main())
