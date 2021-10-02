

class PowerDomain():
    '''
        A power domain definition. 
    '''

    def __init__(self,  name, 
                        pvt        = None,
                        nominal    = None,
                        low        = None,
                        high       = None,
                        power_type = None):

        # save the parameters internally
        self.name       = name

        # either retrieve voltages from PVT structure
        if pvt != None:
            if name in pvt['supplies'].keys():
                self.nominal    = pvt['supplies'][name]['nominal']
                self.low        = pvt['supplies'][name]['range'][0]
                self.high       = pvt['supplies'][name]['range'][1]
        
        # or specify manually
        else:
            self.nominal    = nominal
            self.low        = low
            self.high       = high

        # check we at least have a nominal voltag
        if self.nominal == None:
            raise ValueError('No nominal voltage defined by either PVT or directly')

        # save the power domain type
        self.type = power_type

        # default to the nominal voltage
        self.current_voltage = self.nominal


    def write_netlist(self, analog_sim_obj):
        '''
            Generate the netlist instantiation for the power supply
        '''

        return analog_sim_obj.netlist_dc_voltage(name      = self.name,
                                             voltage   = self.current_voltage)