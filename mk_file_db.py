'''mk_file_db.py

This program creates the database of file information needed for file duplicate
detection or directory tree differences.
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
                    help='Database in which to store file information')
parser.add_argument('dir',
                    nargs='+',
                    help='Directory root to scan for files')


def main(argv=None):
    if argv is None:
        argv = sys.argv

    args = parser.parse_args()

    print(args.dir)
    for d in args.dir:
        file_dup.mk_file_db(d, args.db)
    
if __name__ =='__main__':
    sys.exit(main())