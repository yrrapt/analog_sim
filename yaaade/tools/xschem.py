import os
from subprocess import call


def netlist_generation(schematic, folder=None):
    """
        Generate a netlist from schematic
    """

    # start with only the xschem command
    command = ["xschem"]
    command += ["-n"]
    command += ["-q"] 

    # specify the output netlist
    if folder:
        command += ["-o"]
        command += [os.getcwd() + "/" + folder]    
    
    # ensure standard libraries are included in netlist
    command += ["--tcl"] 
    command += ["sky130_models"] 

    # add the schematic
    command += [os.getcwd() + "/" + schematic]

    # perform netlisting
    status = call(command, cwd=os.environ['PROJECT_ROOT'])

