#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''Read in a file of object, correction fields and patch each object'''

import argparse
import os.path
import encodedcc


HEADERS = {'content-type': 'application/json'}
DEBUG_ON = False
EPILOG = '''Examples:

To get one ENCODE object from the server/keypair called "default" in the default keypair file and print the JSON:

        %(prog)s --id ENCBS000AAA

To use a different key from the default keypair file:

        %(prog)s --id ENCBS000AAA --key submit

For more details:

        %(prog)s --help
'''

# I need my attachment thing here


def main():

    parser = argparse.ArgumentParser(
        description=__doc__, epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument('--infile',
                        help="A two column list with identifier and value to patch (or remove)")
    parser.add_argument('--field',
                        help="The field to patch.")
    parser.add_argument('--key',
                        default='default',
                        help="The keypair identifier from the keyfile.  Default is --key=default")
    parser.add_argument('--keyfile',
                        default=os.path.expanduser("~/keypairs.json"),
                        help="The keypair file.  Default is --keyfile=%s" % (os.path.expanduser("~/keypairs.json")))
    parser.add_argument('--debug',
                        default=False,
                        action='store_true',
                        help="Print debug messages.  Default is False.")
    parser.add_argument('--array',
                        default=False,
                        action='store_true',
                        help="Field is an array.  Default is False.")
    parser.add_argument('--remove',
                        default=False,
                        action='store_true',
                        help="Patch to remove the value specified in the input file from the given field.  Default is False.")
    parser.add_argument('--dryrun',
                        default=False,
                        action='store_true',
                        help="Dry run of the script, no data will actually be patched.")
    args = parser.parse_args()

    DEBUG_ON = args.debug
    print(DEBUG_ON)

    key = encodedcc.ENC_Key(args.keyfile, args.key)

    connection = encodedcc.ENC_Connection(key)

    FIELD = args.field

    objDict = {}
    with open(args.infile) as fd:
        objDict = dict(line.strip().split(None, 1) for line in fd)

    for key in objDict:

        '''Interpret the new value'''
        if objDict[key].strip() == 'NULL':
            objDict[key] = None
        elif objDict[key].strip() == 'False':
            objDict[key] = False
        elif objDict[key].strip() == 'True':
            objDict[key] = True
        elif objDict[key].isdigit():
            objDict[key] = int(objDict[key])

        object = encodedcc.get_ENCODE(key, connection)
        old_thing = object.get(FIELD)

        if args.array:
            if objDict[key] is None:
                patch_thing = []
            elif old_thing is None:
                patch_thing = []
                patch_thing.append(objDict[key])
            else:
                patch_thing = list(old_thing)
                patch_thing.append(objDict[key])
                temp = list(set(patch_thing))
                patch_thing = temp

            if args.remove:
                items = objDict[key].split(', ')
                print("Removing %s from %s" % (objDict[key], key))
                patch_thing = list(old_thing)
                for i in range(len(items)):
                    patch_thing.remove(items[i])
                temp = list(set(patch_thing))
                patch_thing = temp
        else:
            if args.remove:
                patch_thing = None
            else:
                patch_thing = objDict[key]

        '''construct a dictionary with the key and value to be changed'''
        patchdict = {FIELD: patch_thing}

        if not args.dryrun:
            response = encodedcc.patch_ENCODE(key, connection, patchdict)
        else:
            print("In DRY RUN mode, no data will be patched...")

        '''print what we did'''
        print("Original:  %s" % (old_thing))
        print("PATCH:     %s" % (patch_thing))

if __name__ == '__main__':
        main()
