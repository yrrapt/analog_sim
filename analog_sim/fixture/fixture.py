import re, os, yaml

import analog_sim.tools.xschem as xschem
from analog_sim.fixture.component import *
from analog_sim.fixture.power import *
from analog_sim.fixture.simulation import *
from analog_sim.plot.plot import *

class Fixture():
    '''
        A testbench object. 
    '''

    netlist_path = '_rundir/netlist.spice'

    def __init__(self, dut_schematic=''):

        # internal test items
        self.includes = []
        self.power_domains = {}
        self.components = {}
        self.options = {}
        self.simulation = None
        self.initial_conditions = None
        self.node_set = None

        # generate the cell netlist
        if dut_schematic != '':
            netlist = xschem.generate_cell(schematic=dut_schematic)
            netlist = netlist.split('** flattened .save nodes')[0]

            cell_name = dut_schematic.split('/')[-1].split('.')[0]
            self.add_component( DUTComponent(   name            = cell_name,
                                                netlist         = netlist))
        
        # save reference to the simulator object
        simulator = os.environ['SIMULATOR']
        if simulator == 'xyce':
            from analog_sim.spice.xyce import XyceInterface
            self.analog_sim_obj = XyceInterface()

        elif simulator == 'ngspice':
            from analog_sim.spice.ngspice import NgSpiceInterface
            self.analog_sim_obj = NgSpiceInterface()

        elif simulator == 'spectre':
            from analog_sim.spice.spectre import SpectreInterface
            self.analog_sim_obj = SpectreInterface()


    def set_include(self, config):

        if type(config) == str:

            x = re.match(r'\$[A-Z_]+', config)

            config = config.replace(x.group(0), os.environ[x.group(0)[1:]])

            with open(config) as config_file:
                global_settings = yaml.load(config_file, Loader=yaml.FullLoader)
                self.includes.append( IncludeLibrary(global_settings['include'], self.pvt['corner']['nominal']) )


    def set_pvt(self, config):

        if type(config) == str:

            x = re.match(r'\$[A-Z_]+', config)

            config = config.replace(x.group(0), os.environ[x.group(0)[1:]])

            with open(config) as config_file:
                global_settings = yaml.load(config_file, Loader=yaml.FullLoader)
                self.pvt = global_settings['pvt']


    def set_sim_conditions(self, conditions):
        print('set_sim_conditions')
        pass


    def add_component(self, component):
        '''
            Add a component to the simulation
        '''

        if not component.type in self.components.keys():
            self.components[component.type] = {}

        self.components[component.type][component.name] = component


    def add_power_domain(self, power_domain):
        '''
            Add a power domain to the simulation
        '''

        self.power_domains[power_domain.name] = power_domain


    def get_power_domain(self, name):
        '''
            Return the reference to a power domain
        '''

        return self.power_domains[name]


    def set_simulation(self, simulation):
        '''
            Set the simulation configuration to be used
        '''

        self.simulation = simulation


    def set_initial_conditions(self, initial_conditions):
        '''
            Set the simulation initial conditions
        '''

        self.initial_conditions = initial_conditions


    def set_node_set(self, node_set):
        '''
            Set the simulation node set
        '''

        self.node_set = node_set

    
    def write_netlist(self):
        '''
            Write the netlist for the simulation
        '''

        netlist = '* auto-generated netlist from analog_sim environment\n\n'

        # create supply domains first
        netlist += '*** Library includes\n\n'
        for include in self.includes:

            netlist += include.write_netlist(self.analog_sim_obj)
            netlist += '\n'

        # create supply domains first
        netlist += '*** Supply domains\n\n'
        for domain in self.power_domains:

            netlist += '* Supply domain: %s\n' % domain
            netlist += self.power_domains[domain].write_netlist(self.analog_sim_obj)
            netlist += '\n'

        # short gnd to 0
        netlist += 'Vgnd0 gnd 0 0\n'

        # add all the components
        netlist += '\n*** Components\n\n'
        for component_type in self.components:
            for component in self.components[component_type]:

                netlist += '* Component: %s\n' % component
                netlist += self.components[component_type][component].write_netlist(self.analog_sim_obj)
                netlist += '\n'

        # instantiate any DUTS
        netlist += '\n*** DUTs\n\n'
        for dut in self.components['dut']:

            netlist += '* DUT: %s\n' % dut
            netlist += self.components['dut'][dut].write_netlist_instance(self.analog_sim_obj)
            netlist += '\n'

        # set initial conditions
        if self.initial_conditions != None:
            netlist += self.analog_sim_obj.netlist_initial_conditions(self.initial_conditions)
            netlist += '\n\n'

        # set node set
        if self.node_set != None:
            netlist += self.analog_sim_obj.netlist_node_set(self.node_set)
            netlist += '\n\n'

        # insert simulation instruction
        if self.simulation == None:
            print('WARNING! There is no simulation command set!')
        netlist += '* Simulation command\n'
        netlist += self.simulation.write_netlist(self.analog_sim_obj)
        netlist += '\n'

        # write netlist to file
        self.analog_sim_obj.write_netlist(netlist)
        
    
    def run_simulation(self):
        '''
            Run the simulation and retrieve the results
        '''

        # first form the netlist
        self.write_netlist()

        # kick off the simulation
        self.analog_sim_obj.run_simulation()

        # read in the results
        self.analog_sim_obj.read_results()