import xmltodict
import subprocess
import logging

log = logging.getLogger(__name__)


def run_drc(gds_file, cell, rules_file, results_file='/tmp/analog_sim/klayout_drc_results.xml', waivers=[]):
    """
        Run DRC in KLayout
    """

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
        if code in waivers:
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

    return not(len(errors['unwaived']) > 0)


def run_lvs(gds_file, cell, source_netlist, rules_file, 
            extracted_netlist='/tmp/analog_sim/klayout_lvs_netlist.spice', 
            lvs_database='/tmp/analog_sim/klayout_lvs_results.lvsdb',
            log_file='/tmp/analog_sim/klayout_lvs_log'):
    """
        Run LVS in KLayout
    """


    # klayout -b -r /home/tom/repositories/integratedspace/root/env/tech_xt018/lvs/xt018.lvs -rd source_netlist=/home/tom/.xschem/simulations/INVX2.spice -rd lvs_database=/tmp/analog_sim/lvs_database.lvsdb -rd extracted_netlist=/tmp/analog_sim/lvs_netlist.spice -rd input=/home/tom/repositories/integratedspace/root/env/tech_xt018/stdcell/layout/stdcell.gds -rd cellname=INVX2

    # run the simulation through command line
    bash_command  = "klayout -b "
    bash_command += "-r %s "                    % rules_file
    bash_command += "-rd source_netlist=%s "    % source_netlist
    bash_command += "-rd lvs_database=%s "      % lvs_database
    bash_command += "-rd extracted_netlist=%s " % extracted_netlist
    bash_command += "-rd log_file=%s "          % log_file
    bash_command += "-rd input=%s "             % gds_file
    bash_command += "-rd cellname=%s"           % cell

    # begin theL LVS run
    log.info('Beginning KLayout LVS run with settings: %s.' % bash_command)
    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    log.info('KLayout LVS run complete.')

    # read the results
    result = open(log_file,'r').read()
    if result.startswith("true"):
        return True
    else:
        return False
