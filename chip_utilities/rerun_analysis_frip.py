#!/usr/bin/env python

from __future__ import print_function
import dxpy
from pprint import pformat
import sys
import re
import traceback
import logging
from time import sleep

logging.basicConfig()
logger = logging.getLogger(__name__)

# E3_PROJECT_ID = 'project-BKp5K980bpZZ096Xp1XQ02fZ'
# FRIP_DEV_PROJECT_ID = 'project-F3BpKqj07z6y979Z4X36P6z9'
# FRIP_PROJECT_ID = 'project-F3Bvp4004vxZxbpZBBJGPyYy'
# TEST_ANALYSIS_ID = 'analysis-F2v67b80bpZV0p9q788kgBGp'
# TEST_ANALYSIS_ID = 'analysis-F3BZ8v8036977yg98x815zB3'\
ACCESSION_OUTPUT_FOLDER = "/accession_log/"

APPLETS_PROJECT_ID = next(dxpy.find_projects(
    name='ENCODE - ChIP Production',
    return_handler=True)).get_id()
APPLETS = {}

ASSAY_SPECIFICS = {
    'tf': {
        'pre_stage': 'SPP Peaks',
        'final_stage': 'Final IDR peak calls',
        'applet': 'encode_idr',
    },
    'histone': {
        'pre_stage': 'ENCODE Peaks',
        'final_stage': 'Final narrowpeaks',
        'applet': 'overlap_peaks',
    }
}

EPILOG = '''Notes:

Examples:

    %(prog)s
'''


def get_args():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__, epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    def t_or_f(arg):
        ua = str(arg).upper()
        if ua == 'TRUE'[:len(ua)]:
            return True
        elif ua == 'FALSE'[:len(ua)]:
            return False
        else:
            assert not (True or False), "Cannot parse %s to boolean" % (arg)

    parser.add_argument('analysis_ids', help='List of analysis IDs to rerun', nargs='*', default=None)
    parser.add_argument('--infile', help='File containing analysis IDs', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('--accession', help='Automatically accession the results to the ENCODE Portal', type=t_or_f, default=None)
    parser.add_argument('--debug', help="Print debug messages", type=t_or_f, default=None)
    parser.add_argument('--dryrun', help="Set up workflow but don't run.", type=t_or_f, default=None)
    parser.add_argument('-a', '--assay_type', choices=['tf', 'histone'], help='Assay type. Required.', required=True)

    return parser.parse_args()


def find_applet_by_name(applet_name, applets_project_id=APPLETS_PROJECT_ID):
    if (applet_name, applets_project_id) not in APPLETS:
        found = dxpy.find_one_data_object(
            classname="applet",
            name=applet_name,
            project=applets_project_id,
            zero_ok=False,
            more_ok=False,
            return_handler=True)
        APPLETS[(applet_name, applets_project_id)] = found
    return APPLETS[(applet_name, applets_project_id)]


def stage_named(name, analysis):
    try:
        stage = next(
            stage for stage in analysis.describe()['stages']
            if stage['execution']['name'] == name
        )
    except StopIteration:
        stage = None
    except:
        raise

    return stage


def get_assay_specific_variables(analysis, assay_type):
    '''
    Find final stage input and applet and update them with
    inputs from penulitmate stage.
    '''
    pre_stage_input = stage_named(
        ASSAY_SPECIFICS[assay_type]['pre_stage'], analysis
    )['execution']['input']
    final_stage = stage_named(
        ASSAY_SPECIFICS[assay_type]['final_stage'], analysis
    )
    new_input = final_stage['execution']['input']
    new_input.update(
        {
            name: input_file
            for name, input_file in pre_stage_input.items()
            if name in ['rep1_ta', 'rep1_xcor', 'rep2_ta', 'rep2_xcor']
        }
    )
    new_input.update(
        {
            'paired_end': pre_stage_input['rep1_paired_end']
        }
    )
    new_applet = find_applet_by_name(ASSAY_SPECIFICS[assay_type]['applet'])
    return final_stage, new_input, new_applet


def rerun_with_frip(analysis_id, dryrun, assay_type):
    logger.debug(
        'rerun_with_frip: analysis_id %s'
        % (analysis_id))
    analysis = dxpy.DXAnalysis(analysis_id)
    project_id = analysis.describe()['project']
    temp = dxpy.api.workflow_new({
        'name': analysis.describe()['executableName'],
        'project': project_id,
        'initializeFrom': {'id': analysis.get_id()},
        'temporary': True})
    new_workflow = dxpy.DXWorkflow(temp['id'])
    logger.debug(
        'rerun_with_frip: new_workflow %s %s'
        % (new_workflow.get_id(), new_workflow.name))
    final_stage, new_input, new_applet = get_assay_specific_variables(
        analysis,
        assay_type
    )
    accessioning_stage = stage_named('Accession results', analysis)
    if accessioning_stage:
        new_workflow.remove_stage(accessioning_stage['id'])
    logger.debug(
        'rerun_with_frip: new_applet %s %s'
        % (new_applet.get_id(), new_applet.name))
    logger.debug(
        'rerun_with_frip: new_input \n%s'
        % (pformat(new_input)))
    new_workflow.update_stage(
        final_stage['id'],
        executable=new_applet.get_id(),
        stage_input=new_input,
        force=True)

    m = re.match('ENCSR.{6}', analysis.name)
    accession = m.group(0)

    analysis_properties = analysis.describe()['properties']
    analysis_properties.update({
        'experiment_accession': accession,
        'original_analysis': analysis_id
    })
    if dryrun:
        logger.debug(
            'rerun_with_frip: workflow created but dryrun so no analysis run')
        return new_workflow
    else:
        logger.debug(
            'rerun_with_frip: running workflow')
        return new_workflow.run(
            {},
            project=project_id,
            name="%s frip" % (analysis.name),
            properties=analysis_properties)


def accession_analysis(analysis):
    accession_analysis_applet = find_applet_by_name('accession_analysis')
    logger.debug(
        'accession_analysis: found accession_analysis_applet %s'
        % (accession_analysis_applet.name))
    accession_output_folder = ACCESSION_OUTPUT_FOLDER
    accession_job_input = {
        'analysis_ids': [analysis.get_id()],
        'wait_on_files': [],
        'fqcheck': False,
        'force_patch': True,
        'encoded_check': False
    }
    sleep(5)
    max_retries = 10
    retries = max_retries
    accession_job = None
    while retries:
        logger.debug('accession_analysis: running accession_analysis_applet with input %s' % (accession_job_input))
        try:
            accession_job = accession_analysis_applet.run(
                accession_job_input,
                name='Accession %s' % (analysis.name),
                folder=accession_output_folder,
                depends_on=[analysis.get_id()],
                project=analysis.describe()['project']
            )
        except Exception as e:
            logger.error(
                "%s launching auto-accession ... %d retries left"
                % (e, retries))
            sleep(5)
            retries -= 1
            continue
        else:
            logger.debug(
                "Auto-accession will run as %s %s"
                % (accession_job.name, accession_job.get_id()))
            break
    else:
        logging.error("Auto-accession failed with %s" % (e))

    return accession_job


def main():

    args = get_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Logging level set to DEBUG")
    else:
        logger.setLevel(logging.INFO)

    if args.analysis_ids:
        ids = args.analysis_ids
    else:
        ids = args.infile

    first_row = True
    for string in ids:
        analysis_id = string.strip()
        if not analysis_id:
            continue

        try:
            new_analysis = rerun_with_frip(analysis_id, args.dryrun, args.assay_type)
        except:
            row = "%s\terror" % (analysis_id)
            print("%s\t%s" % (analysis_id, "error"), file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        else:
            if args.dryrun:
                # since it's only a temporary workflow, the project is just a termporary
                # container, which has only an ID and not a name
                project_name = new_analysis.describe().get('project')
            else:
                project = dxpy.DXProject(new_analysis.describe().get('project'))
                project_name = project.name
            row = "%s\t%s\t%s" % (
                analysis_id,
                new_analysis.get_id(),
                project_name
            )

            if args.accession:
                try:
                    accessioning_job = accession_analysis(new_analysis)
                except Exception as e:
                    logger.error("acccession_analysis failed with %s" % (e))
                    row += "\tfailed"
                else:
                    row += "\t%s" % (None if not accessioning_job else accessioning_job.get_id())
            else:
                row += " manually"

        if first_row:
            print("old_analysis\tnew_analysis\tproject\taccession_job")
        print(row)
        first_row = False


if __name__ == '__main__':
    main()
