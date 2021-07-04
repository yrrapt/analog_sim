import os, re, subprocess
import numpy as np
from spyci import spyci
from PySpice.Spice.NgSpice.Shared import NgSpiceShared

from yaaade.spice.generic import GenericSpiceInterface


class NgSpiceInterface(GenericSpiceInterface):
    '''

    '''

    def __init__(self, verbose=True, netlist_path=None, pdk_path=None):
        '''
            Instantiate the object
        '''

        super().__init__(verbose, netlist_path, pdk_path)
    
        self.config['simulator'] = {'executable'    :   'ngspice',
                                    'shared'        :   True,
                                    'silent'        :   False}
        self.config['verbose'] = verbose

        # create an ngspice shared object
        self.ngspice = NgSpiceShared.new_instance()


    def set_parameters(self, parameters):
        '''
            Set parameters inside the netlist

            Parameters should be passed as an array with with sub-arrays with
            the first element parameter string and the second element a value.

            ie. [['vds', 1.8], ['vbs', 0.2], ['ids', 1e-6]]
        '''

        # keep a list of the of parameter values to print to terminal
        log_information = "New netlist parameter values: "

        # different methods of changing parameters
        if self.config['simulator']['shared']:

            # loop through each parameter updating the value
            for parameter in parameters:

                if parameter[1] < 1e-6:
                    self.ngspice.exec_command("alterparam %s=%0.20f" % (parameter[0], parameter[1]))
                    log_information += '%s=%0.20f  ' % (parameter[0], parameter[1])
                else:
                    self.ngspice.exec_command("alterparam %s=%f" % (parameter[0], parameter[1]))
                    log_information += '%s=%f  ' % (parameter[0], parameter[1])

        # loop through each parameter updating the value
        for parameter in parameters:

            if parameter[1] < 1e-6:
                sub_string = ".param %s=%0.20f" % (parameter[0], parameter[1])
                log_information += '%s=%0.20f  ' % (parameter[0], parameter[1])
            else:
                sub_string = ".param %s=%f" % (parameter[0], parameter[1])
                log_information += '%s=%f  ' % (parameter[0], parameter[1])
            self.simulation['netlist'] = re.sub(r'\.param %s=.*' % parameter[0], sub_string, self.simulation['netlist'])

        # update user
        if self.config['verbose']:
            print(log_information)


    def set_temperature(self, temp):
        '''
            Set the simulation temperature
        '''

        if self.config['simulator']['shared']:
            print("alterparam temp=%f" % temp)
            self.ngspice.exec_command("alterparam temp=%f" % temp)

        else:

            # change the temperature in the netlist
            sub_string = ".param temp=%f" % temp
            self.simulation['netlist'] = re.sub(r'\.param temp=.*', sub_string, self.simulation['netlist'])
            sub_string = ".temp %f" % temp
            self.simulation['netlist'] = re.sub(r'\.temp .*', sub_string, self.simulation['netlist'])

        # update user
        if self.config['verbose']:
            log_information = "New temperature: %f" % temp
            print(log_information)


    def run_simulation(self, new_instance=True, outputs=None):
        '''
            Run simulation
        '''

        # write the temporary netlist
        with open('rundir/spiceinterface_temp.spice', 'w') as f:
            f.write(self.simulation['netlist'])

        # run ngspice
        if self.config['simulator']['shared']:

            # destroy previous run data
            self.ngspice.destroy()
            self.ngspice.exec_command("reset")

            # load the netlist into the 
            if new_instance:
                self.ngspice.source('rundir/spiceinterface_temp.spice')

            # run the simulation
            if self.config['simulator']['silent']:
                with suppress_stdout_stderr():
                    self.ngspice.run()
            else:
                self.ngspice.run()

            # save the outputs
            self.ngspice.exec_command("set filetype=ascii")
            self.ngspice.exec_command("write rundir/spiceinterface_temp.raw")


        else:

            # set the output format to ascii required by spyci
            os.environ["SPICE_ASCIIRAWFILE"] = "1"

            # run the simulation through command line
            bash_command = "ngspice -b -r rundir/spiceinterface_temp.raw -o rundir/spiceinterface_temp.out rundir/spiceinterface_temp.spice"
            process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
            output, error = process.communicate()

            # check if error occured
            with open('rundir/spiceinterface_temp.out') as f:
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
                self.simulation_data[output] = spyci.load_raw("rundir/spiceinterface_temp_"+output+".raw")
        else:
            self.simulation_data = spyci.load_raw("rundir/spiceinterface_temp.raw")


    def set_parameters(self, parameters):
        '''
            Set parameters inside the netlist

            Parameters should be passed as an array with with sub-arrays with
            the first element parameter string and the second element a value.

            ie. [['vds', 1.8], ['vbs', 0.2], ['ids', 1e-6]]
        '''

        # keep a list of the of parameter values to print to terminal
        log_information = "New netlist parameter values: "


        # loop through each parameter updating the value
        for parameter in parameters:

            if parameter[1] < 1e-6:
                sub_string = ".param %s=%0.20f" % (parameter[0], parameter[1])
                log_information += '%s=%0.20f  ' % (parameter[0], parameter[1])
            else:
                sub_string = ".param %s=%f" % (parameter[0], parameter[1])
                log_information += '%s=%f  ' % (parameter[0], parameter[1])
            self.simulation['netlist'] = re.sub(r'\.param %s=.*' % parameter[0], sub_string, self.simulation['netlist'])

        # update user
        if self.config['verbose']:
            print(log_information)


    def get_signal(self, signal_name, factor=1.0, dataset=None, complex_out=False):
        '''
            Return a signal from the simulation results
        '''

        # grab the simulation dataset requested
        if dataset:
            simulation_data = self.simulation_data[dataset]
        else:
            simulation_data = self.simulation_data

        # find where the node is in the data
        index = None
        for data_i, data_var in enumerate(simulation_data['vars']):

            if data_var['name'] == signal_name.lower():
                index = data_i

        assert index != None, 'The provided signal (%s) cannot be found in the simulation results' % signal_name

        # extract each data point and convert to real list
        data = []
        for n in range(len(simulation_data['values'])):

            if complex_out:
                data.append(factor*simulation_data['values'][n][index])
            else:
                data.append(factor*np.real(simulation_data['values'][n][index]))

        return data


    def set_sim_dc(self, variable, start, stop, increment):
        '''
            Define a DC sweep simulation
        '''

        sim_command = '.dc %s %d %d %d' % (variable, start, stop, increment)
        self.set_sim_command(sim_command)


    def set_sim_tran(self, stop, step, start_save=None):
        '''
            Define a DC sweep simulation
        '''

        # .tran 0.001n 50n 20n
        sim_command = '.tran %fn %fn' % (step*1e9, stop*1e9)

        if start_save != None:
            sim_command += ' %fn' % (start_save*1e9)

        self.set_sim_command(sim_command)


    # def insert_op_save(self, devices, expressions):
    #     '''
    #         In NGSpice a control block can be used to insert OP
    #         save instructions for all devices
    #     '''

    #     # save operating points for all FETs
    #     command  = '.control\n'
    #     command += 'unset noglob\n'
    #     command += 'save @M.*[*]\n'
    #     command += 'set noglob\n'
    #     command += '.endc\n'

    #     # add to netlist
    #     self.simulation['netlist'] = re.sub(r'\.end[$\n]', command + "\n.end", self.simulation['netlist'])
