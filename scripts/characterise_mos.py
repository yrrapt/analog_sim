import yaml

from yaaade.characterise.mos import CharacteriseMos


# create the object
characterise_mos_obj = CharacteriseMos()
characterise_mos_obj.spice_interface_obj.config['simulator']['shared']

# read in the device simulation parameters
with open(r'devices.yaml') as file:
    devices = yaml.full_load(file)


# loop through each of the devices making the measurements
for device in devices:

    print('-'*150)
    print('EXTRACTING OPERATING POINTS FOR DEVICE: ', device)
    print('-'*150)
    characterise_mos_obj.measure_mos_op( device, 
                                        devices[device]['w'], 
                                        devices[device]['l'], 
                                        ids=devices[device]['ids'],
                                        vds=devices[device]['vds'],
                                        vbs=devices[device]['vbs'],
                                        # vgs=devices[device]['vgs'],
                                        vdd=devices[device]['vdd'],
                                        type=devices[device]['type'])
