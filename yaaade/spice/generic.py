import numpy as np
import os, sys
import contextlib
import io
import re
import h5py
import subprocess
from spyci import spyci
from PySpice.Spice.NgSpice.Shared import NgSpiceShared

import matplotlib.pyplot as plt
import matplotlib.ticker
import matplotlib
from matplotlib.ticker import FuncFormatter


class GenericSpiceInterface():
    '''
        A library to interface to Spice simulators (NGSpice, Xyce, Spectre, TSpice etc...)

        Contains high level constructs to manipulate and run simulations without relying
        on simulator specfic netlist constructions.

        Will be developed into a library to allow for high programmatic control of electronic
        circuit simulation, design and verification. 
    '''

    def __init__(self, verbose=True, netlist_path=None, pdk_path=None):
        '''
            Instantiate the object
        '''

        # if pdk_path is None:
        #     self.pdk_path = os.environ.get('SKY130LIB', 'sky130_fd_pr')
        # else:
        #     self.pdk_path = pdk_path

        # store the setup information internally
        self.simulation = {}
        self.config = {}
        self.config['simulator'] = {'executable'    :   'ngspice',
                                    'shared'        :   True,
                                    'silent'        :   False}
        self.config['verbose'] = verbose

        # create an ngspice shared object
        self.ngspice = NgSpiceShared.new_instance()

        # if provided read in the base netlist
        if netlist_path:
            self.read_netlist_file(netlist_path)

        self.plot_init=False

        # define some limits
        self.limits = { 'phase_margin'  :   45,
                        'gain_margin'   :   10}


    def read_netlist_file(self, netlist_path):
        '''
            Read in a netlist from file
        '''

        with open(netlist_path) as f:
            self.simulation['netlist'] = f.read()

            # the line continuation is not needed as messes up parsing, remove it
            self.simulation['netlist'] = re.sub(r'\n\+', '', self.simulation['netlist'])



    def set_sim_command(self, command):
        '''
            Add a simulation command to the netlist
        '''

        # wrap the command in new lines
        command = "\n" + command + "\n"

        # remove the .end keyword and append
        self.simulation['netlist'] = re.sub(r'\.end\n', command + "\n.end", self.simulation['netlist'])



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
            print(temp)
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



    def set_corner(self, corner):
        '''
            Set the simulation corner
        '''

        # change the temperature in the netlist
        sub_string = r"\1sky130.lib.spice %s" % corner
        self.simulation['netlist'] = re.sub(r'(\.lib .*)sky130.lib.spice .*', sub_string, self.simulation['netlist'])

        # update user
        if self.config['verbose']:
            log_information = "New corner: %s" % corner
            print(log_information)



    def find_device_type(self, device):
        '''
            Traverse the netlist heirarchy to find the device type for a given reference designator
        '''

         # delete all subcircuits
            # \n\.subckt[\s\S]*?\.ends
        temp_netlist = re.sub(r'\n\.subckt[\s\S]*?\.ends', '', self.simulation['netlist'])

        # split the heirarchy
        heirarchy = device.split('.')

        # device is in subcircuit
        if len(heirarchy) > 1:

            # descend the heirarchy
            for component in heirarchy[:-1]:

                # find the subcircuit name for the instance
                search_str = component + ' .*(?<!=) (\w+)(?!=)'
                regex = re.search(search_str, temp_netlist)
                subcircuit_name = regex.group(1)

                # delete everything apart from the current subcircuit+
                search_str = r'\n\.subckt '+subcircuit_name+r' [\s\S]+?\.ends'
                regex = re.search(search_str, self.simulation['netlist'])
                temp_netlist = regex.group(0)


        # find the device type
        search_str = heirarchy[-1] + r'.*(sky130\S*)'
        regex = re.search(search_str, temp_netlist)
        device_type = regex.group(1)

        return device_type


    def find_mosfets_in_subcircuit(self, devices, search_subcircuit=None, refdes_list=None):
        '''
            Traverse the netlist heirarchy to find all MOSFETs
        '''

        try:

            # look in a subcircuit
            if search_subcircuit:

                # delete everything apart from the current subcircuit+
                search_str = r'\n\.subckt ' + search_subcircuit + r' [\s\S]+?\.ends'
                regex = re.search(search_str, self.simulation['netlist'])
                temp_netlist = regex.group(0)

            # look at the top level
            else:

                # delete all subcircuits
                temp_netlist = re.sub(r'\n\.subckt[\s\S]*?\.ends', '', self.simulation['netlist'])
                refdes_list = []


            # find all subcircuits at this level
            search_str = r'\n([x|X].*)'
            subcircuits = re.findall(search_str, temp_netlist)

            # find subcircuits and pull out sky130 devices on this level
            for subcircuit in subcircuits[::-1]:
                if 'sky130_fd_pr_' in subcircuit:

                    subcircuit_prefix = ''
                    for level in refdes_list:
                        subcircuit_prefix += level + '.'

                    subcircuit_name = subcircuit_prefix + subcircuit.split(' ')[0]

                    devices.append(subcircuit_name)
                    subcircuits.remove(subcircuit)

            # find the name of further subcircuits
            subcircuits_names = []
            for subcircuit in subcircuits:

                temp = subcircuit.split(' ')

                for item in temp[::-1]:
                    if not '=' in item:
                        subcircuits_names.append([item, temp[0]])
                        break

            # recursively look into each circuit
            for subcircuit_name in subcircuits_names:

                if not 'sky130_fd_sc' in subcircuit_name[0]:

                    # append the reference designator list and search the next level down
                    current_refdes_list = refdes_list + [subcircuit_name[1]]
                    self.find_mosfets_in_subcircuit(devices, search_subcircuit=subcircuit_name[0], refdes_list=current_refdes_list)

        except:

            print("find_mosfets_in_subcircuit() - Failed to find MOSFETs in this level of heirarchy, you may want to look into it")
            print("  Provided with deviced: ", devices)



    def find_all_mosfets(self):
        '''
            Traverse the netlist heirarchy to find all MOSFETs
        '''

        devices = []

        self.find_mosfets_in_subcircuit(devices)

        return devices



    def insert_op_save(self, devices, expressions):
        '''
            Insert save commands for devices
        '''

        # wrap the command in new lines
        command = "\n\n.save all "

        # loop through devices and parameters
        for device in devices:
            for expression in expressions:

                # get the device type 
                device_type = self.find_device_type(device)

                # vsat_marg is not in devices so need to form that ourselves
                if expression == "vsat_marg":
                    command += '@M.' + device + '.m' + device_type + '[vds] '
                    command += '@M.' + device + '.m' + device_type + '[vdsat] '
                else:
                    command += '@M.' + device + '.m' + device_type + '[' + expression + '] '

        # remove the .end keyword and append
        self.simulation['netlist'] = re.sub(r'\.end$', command + "\n.end", self.simulation['netlist'])


    def plot_op_save(self, devices, expressions, sweepvar, linewidth=1.0, alpha=1.0, 
                        title=None, axis_titles=None, interactive=False, 
                        append=False, display=True):
        '''
            Insert save commands for devices
        '''

        if not display:
            import matplotlib
            matplotlib.use('Agg')

        # create the plots
        with plt.style.context('seaborn-notebook'):

            # grab the swept variable
            sweep = self.get_signal(sweepvar)
            
            # setup subplots
            if not self.plot_init:
                self.fig, self.axes = plt.subplots(ncols=1, nrows=len(expressions), squeeze=True)

                # set title
                if title:
                    self.fig.suptitle(title)    

                # set the axis titles
                if axis_titles:
                    self.axes.xlabel(axis_titles[0])
                    self.axes.ylabel(axis_titles[1])

                if interactive and display:
                    plt.ion()
                    plt.show()

                formatter = FuncFormatter(lambda y, _: '{:.16g}'.format(y))

            # calculate and plot the data
            plot_signals = []
            for row_i, expression in enumerate(expressions):
                for device in devices:

                    # get the device type 
                    device_type = self.find_device_type(device)

                    # vsat_marg is not in devices so need to form that ourselves
                    if expression == "vsat_marg":
                        measurement_vds = 'v(@M.' + device + '.m' + device_type + '[vds])'
                        measurement_vdsat = 'v(@M.' + device + '.m' + device_type + '[vdsat])'

                        # get the results
                        data_measurement_vds = self.get_signal(measurement_vds)
                        data_measurement_vdsat = self.get_signal(measurement_vdsat)
                        data = [data_measurement_vds[i] - data_measurement_vdsat[i] for i in range(len(data_measurement_vds))]
                    else:
                        measurement = '@M.' + device + '.m' + device_type + '[' + expression + ']'
                        
                        # get the results
                        data = self.get_signal(measurement)

                    # check for negative values
                    for val in data:
                        if val < 0:
                            print('Device %s has negative Vdsatmargin!' % device)
                            plot_signals.append(device)
                            break

            # plot the results
            if len(plot_signals) > 0:
                if len(expressions) > 1:
                    for signal in plot_signals:
                        self.axes[row_i].plot(sweep, signal, linewidth=linewidth, alpha=alpha)
                else:
                    for signal in plot_signals:
                        self.axes.plot(sweep, signal, linewidth=linewidth, alpha=alpha)
                self.axes.legend(devices)
                self.axes.grid(True)

            # update the graph
            if display:
                if append:
                    plt.draw()
                    plt.pause(0.001)
                else:
                    plt.draw()
                    plt.pause(0.001)
                    plt.show()

        self.plot_init=True


    def check_op_region(self, sweepvar=None, exempt_list=None, skip_insertion=False, devices=None):
        """
            Check that all the devices are in saturation
        """

        if not skip_insertion:

            # find all the devices
            if not devices:
                devices = self.find_all_mosfets()

            # insert the command to save the devices
            self.insert_op_save(devices, ['vsat_marg'])

        # run the simulation
        self.run_simulation()

        # split the devices into linear and switched devices
        devices_saturation = []
        devices_switched = []
        devices_triode = []
        devices_decap = []
        devices_dummy = []
        for device in devices:
            if 'sw' in device:
                devices_switched.append(device)
            elif 'triode' in device:
                devices_triode.append(device)
            elif 'decap' in device:
                devices_decap.append(device)
            elif 'dum' in device:
                devices_dummy.append(device)
            else:
                devices_saturation.append(device)

        # grab the swept variable
        if sweepvar:
            sweep = self.get_signal(sweepvar)

        # initialise a test pass
        test_pass = True

        # check that all linear devices are in saturation
        plot_device_names = []
        for device in devices_saturation:

            # get the device type 
            device_type = self.find_device_type(device)

            # vsat_marg is not in devices so need to form that ourselves
            measurement_vds = 'v(@M.' + device + '.m' + device_type + '[vds])'
            measurement_vdsat = 'v(@M.' + device + '.m' + device_type + '[vdsat])'

            # get the results
            data_measurement_vds = self.get_signal(measurement_vds)
            data_measurement_vdsat = self.get_signal(measurement_vdsat)
            data = [data_measurement_vds[i] - data_measurement_vdsat[i] for i in range(len(data_measurement_vds))]
            
            # check for negative values
            for i, val in enumerate(data):
                if val < 0:

                    # some devices can be ignored if specified by the user
                    if exempt_list:
                        if not device in exempt_list:

                            # signal there is an error
                            test_pass = False

                            print('Device %s has negative Vdsatmargin!  Vds=%f, Vdsat=%f at sweep=%f' % (device, data_measurement_vds[i], data_measurement_vdsat[i], sweep[i]))
                            
                            if sweepvar:
                                plt.plot(sweep, data)
                                plot_device_names.append(device)
                            break

                    else:

                        # signal there is an error
                        test_pass = False

                        print('Device %s has negative Vdsatmargin!  Vds=%f, Vdsat=%f at sweep=%f' % (device, data_measurement_vds[i], data_measurement_vdsat[i], sweep[i]))
                            
                        if sweepvar:
                            plt.plot(sweep, data)
                            plot_device_names.append(device)
                        break

        # render the plot
        if len(plot_device_names) > 0:
            plt.legend(plot_device_names)
            plt.grid(True)
            plt.show()

        #  alert the user - primarily if it's a pass so there is some notification the test has been performed
        if test_pass:
            print('The test has completed with no operating point issues found')
        else:
            print('The test has found operating point issues - please investigate further')


    def restart_simulation(self):
        '''
            Remove the current circuit and restart from scratch
        '''

        # remove the current circuit
        self.ngspice.exec_command("remcirc")

        # write the temporary netlist
        with open('spiceinterface_temp.spice', 'w') as f:
            f.write(self.simulation['netlist'])

        # reload the circuit
        if self.config['simulator']['silent']:
            with suppress_stdout_stderr():
                self.ngspice.source('spiceinterface_temp.spice')
        else:
            self.ngspice.source('spiceinterface_temp.spice')



    def run_simulation(self, new_instance=True, outputs=None):
        '''
            Run simulation
        '''

        # select the simulation interface to use
        if self.config['simulator']['executable'] == 'ngspice':

            # write the temporary netlist
            with open('spiceinterface_temp.spice', 'w') as f:
                f.write(self.simulation['netlist'])

            # run ngspice
            if self.config['simulator']['shared']:

                # destroy previous run data
                self.ngspice.destroy()
                self.ngspice.exec_command("reset")

                # load the netlist into the 
                if new_instance:
                    self.ngspice.source('spiceinterface_temp.spice')

                # run the simulation
                if self.config['simulator']['silent']:
                    with suppress_stdout_stderr():
                        self.ngspice.run()
                else:
                    self.ngspice.run()

                # save the outputs
                self.ngspice.exec_command("set filetype=ascii")
                self.ngspice.exec_command("write spiceinterface_temp.raw")


            else:

                # set the output format to ascii required by spyci
                os.environ["SPICE_ASCIIRAWFILE"] = "1"

                # run the simulation through command line
                bash_command = "ngspice -b -r spiceinterface_temp.raw -o spiceinterface_temp.out spiceinterface_temp.spice"
                process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
                output, error = process.communicate()

                # check if error occured
                with open('spiceinterface_temp.out') as f:
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
                    self.simulation_data[output] = spyci.load_raw("spiceinterface_temp_"+output+".raw")
            else:
                self.simulation_data = spyci.load_raw("spiceinterface_temp.raw")

        else:
            assert False, 'The simulator (%s) is not currently supported' % self.config['simulator']


    def monte_carlo(self, number_runs, analysis, signals, measurements=None):
        """
            Perform Monte-Carlo simulation

            Both signals and measurements should be list of dictionaries with:
                name
                plot
        """

        # use the shared simulator interface
        self.config['simulator']['shared'] = True

        # add the monte-carlo parameters to the netlist
        # self.monte_carlo_parameters_append()
        # self.run_simulation(new_instance=True)

        # find the number of signals to plot
        # number_plots = 0
        # for signal in signals:
        #     print(signal)
        #     if signal[1]:
        #         number_plots += 1
        # for measurement in measurements:
        #     if measurement["plot"]:
        #         number_plots += 1

        # 
        # if number_plots > 0:

        # loop through the simulation
        data = []
        for i in range(number_runs):

            print('Beginning run %d of %d' % (i+1, number_runs))

            # run the simulation
            self.run_simulation(new_instance=(i==0))

            # # get the signals
            # temp_dict = {}
            # temp_dict['signals'] = self.get_signals(self, signals)

            # update plots
            if analysis == "op":

                # plot the results
                if i < number_runs-1:
                    self.plot_histogram('v(res)', interactive=True, append=True)
                else:
                    self.plot_histogram('v(res)', interactive=True)

            elif analysis == "dc_sweep":

                # plot the result
                if i < number_runs-1:
                    self.plot_dc_sweep(signals[0], linewidth=1, alpha=0.5, interactive=True, append=True)
                else:
                    self.plot_dc_sweep(signals[0], linewidth=1, alpha=0.5, interactive=True)

            elif analysis == "bode":

                # plot the result
                if i < number_runs-1:
                    self.plot_bode('v(ac)', linewidth=1, alpha=0.5, interactive=True, append=True)
                else:
                    self.plot_bode('v(ac)', linewidth=1, alpha=0.5, interactive=True)
            


    def monte_carlo_parameters_append(self):
        '''
            Append Monte-Carlo parameters
        '''

        # remove the end command at the end of the netlist
        self.simulation['netlist'] = re.sub(r'\.end\n', '', self.simulation['netlist'])

        # add the parameters
        self.simulation['netlist'] += '\n\n* MONTE CARLO PARAMETERS'
        for parameter in self.monte_carlo_parameters:
            assert parameter[1] == "gauss"
            self.simulation['netlist'] += "\n.param %s_spectre='agauss(0, %f, %d)/%s'" % (parameter[0], parameter[2], self.monte_carlo_sigma, parameter[0])    
        self.simulation['netlist'] += '\n\n\n'

        # append the end command we previously removed
        self.simulation['netlist'] += '\n.end\n'



    def read_results(self, netlist="spiceinterface_temp.raw"):
        '''
            Read the simulation resutls from file
        '''

        self.simulation_data = spyci.load_raw(netlist)



    def set_dc_sweep(self, parameter, start, end, number_steps):
        '''
            Set the values for a DC sweep
        '''

        # calculate the step size
        step_size = (end - start)/(number_steps-1)


        if self.config['simulator']['shared']:
            print("NOT IMPLEMENTED EFFICIENTLY!!!! - set_dc_sweep()")
    
        # update the netlist
        sub_string = ".dc %s %0.12f %0.12f %0.12f" % (parameter, start, end, step_size)
        self.simulation['netlist'] = re.sub(r'\.dc .*', sub_string, self.simulation['netlist'])



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


    def get_signals(self, signal_names, factor=1.0):
        '''
            Return one or more signals from the simulation results
        '''

        # loop through each signal
        data_dict = {}
        for signal in signal_names:
            data_dict[signal] = self.get_signal(signal, factor)

        return data_dict


    def get_swept_values(self, return_name=False, dataset=None):
        '''
            Return the values of the swept parameter and optionally the name
        '''

        # grab the simulation dataset requested
        if dataset:
            simulation_data = self.simulation_data[dataset]
        else:
            simulation_data = self.simulation_data

        # extract each data point and convert to real list
        index = 0
        data = []
        for n in range(len(simulation_data['values'])):
            data.append(np.real(simulation_data['values'][n][index]))

        # return just the data or include the name of the swept parameter?
        if return_name:
            return data, simulation_data['vars'][index]
        else:
            return data



    def sweep_parameter(self, parameter, start, end, number_steps, signals, sweeptype='singlestep'):
        '''
            Sweep the temperature and provide the resulting signals
        '''

        # start/stop the simulator for each sweep step
        # this is slower but more flexible
        if sweeptype == 'singlestep':

            # create temperature list
            parameter_list = np.linspace(start, end, number_steps)

            # create a results dictionary
            results = {}
            results[parameter] = parameter_list

            # create arrays for the signals
            for signal in signals:
                results[signal] = []

            # loop through the temperatures
            for parameter_value in parameter_list:

                # update the netlist
                if parameter == 'temp':
                    self.set_temperature(parameter_value)
                else:
                    self.set_parameters([[parameter, float(parameter_value)]])

                # run the simulation
                self.run_simulation()

                # grab the results
                for signal in signals:

                    temp_signal = self.get_signal(signal)

                    # if a single point is returned we don't want unnecessary list depth
                    if len(temp_signal) == 1:
                        results[signal] = temp_signal[0]
                    else:
                        results[signal] = temp_signal

        # edit the DC sweep commad
        elif sweeptype == 'dcsweep':

            # edit the netlist DC sweep command
            self.set_dc_sweep(parameter, start, end, number_steps)

            # run the simulation
            self.run_simulation()

            # create a results dictionary
            results = {}
            for signal in signals:

                if signal == 'temp':
                    results[signal] = np.linspace(start, end, number_steps)
                else:
                    results[signal] = self.get_signal(signal)

        return results




# Define a context manager to suppress stdout and stderr.
class suppress_stdout_stderr(object):
    '''
    A context manager for doing a "deep suppression" of stdout and stderr in 
    Python, i.e. will suppress all print, even if the print originates in a 
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).      

    '''
    def __init__(self):
        # Open a pair of null files
        self.null_fds =  [os.open(os.devnull,os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = [os.dup(1), os.dup(2)]

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0],1)
        os.dup2(self.null_fds[1],2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0],1)
        os.dup2(self.save_fds[1],2)
        # Close all file descriptors
        for fd in self.null_fds + self.save_fds:
            os.close(fd)
