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
    command += ["-b"] 
    command += ["-x"] 

    # specify the output netlist
    if folder:
        command += ["-o"]
        command += [os.getcwd() + "/" + folder]    
    
    # ensure standard libraries are included in netlist
    with open('/tmp/netlist.tcl','w') as file:
        file.write('xschem netlist\nxschem netlist') 
    command += ["--script"] 
    command += ["/tmp/netlist.tcl"] 

    # add the schematic
    command += [schematic]

    # perform netlisting
    status = call(command, cwd=os.environ['PROJECT_ROOT'])
