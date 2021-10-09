import numpy as np
import os, sys
import contextlib
import io
import re
import h5py
import subprocess
import fnmatch
from spyci import spyci


import matplotlib.pyplot as plt
import matplotlib.ticker
import matplotlib
from matplotlib.ticker import FuncFormatter

def create_sim_object(simulator: str):
    """
        Create the specified simulator object and return
    """

    if simulator == 'ngspice':
        from analog_sim.spice.ngspice import NgSpiceInterface
        analog_sim_obj = NgSpiceInterface()
    elif simulator == 'xyce':
        from analog_sim.spice.xyce import XyceInterface
        analog_sim_obj = XyceInterface()

    elif simulator == 'spectre':
        from analog_sim.spice.spectre import SpectreInterface
        analog_sim_obj = SpectreInterface()

    return analog_sim_obj


class GenericSpiceInterface():
    '''
        A library to interface to Spice simulators (NGSpice, Xyce, Spectre, TSpice etc...)

        Contains high level constructs to manipulate and run simulations without relying
        on simulator specfic netlist constructions.

        Will be developed into a library to allow for high programmatic control of electronic
        circuit simulation, design and verification. 
    '''

    run_dir      = '_rundir'
    temp_netlist = 'netlist.spice'
    temp_result  = 'results.raw'
    temp_log     = 'simulation.log'

    result_type  = 'binary'

    def __init__(self, verbose=True, netlist_path=None, pdk_path=None):
        '''
            Instantiate the object
        '''

        # is there a plot attached to the object?
        self.plot_init=False

        # if provided read in the base netlist
        if netlist_path:
            self.read_netlist_file(netlist_path)


    def write_netlist(self, netlist):
        '''
            Write the netlist to file
        '''

        # create the run directory if it doesn't already exist
        if not os.path.exists(self.run_dir):
            os.makedirs(self.run_dir)

        # write the netlist to file
        netlist_path = self.run_dir + '/' + self.temp_netlist
        with open(netlist_path, 'w') as file:
            file.write(netlist)


    def read_netlist_file(self, netlist_path):
        '''
            Read in a netlist from file
        '''

        with open(netlist_path) as f:
            self.simulation['netlist'] = f.read()

            # the line continuation is not needed as messes up parsing, remove it
            self.simulation['netlist'] = re.sub(r'\n\+', '', self.simulation['netlist'])
    

    def run_simulation(self, new_instance=True, outputs=None):
        '''
            Run simulation
        '''

        raise NotImplementedError('This needs to be implemented in a simulator specific function')


    def read_results(self, dataset=None):
        '''
            Read the simulation resutls from file
        '''

        if self.result_type == 'binary':
            self.read_raw_binary(dataset)
        else:
            self.read_raw_ascii(dataset)


    def read_raw_ascii(self, dataset):
        '''
            Read an ASCII raw results file
        '''

        raw_path = self.run_dir + '/' + self.temp_result
        raw_data = spyci.load_raw(raw_path)
        simulation_data = {}

        # pull out the data from the raw format into a nicer dictionary
        # with the signal name as the key
        for data_i, data_var in enumerate(raw_data['vars']):
            simulation_data[data_var['name']] = []
            for n in range(len(raw_data['values'])):
                simulation_data[data_var['name']].append(raw_data['values'][n][data_i])

        # single simulation data or multiple
        if dataset == None:
            self.simulation_data = simulation_data
        else:
            self.simulation_data = {}
            self.simulation_data[dataset] = simulation_data


    def read_raw_binary(self, dataset):
        '''
            Taken from: https://gist.github.com/snmishra/27dcc624b639c2626137
            Read ngspice binary raw files. Return tuple of the data, and the
            plot metadata. The dtype of the data contains field names. This is
            not very robust yet, and only supports ngspice.
            >>> darr, mdata = rawread('test.py')
            >>> darr.dtype.names
            >>> plot(np.real(darr['frequency']), np.abs(darr['v(out)']))
        '''

        BSIZE_SP = 512 # Max size of a line of data; we don't want to read the
               # whole file to find a line, in case file does not have
               # expected structure.
        MDATA_LIST = [b'title', b'date', b'plotname', b'flags', b'no. variables',
                    b'no. points', b'dimensions', b'command', b'option']

        # Example header of raw file
        # Title: rc band pass example circuit
        # Date: Sun Feb 21 11:29:14  2016
        # Plotname: AC Analysis
        # Flags: complex
        # No. Variables: 3
        # No. Points: 41
        # Variables:
        #         0       frequency       frequency       grid=3
        #         1       v(out)  voltage
        #         2       v(in)   voltage
        # Binary:
        fname = self.run_dir + '/' + self.temp_result
        fp = open(fname, 'rb')
        plot = {}
        count = 0
        arrs = []
        plots = []
        while (True):
            try:
                mdata = fp.readline(BSIZE_SP).split(b':', maxsplit=1)
            except:
                raise
            if len(mdata) == 2:
                if mdata[0].lower() in MDATA_LIST:
                    plot[mdata[0].lower()] = mdata[1].strip()
                if mdata[0].lower() == b'variables':
                    nvars = int(plot[b'no. variables'])
                    npoints = int(plot[b'no. points'])
                    plot['varnames'] = []
                    plot['varunits'] = []
                    for varn in range(nvars):
                        varspec = (fp.readline(BSIZE_SP).strip()
                                .decode('ascii').split())
                        assert(varn == int(varspec[0]))
                        plot['varnames'].append(varspec[1])
                        plot['varunits'].append(varspec[2])
                if mdata[0].lower() == b'binary':
                    rowdtype = np.dtype({'names': plot['varnames'],
                                        'formats': [np.complex_ if b'complex'
                                                    in plot[b'flags']
                                                    else np.float_]*nvars})
                    # We should have all the metadata by now
                    arrs.append(np.fromfile(fp, dtype=rowdtype, count=npoints))
                    plots.append(plot)
                    fp.readline() # Read to the end of line
            else:
                break

        # pull out the data from the raw format into a nicer dictionary
        # with the signal name as the key
        simulation_data = {}
        for data_i, data_var in enumerate(plots[0]['varnames']):

            # extract the interleaved data points
            data = []
            for n in range(int(plots[0][b'no. points'])):
                data.append(arrs[0][n][data_i])

            simulation_data[data_var.lower()] = {   'data'  : data,
                                                    'units' : plots[0]['varunits'][data_i]}

        # single simulation data or multiple
        if dataset == None:
            self.simulation_data = simulation_data
        else:
            self.simulation_data = {}
            self.simulation_data[dataset] = simulation_data


    def get_signal(self, signal_name, factor=1.0, dataset=None, complex_out=False):
        '''
            Return a signal from the simulation results
        '''

        # grab the simulation dataset requested
        if dataset:
            simulation_data = self.simulation_data[dataset]
        else:
            simulation_data = self.simulation_data

        # extract each data point and convert to real list
        if factor != 1.0 or (complex_out==False and np.iscomplex(simulation_data[signal_name.lower()]['data'][0])):
            data = []
            for n in range(len(simulation_data[signal_name.lower()])):

                if complex_out:
                    data.append(factor*simulation_data[signal_name.lower()][n])
                else:
                    data.append(factor*np.real(simulation_data[signal_name.lower()][n]))

            return data['data'], data['units']
        
        else:
            return simulation_data[signal_name.lower()]['data'], simulation_data[signal_name.lower()]['units']


    def get_signals(self, signal_names, factor=1.0, complex_out=False):
        '''
            Return one or more signals from the simulation results
        '''

        # loop through each signal
        data_dict = {}
        for signal in signal_names:
            data_dict[signal] = self.get_signal(signal, factor, complex_out=complex_out)

        return data_dict



    def set_temperature(self, temp):
        '''
            Set the simulation temperature
        '''

        raise NotImplementedError('This needs to be implemented in a simulator specific function')


    def set_parameter(self, parameter, value):
        '''
            Set parameter inside the netlist
        '''

        raise NotImplementedError('This needs to be implemented in a simulator specific function')


    def set_parameters(self, parameters):
        '''
            Set parameters inside the netlist

            Parameters should be passed as an array with with sub-arrays with
            the first element parameter string and the second element a value.

            ie. [['vds', 1.8], ['vbs', 0.2], ['ids', 1e-6]]
        '''

        for parameter in parameters:
            self.set_parameter(parameter[0], parameter[1])


    def set_sim_dc(self, variable, start, stop, increment):
        '''
            Define a DC sweep simulation
        '''

        raise NotImplementedError('This needs to be implemented in a simulator specific function')


    def set_sim_tran(self, stop, step, start_save=None):
        '''
            Define a DC sweep simulation
        '''

        raise NotImplementedError('This needs to be implemented in a simulator specific function')


    def netlist_voltage_dc(self, name, voltage, negative='0'):
        '''
            Write a netlist line for a DC voltage source
        '''

        return 'V' + name + ' ' + name + ' ' + negative + ' ' + ('%f' % voltage)
        raise NotImplementedError('This needs to be implemented in a simulator specific function')


    def netlist_current_pulse(self, name, value0, value1, 
                                    delay=None, 
                                    rise_time=None, 
                                    fall_time=None, 
                                    pulse_width=None, 
                                    period=None, 
                                    negative='0'):
        '''
            Write a netlist line for a pulse current source
        '''

        string  = 'I' + name + ' ' + name + ' ' + negative + ' pulse( ' 
        string += '%s ' % self.unit_format(value0)
        string += '%s ' % self.unit_format(value1)
        
        if delay != None:
            string += '%s ' % self.unit_format(delay)

            if delay != None:
                string += '%s ' % self.unit_format(rise_time)
        
                if fall_time != None:
                    string += '%s ' % self.unit_format(fall_time)
            
                    if pulse_width != None:
                        string += '%s ' % self.unit_format(pulse_width)
                    
                        if period != None:
                            string += '%s ' % self.unit_format(period)
        string += ')'
        return string


    def netlist_library(self, library, corner):
        '''
            Include a library with a corner specification
        '''

        # form the library include line
        line  = '.lib %s %s' % (library, corner)
        return line


    def netlist_include(self, file):
        '''
            Include a file
        '''

        # form the include line
        line  = '.include %s' % file
        return line


    def netlist_comment(self, comment):
        '''
            Add a comment
        '''

        # form the include line
        line  = '* %s' % comment
        return line


    def netlist_title(self, title):
        '''
            Add a title
        '''

        # form the include line
        line  = '.title %s' % title
        return line


    def netlist_capacitor(self, name, positive_net, capacitance, negative_net='0'):
        '''
            Create a capacitor instance
        '''

        # form the include line
        line  = 'C%s %s %s %s' % (name, positive_net, negative_net, self.unit_format(capacitance))
        return line


    def netlist_end(self):
        '''
            Create an end statmenet
        '''

        # form the include line
        line  = '.end'
        return line


    def unit_format(self, value):
        '''
            Format a value into a condensed engineering format
        '''

        if   abs(value) > 1e9:
            return '%fG' % (value / 1e9)
        elif abs(value) > 1e6:
            return '%fM' % (value / 1e6)
        elif abs(value) > 1e3:
            return '%fk' % (value / 1e3)
        elif abs(value) < 1e-12:
            return '%ff' % (value / 1e-15)
        elif abs(value) < 1e-9:
            return '%fp' % (value / 1e-12)
        elif abs(value) < 1e-6:
            return '%fn' % (value / 1e-9)
        elif abs(value) < 1e-3:
            return '%fu' % (value / 1e-6)
        elif abs(value) < 0:
            return '%fm' % (value / 1e-3)
        else:
            return '%f' % value




