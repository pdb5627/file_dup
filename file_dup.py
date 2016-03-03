#! /usr/bin/python3

''' file_dup.py

Library for detecting duplicate files in one or more file directory trees.

The basic approach is to store file information about a directory tree
in a SQLite database. The database can then be queried to look for duplicates
within a directory tree or get the intersection or difference between
two directory trees.

'''

from __future__ import print_function, unicode_literals, division
import sys
import os
import collections
import datetime
import time
import sqlite3
import binascii

import hashlib
hash_func = hashlib.md5
BLOCKSIZE = 65536

def hash_file(f):
    hasher = hash_func()
    with open(f, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.digest()
    
def hash2int(digest):
    logger.info('# bytes: %d' % len(digest))
    return int.from_bytes(digest, byteorder='big', signed=True) # from_bytes only in Python 3.2+
    
def int2hash(i):
    return int.to_bytes(i, byteorder='big', signed=True) # from_bytes only in Python 3.2+

# Set up a logger so any errors can go to file since there's no screen to print to.
import logging
from logging.config import dictConfig

logging_config = {
    'version': 1,
    'formatters': {
        'f': {'format':
              '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'},
        's': {'format':
              '%(message)s'}
        },
        
    'handlers': {
        'h': {'class': 'logging.StreamHandler',
            'formatter': 's',
            'level': 'INFO'}
        },
    'loggers': {
        'file_dup' : {'handlers': ['h'],
            'level': 'INFO'}
        }
}

dictConfig(logging_config)

# logger should be set by the application using the library
# https://docs.python.org/3/howto/logging.html#library-config
# I'm not doing this. Not sure how it would be done, and I want the complexity
# of setting up the logger in this module, not in the files that use it.
logger = logging.getLogger('file_dup')

FileInfo = collections.namedtuple('FileInfo',
                                  ['filename', 'mtime', 'size', 'hash'])

def mk_file_db(dirs, db):
    ''' Scan directory tree(s) and save file information to an sqlite database.
        The directory is passed as a string or a list of directories.
        The sqlite database is passed as a string filename to save to.
    '''
    # Clear database first by saving empty list
    save_to_db([], db, add=False)
    
    for dir in ([dirs] if isinstance(dirs, str) else dirs):
        logger.info('Directory: %s' % dir)
        logger.info('Database: %s' % db)
        file_list = get_file_list(dir)
        save_to_db(file_list, db, add=True)
    return
    
def get_file_list(dir):
    ''' Scan directory tree and generate a list of files. File information
        is saved in objects of class FileInfo.
    '''
    rtn_list = []
    # First get number of files so we can indicate progress
    num_files = sum( (len(file_list) for _, _, file_list in os.walk(dir)) )
    logger.info('Scanning directory %s' % dir)
    logger.info('Files to scan: %d' % num_files)
    n = 0
    for dir_name, subdir_list, file_list in os.walk(dir):
        for fname in file_list:
            abs_fname = os.path.abspath(os.path.join(dir_name, fname))
            fstat = os.stat(abs_fname)
            fhash = hash_file(abs_fname)
            
            #logger.info('filename: %s, mtime: %d, size: %d, hash: %s' % \
            #    (abs_fname, fstat.st_mtime, fstat.st_size, binascii.hexlify(fhash)))
            
            f = FileInfo(filename = abs_fname,
                         mtime = fstat.st_mtime,
                         size = fstat.st_size,
                         hash = fhash)
            rtn_list.append(f)
            n += 1
            # Print only every 100 files.
            if n%100 == 0:
                logger.info('Scan progress: %d / %d (%.1f%%)' % (n, num_files, n/num_files*100.))
    logger.info('Scanning complete.')
    return rtn_list
                         
def save_to_db(file_list, db, add=False):
    con = None

    try:
        con = sqlite3.connect(db)
        con.text_factory = str
        cur = con.cursor()    
        
        # Create tables as needed
        if not add:
            cur.execute("DROP TABLE IF EXISTS Files") # Clear db table
        cur.execute("CREATE TABLE IF NOT EXISTS Files(id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, mtime INTEGER, size INTEGER, hash BLOB)")
        
        for f in file_list:
            # Insert file info
            cur.execute("INSERT INTO Files (filename,mtime,size,hash) VALUES (?,?,?,?)", (f.filename, f.mtime, f.size, f.hash))

        # Save to disk
        logger.info("Saving data to database")
        con.commit()

    except sqlite3.Error as e:
        logger.error("SQLite Error: %s" % e.args[0])
        
    finally:
        
        if con:
            con.commit()
            con.close()

def get_from_db(db):
    '''Get list of FileInfo objects from database db'''

    con = None

    try:
        con = sqlite3.connect(db)
        con.text_factory = str
        cur = con.cursor()    

        # Retrieve file info
        rtn = [ FileInfo(*r) for r in cur.execute("SELECT filename,mtime,size,hash FROM Files") ]
        logger.info('file list length from db: %d' % len(rtn))
        return rtn

    except sqlite3.Error as e:
        logger.error("SQLite Error: %s" % e.args[0])
        
    finally:            
        if con:
            con.close()

def fkey(f):
    return (f.size, str(f.hash))

def file_list_to_hash_dict(file_list):
    file_dict = {}
    for f in file_list:
        try:
            file_dict[fkey(f)].append(f)
        except KeyError:
            file_dict[fkey(f)] = [f]
    return file_dict
    
def file_list_to_hash_set(file_list):
    return set( (fkey(f) for f in file_list) )

def find_dupes(db_list):
    '''Identify duplicate files in database(s)'''
    file_list = []
    for db in ([db_list] if isinstance(db_list, str) else db_list):
        file_list.extend(get_from_db(db))
    file_dict = file_list_to_hash_dict(file_list)
    dup_list = filter(lambda l: len(l) > 1, file_dict.values())
    return list(dup_list)

def file_list_split(db_A, db_B, no_dupes=False):
    ''' Given two databases of files "A" and "B", returns three lists that
        divide the sets of files into those that are in both databases, 
        those that are only in database "A" and those that are only in
        database "B".

        If no_dupes is set to true, then only one filename per unique
        hash is returned, otherwise all copies of the identical files
        are returned.
   '''

    file_dict_A = file_list_to_hash_dict(get_from_db(db_A))
    file_dict_B = file_list_to_hash_dict(get_from_db(db_B))
    file_set_A = set(file_dict_A)
    file_set_B = set(file_dict_B)
    
    A_and_B = file_set_A & file_set_B
    A_only = file_set_A - A_and_B
    B_only = file_set_B - A_and_B
    
    A_and_B_list = sum( (([file_dict_A[k][0]] if no_dupes else file_dict_A[k]) for k in A_and_B), [] )
    A_only_list = sum( (([file_dict_A[k][0]] if no_dupes else file_dict_A[k]) for k in A_only), [] )
    B_only_list = sum( (([file_dict_B[k][0]] if no_dupes else file_dict_B[k]) for k in B_only), [] )
    return (A_and_B_list, A_only_list, B_only_list)
    
    
