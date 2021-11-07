import xmltodict
import subprocess
import logging

log = logging.getLogger(__name__)

def run_drc():
    """
        Run DRC in KLayout
    """

    # TODO - hardcode for now
    gds_file     = "/home/tom/repositories/integratedspace/root/env/tech_xt018/stdcell/layout/stdcell.gds"
    cell         = "INVX2"
    rules_file   = "/home/tom/repositories/integratedspace/root/env/tech_xt018/drc/xt018.drc"
    results_file = "/home/tom/repositories/integratedspace/root/env/analog_sim/_devel/results_drc.txt"
    waiver_list = ['B1DT']

    # run the simulation through command line
    bash_command = "klayout -b -r %s -rd input=%s -rd cellname=%s -rd report=%s " % (rules_file, gds_file, cell, results_file)
    log.info('Beginning KLayout DRC run with settings: %s.' % bash_command)
    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    log.info('KLayout DRC run complete.')

    # read the results
    results = xmltodict.parse(open(results_file,'r').read())

    # sort the results
    errors = {  'unwaived'  : [],
                'waived'    : []}
    for error in results['report-database']['items']:

        # pull out the DRC error code
        code = results['report-database']['items'][error]['category'].split(' ')[0].replace("'", "")

        # sort into waived and unwaived errors
        if code in waiver_list:
            errors['waived'].append(results['report-database']['items'][error])
        else:
            errors['unwaived'].append(results['report-database']['items'][error])


    # print out the errors
    if len(errors['unwaived']) > 0:
        log.warning('DRC Errors Found!:')

        for error in errors['unwaived']:
            log.warning('\t%sx - %s' % (error['multiplicity'], error['category']))
    
    else:
        log.info('No DRC Errors Found.')