import numpy as np


class Measure():
    '''

    '''

    def __init__(self, sim):
        '''
            Create the object 
        '''

        self.sim = sim


    def measure_max(self, signal):
        '''
            Find the max value and associated sweep point
        '''

        signal_value = self.sim.get_signal(signal)
        sweep_value = self.sim.get_swept_values()
        
        return [sweep_value[signal_value.index(max(signal_value))], max(signal_value)]
        


    def measure_frequency(self, node, netlist=None, measure_after_factor=None, threshold=0.9, hysteresis=0.05, method='fft'):
        '''
            Measure the frequency from time domain signal
        '''

        # extract each data point and convert to real list
        data_real = self.sim.get_signal('v('+node+')')
        analysis_time = self.sim.get_signal('time')


        # trim the data
        if measure_after_factor:
            data_real = data_real[int(len(data_real)*measure_after_factor):]
            analysis_time = analysis_time[int(len(data_real)*measure_after_factor):]

        # define the high and low thresholds for calculating edges
        threshold_low = threshold - hysteresis
        threshold_high = threshold + hysteresis

        # find first rising edge
        for i in range(2,len(data_real)):
            if (float(data_real[i]) > threshold) and (float(data_real[i-1]) > threshold) and (float(data_real[i-2]) < threshold):
                first_index = i
                first_time = analysis_time[i]
                break

        # find second rising edge
        for i in range(first_index+3, len(data_real)):
            if (float(data_real[i]) > threshold) and (float(data_real[i-1]) > threshold) and (float(data_real[i-2]) < threshold):
                second_index = i
                second_time = analysis_time[i]
                break

        # find third rising edge
        for i in range(second_index+3, len(data_real)):
            if (float(data_real[i]) > threshold) and (float(data_real[i-1]) > threshold) and (float(data_real[i-2]) < threshold):
                third_index = i
                third_time = analysis_time[i]
                break

        return 1.0/(third_time-second_time)



    def measure_gain_bandwidth(self, node):
        '''
            Measure the gain and unity gain frequency
        '''

        # grab the signal
        fb = self.sim.get_signal(node, complex_out=True)
        frequency = self.sim.get_signal('frequency')

        # convert the complex rectangular signal representation to magnitude and phase
        gain = [20*np.log10(_) for _ in np.abs(fb)]
        phase = [_*180/np.pi for _ in np.unwrap(np.angle(fb))]

        # find the dc gain
        dc_gain = gain[0]

        # find the unity bandwidth
        try:
            unity_bandwidth = frequency[np.where(np.diff(np.sign(gain)))[0][0]+1]
        except:
            unity_bandwidth = None

        return dc_gain, unity_bandwidth



    def measure_phase_gain_margin(self, node, alert=True, invert=False):
        '''
            Measure the phase and gain stability margins
        '''

        # grab the signal
        fb = self.sim.get_signal(node, complex_out=True)
        frequency = self.sim.get_signal('frequency')

        # convert the complex rectangular signal representation to magnitude and phase
        gain = [20*np.log10(_) for _ in np.abs(fb)]
        phase = [_*180/np.pi for _ in np.unwrap(np.angle(fb))]

        # invert the phase response
        if invert:
            phase = [_+360 for _ in phase]

        # find phase margin
        try:
            unity_bandwidth = frequency[np.where(np.diff(np.sign(gain)))[0][0]+1]
        except:
            unity_bandwidth = None

        try:
            phase_margin = phase[np.where(np.diff(np.sign(gain)))[0][0]+1]
        except:
            phase_margin = None

        # find the gain margin
        try:
            inverted_frequency = frequency[np.where(np.diff(np.sign([_+180 for _ in phase])))[0][0]+1]
        except:
            inverted_frequency = None
        
        try:
            gain_margin = -gain[np.where(np.diff(np.sign([_+180 for _ in phase])))[0][0]+1]
        except:
            gain_margin = None

        # warn user that margins are low
        if alert:
            if phase_margin:
                if phase_margin < self.limits['phase_margin']:
                    print("WARNING: Phase margin is %0.3f degrees" % phase_margin)
            else:
                print("WARNING: Phase margin not found")

            if gain_margin:
                if gain_margin < self.limits['gain_margin']:
                    print("WARNING: Gain margin is %0.3f dB" % gain_margin)
            else:
                print("WARNING: Gain margin not found")

        return phase_margin, gain_margin, unity_bandwidth, inverted_frequency



    # def measure_noise(frequency, noise):
    def measure_noise():
        '''
            Measure the corner frequnecy, slope factor of flicker noise and the thermal noise from simulation data 
        '''

        # get the signals to measure
        frequency = self.sim.get_signal('frequency', dataset='noise1')
        noise = self.sim.get_signal('noise_spectrum', dataset='noise1')
        length = len(frequency)

        # create theoretical flicker noise
        flicker_factor = 1.5
        flicker = [float(noise[0])]
        for i in range(1, length):
            flicker.append( noise[0]/(np.sqrt(frequency[i]**flicker_factor) ) )

        # create theoretical thermal noise
        thermal = [float(noise[-1])]*length
        derivative = [1.0]
        for n in range(1,length):
            derivative.append(noise[n-1]-noise[n])

            if derivative[-1] > derivative[-2]:
                thermal = [float(noise[n])]*length
                break

        # find current corner frequency
        corner_index = None
        for i in range(length):
            if flicker[i]-thermal[i] < 0:
                corner_index = i
                break

        if corner_index:

            # adjust flicker factor
            while flicker[int(corner_index*0.5)]-noise[int(corner_index*0.5)] < 0:

                # decrement the flicker factor and retest
                flicker_factor -= 0.001
                flicker = [float(noise[0])]
                for i in range(1, length):
                    flicker.append( noise[0]/(np.sqrt(frequency[i]**flicker_factor) ) )

            # find the final corner frequency
            for i in range(length):
                if flicker[i]-thermal[i] < 0:
                    corner_index = i
                    corner_frequency = frequency[corner_index]
                    break

        else:
            corner_frequency = None
            flicker_factor = None
    

        return thermal[0], corner_frequency, flicker_factor

