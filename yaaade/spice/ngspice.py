from yaaade.spice.generic import GenericSpiceInterface

class NgSpiceInterface(GenericSpiceInterface):
    '''

    '''

    def __init__(self, verbose=True, netlist_path=None, pdk_path=None):
        '''
            Instantiate the object
        '''

        super().__init__(verbose, netlist_path, pdk_path)