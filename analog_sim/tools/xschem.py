import os
from subprocess import call


def netlist_generation(schematic, folder=None, topcell=False):
    """
        Generate a netlist from schematic
    """

    # start with only the xschem command
    command = ["xschem"]
    command += ["-n"]
    command += ["-q"]
    command += ["-x"]
    # command += ["-b"]

    # specify the output netlist
    if folder:
        command += ["-o"]
        command += [os.getcwd() + "/" + folder]
    
    # ensure standard libraries are included in netlist
    tcl_command = 'xschem netlist\nxschem netlist\n'
    with open('/tmp/netlist.tcl','w') as file:
        file.write(tcl_command)
    command += ["--script"]
    command += ["/tmp/netlist.tcl"]
    
    # include subcircuit definition
    if topcell:
        command += ["--tcl"]
        command += ["set top_subckt 1"]

    # add the schematic
    command += [schematic]

    # perform netlisting
    status = call(command, cwd=os.environ['PROJECT_ROOT'])

    return status


def generate_cell(library, cell):
    """
        Generate the cell
    """

    # generate the cell location string
    string = ''
    if library != '':
        string += library+'/'
    string += cell+'/schematic/'+cell+'.sch'

    # generate the cell
    netlist_generation(string, topcell=True)

    return open(os.environ['HOME']+'/.xschem/simulations/'+cell+'.spice', "r").read()
    