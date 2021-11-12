import os, stat
import subprocess
import logging
import docker
import re
import shutil
from pathlib import Path



log = logging.getLogger(__name__)


def run_pex(gds_file, cell, 
            extracted_netlist='/tmp/analog_sim/space/extracted_netlist.spice',
            log_file='/tmp/analog_sim/klayout_lvs_log'):
    """
        Run PEX in Space
    """

    # create a temporary run directory
    shutil.rmtree('/tmp/analog_sim/space')
    Path("/tmp/analog_sim/space").mkdir(parents=True, exist_ok=True)

    # copy the technology files
    shutil.copy(os.environ['TECH_ENVIRONMENT']+'/pex/space/xt018/bmlist.gds',  '/tmp/analog_sim/space/bmlist.gds')
    shutil.copy(os.environ['TECH_ENVIRONMENT']+'/pex/space/xt018/epslay.def',  '/tmp/analog_sim/space/epslay.def')
    shutil.copy(os.environ['TECH_ENVIRONMENT']+'/pex/space/xt018/maskdata',    '/tmp/analog_sim/space/maskdata')
    shutil.copy(os.environ['TECH_ENVIRONMENT']+'/pex/space/xt018/space.def.p', '/tmp/analog_sim/space/space.def.p')
    shutil.copy(os.environ['TECH_ENVIRONMENT']+'/pex/space/xt018/space.def.s', '/tmp/analog_sim/space/space.def.s')
    shutil.copy(os.environ['TECH_ENVIRONMENT']+'/pex/space/xt018/xspicerc',    '/tmp/analog_sim/space/xspicerc')

    # copy the source
    gds_name = gds_file.split('/')[-1]
    shutil.copy(gds_file,    '/tmp/analog_sim/space/' + gds_name)

    # create the run script
    docker_script = f"""#!/bin/bash

# use the latest technology files
rm -rf /cacd/share/lib/process/xt018
yes | cp -rf /xt018 /cacd/share/lib/process/

# move to working directory
cd /rundir

# remove old project
rmpr -fs .

# create new project
mkpr -p xt018 -l 0.005 .

# open the GDS file
cgi {gds_name}

# create the tech file
tecc /cacd/share/lib/process/xt018/space.def.s 

# run extraction
space3d -l3 -E /cacd/share/lib/process/xt018/space.def.t -P /cacd/share/lib/process/xt018/space.def.p {cell}

# generate netlist
xspice -a {cell} > {cell}.spice

# change ownership to host user
# chown -R {os.environ['USER']}:{os.environ['USER']} /rundir/* 
chmod -R 777 /rundir/* 
""" 

    with open('/tmp/analog_sim/space/run.sh', 'w') as f:
        f.write(docker_script)
    st = os.stat('/tmp/analog_sim/space/run.sh')
    os.chmod('/tmp/analog_sim/space/run.sh', st.st_mode | stat.S_IEXEC)

    # run docker 
    docker_client = docker.from_env()
    volumes = ['/tmp/analog_sim/space:/rundir', os.environ['TECH_ENVIRONMENT']+'/pex/space/xt018:/xt018']
    try:
        docker_output = docker_client.containers.run("space-tech-image", "/rundir/run.sh", volumes=volumes)
    except:
        return False

    # read the extracted netlist
    with open(f'/tmp/analog_sim/space/{cell}.spice') as f:
        netlist = f.read()

    # remove the bulk voltage sources
    netlist = re.sub(r'\n[vr][np]bulk.*', '', netlist)

    # remove commented out models
    netlist = re.sub(r'\n\*.model.*', '', netlist)

    # remove unused pbulk and nbulk ports
    netlist = re.sub(r'[pn]bulk ', '', netlist)

    # use the subcircuit definition
    netlist = re.sub(r'\*\.subckt', '.subckt', netlist)
    netlist = re.sub(r'\*\.ends',   '.ends',   netlist)


    ##### shorting resistor

    # find the net names
    re_matches = re.search(r'\nr\S+ (\S+) (\S+) 0', netlist)

    # remove the 0 ohm resistor line
    netlist = re.sub(r'\nr\S+ (\S+) (\S+) 0', r'', netlist)

    # substitute the net names
    netlist = re.sub(re_matches.groups()[0], re_matches.groups()[1], netlist)


    ### make mosfets subciruits 
    netlist = re.sub(r'\nm', r'\nxm', netlist)
    
    return netlist