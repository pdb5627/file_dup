#! /usr/bin/env python
'''find_B_not_in_A.py

This program looks at two databases of file information and generates
a list of files that are in one database but not the other.
'''

import file_dup
import sys
import argparse
import re
import datetime

#parser = argparse.ArgumentParser(usage=__doc__)
parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose',
    action='store_true',
    help='Print extra debugging output' )
parser.add_argument('-1', '--no_dupes',
    action='store_true',
    help='Eliminate duplicate files in returned list' )

example_date = datetime.datetime.now().strftime('%x %X')
parser.add_argument('--min_mtime',
    help='Return files with an mtime after a specified date. Example format: '+example_date )
parser.add_argument('--max_mtime',
    help='Return files with an mtime before a specified date. Example format: '+example_date )
parser.add_argument('--min_size',
    help='Return files with a size greater than a specified value. Provide value in bytes.' )
parser.add_argument('--max_size',
    help='Return files with a size less than a specified value. Provide value in bytes.' )
parser.add_argument('--regex',
    help='Return files with full path and filename matching the given regex' )

parser.add_argument('db_A',
                    help='Database A of file information')
parser.add_argument('db_B',
                    help='Database B of file information')
                    
def main(argv=None):
    if argv is None:
        argv = sys.argv

    args = parser.parse_args()
    
    if args.min_mtime is not None:
        try:
            min_mtime = datetime.datetime.strptime(args.min_mtime, '%x %X').timestamp() # Only works in Python 3.3+
        except ValueError as e:
            file_dup.logger.error('Value for min_mtime does not parse correctly.')
            file_dup.logger.error('Example of correct date and time format: '+example_date)
    else:
        min_mtime = None
        
    if args.max_mtime is not None:
        try:
            max_mtime = datetime.datetime.strptime(args.max_mtime, '%x %X').timestamp() # Only works in Python 3.3+
        except ValueError as e:
            file_dup.logger.error('Value for min_mtime does not parse correctly.')
            file_dup.logger.error('Example of correct date and time format: '+example_date)
    else:
        max_mtime = None
        
    min_size = None if args.min_size is None else int(args.min_size)
    max_size = None if args.max_size is None else int(args.max_size)
    
    filename_re = None if args.regex is None else re.compile(args.regex)

    A_and_B_dict, A_only_dict, B_only_dict = file_dup.file_list_split(args.db_A, args.db_B, no_dupes=args.no_dupes)
    for f in B_only_dict:
        if (min_mtime is None or f.mtime >= min_mtime) and \
                (max_mtime is None or f.mtime <= max_mtime) and \
                (min_size is None or f.size >= min_size) and \
                (max_size is None or f.size <= max_size) and \
                (filename_re is None or filename_re.match(f.filename)):
            print(f.filename)
    
if __name__ =='__main__':
    sys.exit(main())
