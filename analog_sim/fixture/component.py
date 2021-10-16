import re


class FixtureComponent():
    '''
        A generalised fixture component. 
    '''

    def __init__(self):
        '''
        '''

        pass


class DUTComponent(FixtureComponent):
    '''
        A clock fixture component. 
    '''

    def __init__(self, name, netlist):

        super().__init__()

        # save the parameters internally
        self.type           = 'dut'
        self.name           = name
        self.netlist        = netlist

        # find the pins
        pin_str = re.search(r'\.subckt '+self.name+' (.*)', netlist)
        self.pins = pin_str.group(0).split( )[2:]


    def write_netlist(self, analog_sim_obj):
        '''
            Generate the netlist instantiation for the component
        '''

        return self.netlist


    def write_netlist_instance(self, analog_sim_obj):
        '''
            Generate the netlist instantiation for the component
        '''

        # instance name
        netlist  = 'X%s ' % self.name

        # each pin is connected to a net of the same name
        for pin in self.pins:
            netlist += '%s ' % pin

        # declare subcircuit name
        netlist += '%s ' % self.name

        return netlist


class ClockComponent(FixtureComponent):
    '''
        A clock fixture component. 
    '''

    def __init__(self, name, frequency, power_domain, delay=0, rise_fall=-1):

        super().__init__()

        self.type           = 'clock'
        self.name           = name
        self.frequency      = frequency
        self.power_domain   = power_domain
        self.delay          = delay
        self.rise_fall      = rise_fall


    def write_netlist(self, analog_sim_obj):
        '''
            Generate the netlist instantiation for the component
        '''

        return analog_sim_obj.netlist_clock_voltage(name      = self.name, 
                                                frequency = self.frequency,
                                                voltage   = self.power_domain.current_voltage,
                                                delay     = self.delay,
                                                rise_fall = self.rise_fall)


class BipolarComponent(FixtureComponent):
    '''
        A bipolar transistor fixture component. 
    '''

    def __init__(self, name, model, pin_nets, m=1):

        super().__init__()

        self.type       = 'bipolar'
        self.name       = name
        self.model      = model
        self.pin_nets   = pin_nets
        self.m          = m


    def write_netlist(self, analog_sim_obj):
        '''
            Generate the netlist instantiation for the component
        '''

        return analog_sim_obj.netlist_clock_voltage(name     = self.name, 
                                                model    = self.model,
                                                pin_nets = self.pin_nets,
                                                m        = self.m)


class OpampComponent(FixtureComponent):
    '''
        An opamp fixture component. 
    '''

    def __init__(self, name, pos_net, neg_net, out_net, gain=1e6):

        super().__init__()

        self.type       = 'vccs'
        self.name       = name
        self.pos_net    = pos_net
        self.neg_net    = neg_net
        self.out_net    = out_net
        self.gain       = gain


    def write_netlist(self, analog_sim_obj):
        '''
            Generate the netlist instantiation for the component
        '''

        string = ''
        if type(self.out_net) == list:
            for current_out_net in self.out_net:
                string = analog_sim_obj.netlist_vccs(   name    = self.name+'_'+current_out_net, 
                                                        pos_net = self.pos_net,
                                                        neg_net = self.neg_net,
                                                        out_net = current_out_net,
                                                        gain    = self.gain) + '\n'

        else:
            string = analog_sim_obj.netlist_vccs(   name    = self.name, 
                                                    pos_net = self.pos_net,
                                                    neg_net = self.neg_net,
                                                    out_net = self.out_net,
                                                    gain    = self.gain)
        return string