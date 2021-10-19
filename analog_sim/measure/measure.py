import numpy as np


def measure_max(object, signal):
    '''
        Find the max value and associated sweep point
    '''

    signal_value = object.get_signal(signal)
    sweep_value = object.get_swept_values()
    
    return [sweep_value[signal_value.index(max(signal_value))], max(signal_value)]
    


def measure_frequency(object, node, netlist=None, measure_after_factor=None, threshold=0.9, hysteresis=0.05, method='fft'):
    '''
        Measure the frequency from time domain signal
    '''

    # extract each data point and convert to real list
    data_real = object.get_signal('v('+node+')')
    analysis_time = object.get_signal('time')


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



def measure_gain_bandwidth(object, node):
    '''
        Measure the gain and unity gain frequency
    '''

    # grab the signal
    fb = object.get_signal(node, complex_out=True)
    frequency = object.get_signal('frequency')

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



def measure_phase_gain_margin(object, node, alert=True, invert=False):
    '''
        Measure the phase and gain stability margins
    '''

    # grab the signal
    fb = object.get_signal(node, complex_out=True)
    frequency = object.get_signal('frequency')

    # convert the complex rectangular signal representation to magnitude and phase
    gain = [20*np.log10(_) for _ in np.abs(fb[0])]
    phase = [_*180/np.pi for _ in np.unwrap(np.angle(fb[0]))]

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
    if alert and hasattr(object, 'limits'):
        if phase_margin:
            if phase_margin < object.limits['phase_margin']:
                print("WARNING: Phase margin is %0.3f degrees" % phase_margin)
        else:
            print("WARNING: Phase margin not found")

        if gain_margin:
            if gain_margin < object.limits['gain_margin']:
                print("WARNING: Gain margin is %0.3f dB" % gain_margin)
        else:
            print("WARNING: Gain margin not found")

    return phase_margin, gain_margin, unity_bandwidth, inverted_frequency



def measure_noise(frequency=None, noise=None):
# def measure_noise():
    '''
        Measure the corner frequency, slope factor of flicker noise and the thermal noise from simulation data 
    '''

    # get the signals to measure
    if not frequency.all():
        frequency = object.get_signal('frequency', dataset='noise')
    
    if not noise.all():
        noise = object.get_signal('onoise_spectrum', dataset='noise')

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


def read_clocked_data(object, clock, data, edge='rising', binary=True):
    '''
        Given a signal and a clock detect find the value on the clock edge
    '''

    # get the signals
    clock_signal = object.get_signal(clock)[0]

    # multiple signals can be provided
    if type(data) == list:
        data_signal = []
        for signal in data:
            data_signal.append(object.get_signal(signal)[0])
    else:
        data_signal = object.get_signal(data)[0]

    # find the min/max of the clock signal
    clock_min = min(clock_signal)
    clock_max = max(clock_signal)
    clock_threshold = 0.5*(clock_max - clock_min) + clock_min

    # find the thresholds of the data signals
    if type(data) == list:
        data_threshold = []
        for signal in data:
            data_min = min(data_signal)
            data_max = max(data_signal)
            data_signal.append(0.5*(data_max - data_min) + data_min)
    else:
        data_min = min(data_signal)
        data_max = max(data_signal)
        data_threshold = 0.5*(data_max - data_min) + data_min

    time = object.get_signal('time')[0]

    # now find clock transitions and save output data
    output_data = []
    for n in range(1, len(clock_signal)):

        # detect an edge
        if edge == 'rising':
            if (clock_signal[n-1] < clock_threshold) and (clock_signal[n] >= clock_threshold):
                edge_detected = True
            else:
                edge_detected = False

        else:
            if (clock_signal[n-1] > clock_threshold) and (clock_signal[n] <= clock_threshold):
                edge_detected = True
            else:
                edge_detected = False

        # save the data
        if edge_detected:

            # multiple signals can be provided
            if type(data_signal[0]) == list:
                samples = []
                for i, signal in enumerate(data_signal):
                    if binary:
                        samples.append(int(signal[n] > data_threshold[i]))
                    else:
                        samples.append(signal[n])
                output_data.append(samples)

            # or a signalur signal
            else:
                if binary:
                    output_data.append(int(data_signal[n] > data_threshold))
                else:
                    output_data.append(data_signal[n])

    return output_data

