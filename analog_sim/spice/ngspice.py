import os, re, subprocess
import numpy as np
from spyci import spyci
from PySpice.Spice.NgSpice.Shared import NgSpiceShared

from analog_sim.spice.generic import GenericSpiceInterface


class NgSpiceInterface(GenericSpiceInterface):
    '''

    '''

    def __init__(self, verbose=True, netlist_path=None, pdk_path=None):
        '''
            Instantiate the object
        '''