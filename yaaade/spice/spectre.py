import re
import subprocess
import libpsf

from yaaade.spice.generic import GenericSpiceInterface

class SpectreInterface(GenericSpiceInterface):
    '''

    '''

    def __init__(self, verbose=True, netlist_path=None, pdk_path=None):
        '''
            Instantiate the object
        '''

        super().__init__(verbose, netlist_path, pdk_path)

        self.config['simulator'] = {'executable'    :   'spectre',
                                    'shared'        :   True,
                                    'silent'        :   False}
        self.config['verbose'] = verbose



    def get_sim_results(self, output):
        '''
            Extract all the simulation results
        '''

        sim_data = libpsf.PSFDataSet( 'spiceinterface_temp.raw/' + output )
        signal_names = sim_data.get_signal_names()


    def run_simulation(self, new_instance=True, outputs=None):
        '''
            Run simulation
        '''

        # write the temporary netlist
        with open('spiceinterface_temp.spice', 'w') as f:
            f.write(self.simulation['netlist'])


        # run the simulation through command line
        # bash_command = "spectre -format nutascii spiceinterface_temp.spice"
        # bash_command = "spectre -format psfascii spiceinterface_temp.spice"
        bash_command = "spectre spiceinterface_temp.spice"
        process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()


        self.simulation_data = {}
        for output in outputs:

            if output == 'op':
                sim_data = libpsf.PSFDataSet( 'spiceinterface_temp.raw/dcOp.dc')

            elif output == 'noise':
                sim_data = libpsf.PSFDataSet( 'spiceinterface_temp.raw/noise.noise')
            else:
                sim_data = libpsf.PSFDataSet( 'spiceinterface_temp.raw/' + output )

            self.simulation_data[output] = {}

            for signal in sim_data.get_signal_names():
                signal_shortened = signal.split(':')[-1]

                if output == 'noise' and signal_shortened == 'out':
                    signal_shortened = 'onoise_spectrum'

                self.simulation_data[output][signal_shortened] = sim_data.get_signal(signal)


            if sim_data.is_swept():

                sweep_variable = sim_data.get_sweep_param_names()[0]

                if sweep_variable == 'freq':
                    sweep_variable = 'frequency'

                self.simulation_data[output][sweep_variable] = sim_data.get_sweep_values()




        # sim_data = libpsf.PSFDataSet( 'spiceinterface_temp.raw/dcOp.dc' )
        # signal_names = sim_data.get_signal_names()
        # print('signal_names', signal_names)

        # gm = sim_data.get_signal('MN0:gm')
        # print('gm', gm)

        # # read in the results of the simulation
        # if outputs:
        #     self.simulation_data = {}
        #     for output in outputs:
        #         self.simulation_data[output] = spyci.load_raw("spiceinterface_temp_"+output+".raw")
        # else:
        #     self.simulation_data = spyci.load_raw("spiceinterface_temp.raw")



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
                sub_string = "\\1%s=%0.20f\\2" % (parameter[0], parameter[1])
                log_information += '%s=%0.20f  ' % (parameter[0], parameter[1])
            else:
                sub_string = "\\1%s=%f\\2" % (parameter[0], parameter[1])
                log_information += '%s=%f  ' % (parameter[0], parameter[1])
            self.simulation['netlist'] = re.sub(r'(parameters.+)%s=\S+(.*)' % parameter[0], sub_string, self.simulation['netlist'])

        # update user
        if self.config['verbose']:
            print(log_information)
