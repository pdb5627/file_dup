'''find_B_not_in_A.py

This program looks at two databases of file information and generates
a list of files that are in one database but not the other.
'''

import file_dup
import sys
import argparse

#parser = argparse.ArgumentParser(usage=__doc__)
parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose',
    action='store_true',
    help='Print extra debugging output,' )
parser.add_argument('db_A',
                    help='Database A of file information')
parser.add_argument('db_B',
                    help='Database B of file information')
                    
def main(argv=None):
    if argv is None:
        argv = sys.argv

    args = parser.parse_args()

    A_and_B_dict, A_only_dict, B_only_dict = file_dup.file_list_split(args.db_A, args.db_B)
    for f in B_only_dict:
        print(f.filename)
    
if __name__ =='__main__':
    sys.exit(main())