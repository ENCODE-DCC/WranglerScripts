import requests
import json
import argparse
import os.path

HEADERS = {'content-type': 'application/json'}
DEBUG_ON = False
EPILOG = ''' Provide a list of experiments that need a
controlled_by for thier fastqs.  Assumptions are:
If the file has a value in controlled_by then leave it alone.

To use a different key from the default keypair file:

        %(prog)s --key submit
'''


def set_ENCODE_keys(keyfile, key):
        '''
          Set the global authentication keyds
        '''

        keysf = open(keyfile, 'r')
        keys_json_string = keysf.read()
        keysf.close()

        keys = json.loads(keys_json_string)
        key_dict = keys[key]

        global AUTHID
        global AUTHPW
        global SERVER

        AUTHID = key_dict['key']
        AUTHPW = key_dict['secret']
        SERVER = key_dict['server']
        if not SERVER.endswith("/"):
                SERVER += "/"
        return


def get_ENCODE(obj_id):
        '''GET an ENCODE object as JSON and return as dict
        '''
        # url = SERVER+obj_id+'?limit=all&datastore=database'
        url = SERVER+obj_id+'?frame=embedded'
        if DEBUG_ON:
                print "DEBUG: GET %s" % (url)
        response = requests.get(url, auth=(AUTHID, AUTHPW), headers=HEADERS)
        if DEBUG_ON:
                print "DEBUG: GET RESPONSE code %s" % (response.status_code)
                try:
                        if response.json():
                                print "DEBUG: GET RESPONSE JSON"
                                print json.dumps(
                                    response.json(),
                                    indent=4,
                                    separators=(',', ': ')
                                    )
                except:
                        print "DEBUG: GET RESPONSE text %s" % (response.text)
        if not response.status_code == requests.codes.ok:
                return ''
                response.raise_for_status()
        return response.json()


def get_experiment_list(file, search):

        objList = []
        if search == "NULL":
            f = open(file)
            objList = f.readlines()
            for i in range(0, len(objList)):
                objList[i] = objList[i].strip()
        else:
            set = get_ENCODE(search+'&limit=all&frame=embedded')
            for i in range(0, len(set['@graph'])):
                objList.append(set['@graph'][i]['accession'])
                # objList.append(set['@graph'][i]['uuid'])

        return objList


def get_fastq_dictionary(exp):

    controlfiles = {}
    control = get_ENCODE(exp)
    for ff in control['files']:
        if ff.get('file_format') != 'fastq':
            continue
        biorep = str(ff['replicate']['biological_replicate_number'])
        techrep = str(ff['replicate']['technical_replicate_number'])
        pair = str(ff.get('paired_end'))
        rep = biorep + '-' + techrep
        key = rep + '-' + pair
        biokey = biorep + '-' + pair

        if key in controlfiles:
            print "error: replicate-pair has multiple files"
            controlfiles[key].append(ff['accession'])
            controlfiles[key].append('multiple-files-error')
            # need to find a way to get pairs
        else:
            controlfiles[key] = [ff['accession']]

         #There is a logic error here
        if biokey in controlfiles:
            if ff['accession'] not in controlfiles[biokey]:
                print 'error: control has technical reps'
                controlfiles[biorep] = ['error']
        else:
            controlfiles[biokey] = [ff['accession']]
    return controlfiles


def main():

    parser = argparse.ArgumentParser(
        description=__doc__, epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        )

    parser.add_argument(
        '--infile', '-i',
        default='infile',
        help="File containing a list of ENCSRs.")
    parser.add_argument(
        '--search',
        default='NULL',
        help="The search parameters.")
    parser.add_argument(
        '--key',
        default='default',
        help="The keypair identifier from the keyfile.")
    parser.add_argument(
        '--keyfile',
        default=os.path.expanduser("~/keypairs.json"),
        help="The keypair file.  Default is --keyfile=%s" % (os.path.expanduser("~/keypairs.json")))
    parser.add_argument(
        '--debug',
        default=False,
        action='store_true',
        help="Print debug messages.  Default is False.")
    args = parser.parse_args()

    DEBUG_ON = args.debug

    set_ENCODE_keys(args.keyfile, args.key)

    objList = get_experiment_list(args.infile, args.search)

    for item in objList:
        print "Experiment:" + item
        obj = get_ENCODE(item)
        controlfiles = {}
        if len(obj['possible_controls']) == 1:
            # Only one possible control to deal with
            controlId = obj['possible_controls'][0]['accession']
            controlfiles = get_fastq_dictionary(controlId)
            print controlfiles

            for ff in obj['files']:
                if ff.get('file_format') == 'fastq' and (ff.get('controlled_by') == [] or ff.get('controlled_by') is None):
                    biorep = str(ff['replicate']['biological_replicate_number'])
                    techrep = str(ff['replicate']['technical_replicate_number'])
                    pair = str(ff.get('paired_end'))
                    rep = biorep + '-' + techrep + '-' + pair

                    if rep in controlfiles:
                        answer = controlfiles[rep]
                    elif biorep in controlfiles:
                        answer = controlfiles[biorep]
                    else:
                        answer = 'error: control had no corresponding replicate'

                    print item, controlId, rep, ff['accession'], answer
            print ''
        elif len(obj['possible_controls']) == 2:
            print 'boo'



if __name__ == '__main__':
    main()
