

class SimulationCommand():
    '''
        A generalised simulation command. 
    '''

    def __init__(self):
        '''
        '''

        pass


class DCSweepSimulation(SimulationCommand):
    '''
        A DC sweep simulation command. 
    '''

    def __init__(self, parameter, start, stop, increment):

        super().__init__()

        # save the parameters internally
        self.parameter  = parameter
        self.start      = start
        self.stop       = stop
        self.increment  = increment


    def write_netlist(self, analog_sim_obj):
        '''
            Generate the netlist instantiation for the simulation
        '''

        return analog_sim_obj.netlist_sim_dcsweep(  parameter   = self.parameter, 
                                                    start       = self.start,
                                                    stop        = self.stop,
                                                    increment   = self.increment)


class TranSimulation(SimulationCommand):
    '''
        A transient simulation command. 
    '''

    def __init__(self, final_time, initial_step=-1):

        super().__init__()

        # save the parameters internally
        self.final_time     = final_time
        self.initial_step   = initial_step


    def write_netlist(self, analog_sim_obj):
        '''
            Generate the netlist instantiation for the simulation
        '''

        return analog_sim_obj.netlist_sim_tran( final_time   = self.final_time, 
                                                initial_step = self.initial_step)


class IncludeLibrary():
    '''
        Include library. 
    '''

    def __init__(self, library, corner):
        
        self.library = library
        self.corner  = corner


    def write_netlist(self, analog_sim_obj):
        '''
            Generate the netlist instantiation for the library
        '''

        return analog_sim_obj.netlist_library( library = self.library, 
                                           corner  = self.corner)