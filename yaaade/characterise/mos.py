import h5py
import re
import copy
import numpy as np
import matplotlib.pyplot as plt

from yaaade.spice.ngspice import NgSpiceInterface
from yaaade.measure.measure import Measure

class CharacteriseMos():
    '''

    '''

    def __init__(self):

        # create the spice interface object
        self.spice_interface_obj = NgSpiceInterface()


    def measure_mos_op(self, device, w, l_list, ids=[1e-9,1e-3,10], vds=[0,1.8,11], vbs=[0,1.8,11], vgs=[0,1.8,11], type='nmos', vdd=None, temp=27, corner='tt'):
        '''
            Measure the operating point of an MOS
        '''

        # load the characterisation bench
        if type == 'nmos':
            self.spice_interface_obj.read_netlist_file('nmos_characterise.spice')
        else:
            self.spice_interface_obj.read_netlist_file('pmos_characterise.spice')

        # set the MOS name
        self.spice_interface_obj.simulation['netlist'] = re.sub(r'(.*)mos(.*)', r'\1'+device+r'\2', self.spice_interface_obj.simulation['netlist'])

        # set the temperature and corner
        self.spice_interface_obj.set_temperature(temp)
        self.spice_interface_obj.set_corner(corner)

        # set the maximum supply voltage
        if vdd:
            self.spice_interface_obj.set_parameters([['vdd', vdd]])
        

        # define the list of op parameters
        op_params = ["id", "vth", "vgs", "vds", "vbs", "gm", "gds", "gmbs", "vdsat", "cgg", "cgs", "cgd", "cgb", "cbs", "cdd"]
        save_string = ''
        for op_param in op_params:
            save_string += '@M.XM.m' + device + '[' + op_param + '] '
        self.spice_interface_obj.simulation['netlist'] = re.sub(r'SAVE_TO_BE_POPULATED', save_string, self.spice_interface_obj.simulation['netlist'])

        # create the sweep values
        vds_list = np.linspace(vds[0], vds[1], vds[2])
        vbs_list = np.linspace(vbs[0], vbs[1], vbs[2])
        
        # create drain current sweep
        ids_list = np.logspace(np.log10(abs(ids[0])), np.log10(abs(vbs[1])), int(np.log10(ids[1]/ids[0])*ids[2]))
        # vgs_list = np.logspace(np.log10(abs(vgs[0])), np.log10(abs(vgs[1])), int(np.log10(vgs[1]/vgs[0])*vgs[2]))
        # vgs_list = np.linspace(vgs[0], vgs[1], vgs[2])

        # parameters = [['vgs_max', vgs[1]], ['vgs_incr', vgs[1]/vgs[2]]]
        # self.spice_interface_obj.set_parameters(parameters)
        
        # run an initial simulation to find out how many drain current sweep values are present
        self.spice_interface_obj.run_simulation(outputs=['op1', 'noise1'])
        # self.spice_interface_obj.run_simulation(outputs=['dc1', 'noise1'])
        # num = self.spice_interface_obj.simulation_data['dc1']['no_points']

        # print('num', num)
        # num_ids = len(ids_list)
        # num = len(vgs_list)
        num = len(ids_list)

        # prepopulate the reuslts dictionary
        op_values = {}
        for param in op_params:
            op_values[param] = np.zeros((len(l_list), len(vds_list), len(vbs_list), num))
        op_values['noise_corner'] = np.zeros((len(l_list), len(vds_list), len(vbs_list), num))
        op_values['noise_slope'] = np.zeros((len(l_list), len(vds_list), len(vbs_list), num))
        op_values['noise_thermal'] = np.zeros((len(l_list), len(vds_list), len(vbs_list), num))

        # loop through each parameter value
        for l_i, l in enumerate(l_list):
            for vbs_i, vbs in enumerate(vbs_list):
                for vds_i, vds in enumerate(vds_list):
                    for ids_i, ids in enumerate(ids_list):
                    # for vgs_i, vgs in enumerate(vgs_list):

                        # update user
                        if self.spice_interface_obj.config['verbose']:
                            print('-'*150)
                            print('Beginning new OP setting')

                        # modify the netlist
                        # parameters = [['vbs', vbs], ['vds', vds], ['l', l], ['vgs', vgs]]
                        parameters = [['vbs', vbs], ['vds', vds], ['l', l], ['ids', ids]]
                        self.spice_interface_obj.set_parameters(parameters)

                        # run the simulation
                        # try:
                        self.spice_interface_obj.run_simulation(outputs=['op1', 'noise1'])
                        # self.spice_interface_obj.run_simulation(outputs=['dc1', 'noise1'])

                        # collect the op parameter values
                        for data_i, data_var in enumerate(self.spice_interface_obj.simulation_data['op1']['vars']):

                            # try and extract the op parameter - this will fail if the variable is something else
                            try:
                                op_param = data_var['name'].split('[')[1].split(']')[0]

                                # extract each data point and convert to real list
                                data_real = []
                                for n in range(len(self.spice_interface_obj.simulation_data['op1']['values'])):
                                    data_real.append(np.real(self.spice_interface_obj.simulation_data['op1']['values'][n][data_i]))

                                # save the sweep data to the dictionary
                                op_values[op_param][l_i][vds_i][vbs_i][ids_i] = data_real[0]
                                # op_values[op_param][l_i][vds_i][vbs_i][vgs_i] = data_real[0]

                            except IndexError:
                                pass

                        # calculate the noise parameters
                        frequency = self.spice_interface_obj.get_signal('frequency', dataset='noise1')
                        onoise = self.spice_interface_obj.get_signal('onoise_spectrum', dataset='noise1')
                        thermal, corner_frequency, flicker_factor = Measure.measure_noise(frequency, onoise)
                        op_values['noise_corner'][l_i][vds_i][vbs_i][ids_i] = corner_frequency
                        op_values['noise_slope'][l_i][vds_i][vbs_i][ids_i] = flicker_factor
                        op_values['noise_thermal'][l_i][vds_i][vbs_i][ids_i] = thermal
                        # op_values['noise_corner'][l_i][vds_i][vbs_i][vgs_i] = corner_frequency
                        # op_values['noise_slope'][l_i][vds_i][vbs_i][vgs_i] = flicker_factor
                        # op_values['noise_thermal'][l_i][vds_i][vbs_i][vgs_i] = thermal
                        
                        # simulation failed - most likely to MOS being in a weird region
                        # just ignore this and move on. the point will be filled with zeros
                        # except:
                        #     pass


        # save the data to file
        hdf_file = h5py.File('results/' + device + '.hdf5', 'w')
        for key, values in op_values.items():
            hdf_file.create_dataset(key, data=values)

        # save the width used
        hdf_file.create_dataset('w', data=w)

        # save the indexing information
        indexing_group = hdf_file.create_group('indexing')
        indexing = [['order', ['vbs', 'vds', 'l']], ['vbs', vbs_list], ['vds', vds_list], ['l', l_list]]
        for index in indexing:

            if isinstance(index[1][0], str):
                ascii_list = [_.encode("ascii", "ignore") for _ in index[1]]
                indexing_group.create_dataset(index[0], (len(ascii_list),1),'S10', ascii_list)
            else:   
                indexing_group.create_dataset(index[0], data=index[1])


class QueryMos():
    '''

    '''

    def __init__(self, filepath):
        '''
            Setup the query object to retrieve characterisation info
        '''

        # load the characterisation bench
        self.file = h5py.File(filepath, 'r')


    def get_field_names(self):
        '''
            Query the possible parameters of the file
        '''

        # grab the data keys
        group_list = list(self.file.keys())

        return group_list


    def get_parameter_names(self):
        '''
            Query the possible parameters of the file
        '''

        parameters = list( self.file['indexing'] )
        del parameters[parameters.index('order')]
        return parameters


    def get_parameter_values(self, parameter):
        '''
            Query the possible parameters of the file
        '''

        # check the selected parameter is valid
        parameters = self.get_parameter_names()
        assert parameter in parameters, 'Parameter (%s) not in valid list. Use the get_parameter_names() to find suitable options' % parameter

        # return the data
        return list( self.file['indexing'][parameter] )

        # index = self.find_index(parameter)
        # print('index', index)

        # print( list( self.file ) )


        # print( list( self.file['indexing'] ) )
        # print( list( self.file['indexing']['vds'] ) )


        # print( self.file['vds'][0][1] )

        # # print(self.file[])
        # # return self.file
        # return 0

        
    # short function to find indexes
    def find_index(self, find_parameter):

        # get the indexing data
        indexing = {}
        for key in list(self.file['indexing']):
            indexing[key] = list(self.file['indexing'][key])

        for i in range(len(indexing['order'])):
            if find_parameter == indexing['order'][i][0].decode('ascii'):
                return i


    def query_mos_op(self, parameter, conditions):
        '''
            Query the MOS operating point data
        '''

        if '/' in parameter:
            operands = parameter.split('/')

            if operands[1].startswith('2*pi*'):
                denominator = self.query_single_mos_op(operands[1][5:], conditions)
                denominator = [_*2*np.pi for _ in denominator]
            else:
                denominator = self.query_single_mos_op(operands[1], conditions)


            if operands[0] == '1':
                numerator   = [1.0]*len(denominator)
            else:
                numerator   = self.query_single_mos_op(operands[0], conditions)

            values = [numerator[_]/denominator[_] for _ in range(len(numerator))]
        
        else:
            values = self.query_single_mos_op(parameter, conditions)

        return values


    def query_single_mos_op(self, parameter, conditions):
        '''
            Query a single MOS operating point data
        '''

        # if integrated noise is queried then divert to that function
        if parameter == 'integrated_noise':
            assert 'f_hi' in conditions, 'Must provide frequency high value'
            return self.integrated_noise(conditions=conditions, f_hi=conditions['f_hi'])

        # get the indexing data
        indexing = {}
        for key in list(self.file['indexing']):
            indexing[key] = list(self.file['indexing'][key])

        # find the order of parameters in the LUT
        parameters = self.get_parameter_names()
        indices = [0,0,0,0]
        for key in conditions:
            if key in parameters:
                index = self.find_index(key)
                values = self.get_parameter_values(key)
                
                # find the closest index
                difference = []
                for i in range(len(values)):
                    difference.append( abs(values[i] - conditions[key]) )
                indices[index] = difference.index(min(difference))


        # find the id index
        if 'id' in conditions.keys():

            temp_condition = copy.deepcopy(conditions)
            del(temp_condition['id'])
            id_list = self.query_mos_op('id', temp_condition)
            difference = []
            for id_i in id_list:
                difference.append( abs(id_i - conditions['id'] ) )
            indices[3] = difference.index(min(difference))

            return self.file[parameter][indices[2]][indices[1]][indices[0]][indices[3]]
        
        else:
            return self.file[parameter][indices[2]][indices[1]][indices[0]]

        # # find the indexing for the data
        # index_values = [0]*len(conditions)
        # for condition in conditions:
        #     index = self.find_index(condition)
        #     index_values[index] = indexing[condition].index(conditions[condition])                
        # return self.file[parameter][index_values[2]][index_values[1]][index_values[0]]


    # def collect_expression(self, expression, conditions):
    #     '''
    #         Dismantle an expression to return values
    #     '''
        
    #     if '/' in expression:
    #         operands = expression.split('/')

    #         denominator = self.query_mos_op(operands[1], conditions)
    #         if operands[0] == '1':
    #             numerator   = [1.0]*len(denominator)
    #         else:
    #             numerator   = self.query_mos_op(operands[0], conditions)

    #         values = [numerator[_]/denominator[_] for _ in range(len(numerator))]
        
    #     else:
    #         values = self.query_mos_op(expression, conditions)

    #     return values


    def plot(self, x, y, conditions, y_log=True, extra_plot_cmd=None):
        '''
            Plot two parameters against each other
        '''

        if any([type(conditions[_])==list for _ in conditions]):
            loop_conditions = np.where([type(conditions[_])==list for _ in conditions])[0]
            for loop_condition in loop_conditions:
                for vary in conditions[list(conditions.keys())[loop_condition]]:

                    # create a copy with a single value in the sweep
                    temp_condition = copy.deepcopy(conditions)
                    temp_condition[list(conditions.keys())[loop_condition]] = vary

                    # get the results
                    x_values = self.query_mos_op(x, temp_condition)
                    y_values = self.query_mos_op(y, temp_condition)

                    # now plot the results
                    if y_log:
                        plt.semilogy(x_values, y_values)
                    else:
                        plt.plot(x_values, y_values)

                legend = conditions[list(conditions.keys())[loop_condition]]

        else:

            # get the results
            x_values = self.collect_expression(x, conditions)
            y_values = self.collect_expression(y, conditions)

            # now plot the results
            if y_log:
                plt.semilogy(x_values, y_values)
            else:
                plt.plot(x_values, y_values)

            legend = None

        if legend:
            plt.legend(legend)
        plt.xlabel(x)
        plt.ylabel(y)
        plt.grid()

        if extra_plot_cmd:
            exec(extra_plot_cmd)

        plt.show()


    def integrated_noise(self, conditions, f_hi, f_lo=0.01):
        '''
            Calculate the integrated noise within the bandwidth
        '''

        def noise_calc(conditions):

            # collect noise information
            noise_corner  = self.query_mos_op('noise_corner',  conditions)
            noise_slope   = self.query_mos_op('noise_slope',   conditions)
            noise_thermal = self.query_mos_op('noise_thermal', conditions)

            ## calculate integrated noise
            
            # integrate the thermal noise
            noise = (f_hi - f_lo) * noise_thermal

            # integrate the flicker noise
            M = noise_thermal * noise_corner ** noise_slope
            noise += (M/(-noise_slope+1))*f_hi**(-noise_slope+1)
            noise += (M/( noise_slope-1))*f_lo**(-noise_slope+1)

            return noise

        noise = []
        if any([type(conditions[_])==list for _ in conditions]):
            loop_conditions = np.where([type(conditions[_])==list for _ in conditions])[0]
            for loop_condition in loop_conditions:
                for vary in conditions[list(conditions.keys())[loop_condition]]:

                    # create a copy with a single value in the sweep
                    temp_condition = copy.deepcopy(conditions)
                    temp_condition[list(conditions.keys())[loop_condition]] = vary
                    
                    # calculate noise
                    noise.append(noise_calc(temp_condition))       
        else:
            return noise_calc(conditions)


    def get_matching_value(self, original, matching, value, conditions):
        '''
            Given a given value in one parameter find the matching 
            value in another parameter
        '''

        original_list = self.query_mos_op(original, conditions=conditions)

        closest_index = min(range(len(original_list)), key=lambda i: abs(original_list[i]-value))

        return self.query_mos_op(matching, conditions=conditions)[closest_index]