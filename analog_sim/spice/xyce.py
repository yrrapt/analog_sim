import re
import subprocess

from analog_sim.spice.generic import GenericSpiceInterface

class XyceInterface(GenericSpiceInterface):
    '''

    '''

    def __init__(self, verbose=True, netlist_path=None, pdk_path=None):
        '''
            Instantiate the object
        '''

        super().__init__(verbose, netlist_path, pdk_path)

        # Xyce defaults to binary raw format
        self.result_type = 'binary'


    def run_simulation(self, new_instance=True, outputs=None):
        '''
            Run simulation
        '''

        # run the simulation through command line
        bash_command = "Xyce -r %s/%s %s/%s" % (self.run_dir, self.temp_result, self.run_dir, self.temp_netlist)
        process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()

        # read in the results
        self.read_results("%s/%s" % (self.run_dir, self.temp_result))


    def netlist_clock_voltage(self, name, frequency, voltage, rise_fall=-1, negative='0', delay=0):
        '''
            Write a netlist line for a clock voltage source
            
            PULSE(V1 V2 TD TR TF PW PER)
        '''

        # if the rise and fall is not set then default to 1/50 of the period
        if rise_fall < 0:
            rise_fall = (1/frequency)/50

        # form the voltage pulse line
        line  = 'V' + name + ' ' + name + ' ' + negative + ' '
        line += 'pulse(%s 0 ' % self.unit_format(voltage)
        line += '%s ' % self.unit_format(delay)
        line += '%s ' % self.unit_format(rise_fall)
        line += '%s ' % self.unit_format(rise_fall)
        line += '%s ' % self.unit_format(0.5/frequency)
        line += '%s)' % self.unit_format(1/frequency)
        return line


    def netlist_voltage_pwl(self, name, voltage, negative='0', dc=0):
        '''
            Write a netlist line for a DC PWL source
        '''

        return 'V' + name + ' ' + name + ' ' + negative + ' pwl 0 %f ' % dc + ' ' + voltage


    def netlist_sim_tran(self, final_time, initial_step=-1, use_intitial_conditions=False):
        '''
            Define a transient simulation

            TRAN <initial step value> <final time value>
        '''

        # if the rise and fall is not set then default to 1/50 of the period
        if initial_step < 0:
            initial_step = final_time/1000

        # form the transient simultion line
        line  = '.tran %s %s' % (self.unit_format(initial_step), self.unit_format(final_time))

        if use_intitial_conditions:
            line += ' uic'

        return line


    def netlist_vccs(self, name, in_pos, in_neg, out_pos, out_neg, gain):
        '''
            Create a Voltage Controlled Current Source
        '''

        # form the transient simultion line
        line  = 'G%s %s %s %s %s %s' % (name, out_neg, out_pos, in_pos, in_neg, self.unit_format(gain))
        return line


    def netlist_behavioural_source(self, name, pos_net, neg_net, output_type, expression):
        '''
            Create a Behavioural Source
        '''

        line  = 'B%s %s %s ' % (name, pos_net, neg_net)


        if output_type == 'voltage':
            line += 'V={ %s }' % expression

        elif output_type == 'current':
            line += 'I={ %s }' % expression

        else:
            assert False, 'Unsupported output type specified: %s' % output_type
        
        return line


    def netlist_temperature(self, temperature):
        '''
            Set the temperature
        '''

        # form the include line
        line  = '.options device temp=%s' % temperature
        return line

