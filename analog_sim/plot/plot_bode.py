#!/usr/bin/env python3

import os, sys
from analog_sim.spice.generic import GenericSpiceInterface
from analog_sim.plot.plot import * 

print(sys.argv[1])


# create the object
analog_sim_obj = GenericSpiceInterface()

# read in the results
analog_sim_obj.read_results(sys.argv[1])

# plot the results
plot_bode(analog_sim_obj, 'v(ac)', linewidth=1, alpha=1)