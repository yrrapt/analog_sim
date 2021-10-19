import os, re, subprocess
import numpy as np
from spyci import spyci
from PySpice.Spice.NgSpice.Shared import NgSpiceShared

from analog_sim.spice.generic import GenericSpiceInterface


class NgSpiceInterface(GenericSpiceInterface):
    '''

    '''

    def __init__(self, verbose=True, netlist_path=None, pdk_path=None):
        '''
            Instantiate the object
        '''

        self.config = {}
        self.config['simulator'] = {'executable'    :   'ngspice',
                                    # 'shared'        :   True,
                                    'shared'        :   False,
                                    'silent'        :   False}
        self.config['verbose'] = verbose

        # create an ngspice shared object
        self.ngspice = NgSpiceShared.new_instance()


    def run_simulation(self, new_instance=True, outputs=None):
        '''
            Run simulation
        '''

        # pre-create the file locations    
        netlist_path = self.run_dir + '/' + self.temp_netlist
        raw_path = self.run_dir + '/' + self.temp_result
        log_path = self.run_dir + '/' + self.temp_log

        # run ngspice
        if self.config['simulator']['shared']:

            # destroy previous run data
            self.ngspice.destroy()
            # self.ngspice.exec_command("reset")
            # self.ngspice.reset()

            # load the netlist into the 
            if new_instance:
                self.ngspice.source(netlist_path)

            # run the simulation
            if self.config['simulator']['silent']:
                with suppress_stdout_stderr():
                    self.ngspice.run()
            else:
                self.ngspice.run()

            # save the outputs
            self.ngspice.exec_command("set filetype=ascii")
            
            self.ngspice.exec_command("write %s" % raw_path)


        else:

            # set the output format to ascii required by spyci
            os.environ["SPICE_ASCIIRAWFILE"] = "1"
            self.result_type = 'ascii'

            # run the simulation through command line
            bash_command = "ngspice -b -r %s -o %s %s" % (raw_path, log_path, netlist_path)

            process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
            output, error = process.communicate()

            # check if error occured
            with open(log_path) as f:
                sim_log = f.read()
                if 'fatal' in sim_log or 'aborted' in sim_log:
                    print('\033[91m')
                    print('-'*150)
                    print('ERROR IN SIMULATION:')
                    print(sim_log)
                    print('-'*150)
                    print('\033[0m')

            # read in the results of the simulation
            if outputs:
                self.simulation_data = {}
                for output in outputs:
                    self.read_results("rundir/spiceinterface_temp_"+output+".raw", output)
            else:
                self.read_results(raw_path)
    

    def netlist_voltage_pwl(self, name, voltage, negative='0', dc=0):
        '''
            Write a netlist line for a DC PWL source
        '''

        return 'V' + name + ' ' + name + ' ' + negative + ' dc %f ' % dc + 'pwl ( ' + voltage + ' )'


    def netlist_temperature(self, temperature):
        '''
            Set the temperature
        '''

        # form the include line
        line  = '.option TEMP=%s' % temperature
        return line


    def netlist_control_block(self, control_block):
        '''
            Set a control block
        '''

        # form the include line
        line  =  '.control\n'
        line += control_block + '\n'
        line += '.endc'
        return line


    def netlist_sim_tran(self, final_time, initial_step=-1, use_intitial_conditions=False):
        '''
            Define a transient simulation

            TRAN <initial step value> <final time value>
        '''

        # if the rise and fall is not set then default to 1/50 of the period
        if initial_step < 0:
            initial_step = final_time/1000

        # form the transient instruction
        line = '.tran %s %s' % (self.unit_format(initial_step), self.unit_format(final_time))

        if use_intitial_conditions:
            line += ' uic'

        return line