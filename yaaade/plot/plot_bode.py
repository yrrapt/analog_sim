#!/usr/bin/env python3

import os, sys
from yaaade.spice.generic import GenericSpiceInterface
from yaaade.plot.plot import * 

print(sys.argv[1])


# create the object
yaaade_obj = GenericSpiceInterface()

# read in the results
yaaade_obj.read_results(sys.argv[1])

# plot the results
plot_bode(yaaade_obj, 'v(ac)', linewidth=1, alpha=1)