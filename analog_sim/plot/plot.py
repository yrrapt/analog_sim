import numpy as np

import matplotlib.pyplot as plt
import matplotlib.ticker
import matplotlib
from matplotlib.ticker import FuncFormatter

from analog_sim.measure.measure import *


def plot_dc_sweep(object, sweepvar, node, number_plots=1, linewidth=1.0, alpha=1.0, 
                    title=None, axis_titles=None, interactive=False, 
                    append=False, display=True):
    '''
        Plot a bode plot of the signal
    '''

    if not display:
        import matplotlib
        matplotlib.use('Agg')

    # get the results
    data = object.get_signal(node)
    sweep = object.get_signal(sweepvar)

    # create the plots
    with plt.style.context('seaborn-notebook'):
        
        # setup subplots
        if not object.plot_init:
            object.fig, object.axes = plt.subplots(ncols=1, nrows=number_plots, num='Histogram', squeeze=True)

            # set title
            if title:
                object.fig.suptitle(title)    

            # set the axis titles
            if axis_titles:
                object.axes.xlabel(axis_titles[0])
                object.axes.ylabel(axis_titles[1])

            if interactive and display:
                plt.ion()
                plt.show()

            formatter = FuncFormatter(lambda y, _: '{:.16g}'.format(y))

        # calculate and plot the histogram
        object.axes.plot(sweep, data, linewidth=linewidth, alpha=alpha, color='b')

        # update the graph
        if display:
            if append:
                plt.draw()
                plt.pause(0.001)
            else:
                plt.draw()
                plt.pause(0.001)
                plt.show()

    object.plot_init=True



def plot_histogram(object, node, number_plots=1, number_bins=64, interactive=False, 
                    title=None, axis_titles=None, display=True, append=False):
    '''
        Plot a bode plot of the signal
    '''

    # get the results
    data = object.get_signal(node)[0]

    # store the data
    if not object.plot_init:
        object.data_arr = [data]
    else:
        object.data_arr += [data]

    # create the plots
    with plt.style.context('seaborn-notebook'):
        
        # setup subplots
        if not object.plot_init:
            object.fig, object.axes = plt.subplots(ncols=1, nrows=number_plots, num='Histogram', squeeze=True)

            if interactive and display:
                plt.ion()
                plt.show()

            formatter = FuncFormatter(lambda y, _: '{:.16g}'.format(y))

        # calculate and plot the histogram
        object.axes.cla()
        # n, bins, patches = object.axes.hist(object.data_arr, number_bins, density=1, color = "skyblue", ec="skyblue")
        n, bins, patches = object.axes.hist(object.data_arr, number_bins, density=1)

        # calculate the statistics
        mu = np.mean(object.data_arr)
        sigma = np.std(object.data_arr)

        # add a 'best fit' line
        y = ((1 / (np.sqrt(2 * np.pi) * sigma)) * np.exp(-0.5 * (1 / sigma * (bins - mu))**2))
        object.axes.plot(bins, y, '--')
        object.axes.set_xlabel('Value')
        object.axes.set_ylabel('Probability density')
        object.axes.set_title(r'Histogram. $\mu=%0.3f$, $\sigma=%0.3f$' % (mu, sigma))

        # update the graph
        if display:
            if append:
                plt.draw()
                plt.pause(0.001)
            else:
                plt.draw()
                plt.pause(0.001)
                plt.show()

    object.plot_init=True



def plot_bode(object, node, linewidth=1.0, alpha=1.0, interactive=False, append=False, 
                title=None, display=True, save=False, invert=False):
    '''
        Plot a bode plot of the signal
    '''

    if not display:
        matplotlib.use('Agg')

    # get the results
    signal, units = object.get_signal(node, complex_out=True)
    frequency, units = object.get_signal('frequency')

    # convert the complex rectangular signal representation to magnitude and phase
    gain = [20*np.log10(_) for _ in np.abs(signal)]
    phase = [_*180/np.pi for _ in np.unwrap(np.angle(signal))]

    # get the stability margins
    phase_margin, gain_margin, unity_bandwidth, inverted_frequency = measure_phase_gain_margin(object, node, invert=invert)

    if not object.plot_init:
        object.phase_margin_arr = [phase_margin]
        object.gain_margin_arr = [gain_margin]
        object.unity_bandwidth_arr = [unity_bandwidth]
        object.inverted_frequency_arr = [inverted_frequency]
    else:
        object.phase_margin_arr += [phase_margin]
        object.gain_margin_arr += [gain_margin]
        object.unity_bandwidth_arr += [unity_bandwidth]
        object.inverted_frequency_arr += [inverted_frequency]

    # create the plots
    with plt.style.context('seaborn-notebook'):
        
        # setup subplots
        if not object.plot_init:
            object.fig, object.axes = plt.subplots(sharex='all', ncols=1, nrows=2, 
                                        num='Bode Plot', squeeze=True)

            # set title
            if title:
                object.fig.suptitle(title)

            # if displaying the plot live update 
            if interactive and display:
                plt.ion()
                plt.show()

            # define the scale format
            formatter = FuncFormatter(lambda y, _: '{:.16g}'.format(y))

        # plot the gain
        object.axes[0].plot([_/1e6 for _ in frequency], gain, linewidth=linewidth, alpha=alpha, color='b')

        if not object.plot_init:
            object.axes[0].set_xscale('log')
            object.axes[0].set_ylabel('Magnitude (dB)')

            # setup the grids and markers how we want them
            locmaj = matplotlib.ticker.LogLocator(base=10,numticks=12) 
            object.axes[0].xaxis.set_major_locator(locmaj)
            locmin = matplotlib.ticker.LogLocator(base=10.0,subs=(0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9),numticks=12)
            object.axes[0].xaxis.set_minor_locator(locmin)
            object.axes[0].xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
            object.axes[0].xaxis.set_major_formatter(formatter)
            object.axes[0].grid(True, which="major", ls="-")
            object.axes[0].grid(True, which="minor", ls="--", alpha=0.5)
            
            # mark the gain margin point
            if inverted_frequency:
                object.axes[0].axvline(x=inverted_frequency/1e6, linewidth=1, color='k', ls="--", alpha=0.75)

            # append the gain margin text
            # if gain_margin:
            #     object.text_gain_margin = object.axes[1].text(0.95, 0.95, "Gain Margin: %0.3f dB" % (gain_margin), horizontalalignment='right', verticalalignment='top', transform=object.axes[1].transAxes)

        else:
            object.text_phase_margin.set_text("Phase Margin: %0.3f (%0.3f/%0.3f) degrees" % (np.mean(object.phase_margin_arr), min(object.phase_margin_arr), max(object.phase_margin_arr)))


        # plot the phase
        object.axes[1].plot([_/1e6 for _ in frequency], phase, linewidth=linewidth, alpha=alpha, color='b')


        if not object.plot_init:
            object.axes[1].set_xscale('log')
            object.axes[1].set_xlabel('Frequency (MHz)')
            object.axes[1].set_ylabel('Phase (degrees)')

            # setup the grids and markers how we want them
            object.axes[1].xaxis.set_major_locator(locmaj)
            object.axes[1].xaxis.set_minor_locator(locmin)
            object.axes[1].xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
            object.axes[1].xaxis.set_major_formatter(formatter)
            object.axes[1].grid(True, which="major", ls="-")
            object.axes[1].grid(True, which="minor", ls="--", alpha=0.5)

            # mark the gain margin point
            if unity_bandwidth:
                object.axes[1].axvline(x=unity_bandwidth/1e6, linewidth=1, color='k', ls="--", alpha=0.75)

            # append the phase margin text
            if phase_margin:
                object.text_phase_margin = object.axes[1].text(0.95, 0.95, "Phase Margin: %0.3f degrees" % (phase_margin), horizontalalignment='right', verticalalignment='top', transform=object.axes[0].transAxes)

        # else:
        #     object.text_gain_margin.set_text("Gain Margin: %0.3f (%0.3f/%0.3f) dB" % (np.mean(object.gain_margin_arr), min(object.gain_margin_arr), max(object.gain_margin_arr)))

        # append to existing plot?
        if display:
            if append:
                plt.draw()
                plt.pause(0.001)
            else:
                plt.draw()
                plt.pause(0.001)
                plt.show()

        # save the plot to file
        if save:
            object.fig.savefig(save)

    object.plot_init=True



def plot_ac(object, node, linewidth=1.0, alpha=1.0, interactive=False, append=False, 
                title=None, display=True, save=False, invert=False):
    '''
        Plot a bode plot of the signal
    '''

    if not display:
        matplotlib.use('Agg')

    # get the results
    signal = object.get_signal(node, complex_out=True)
    frequency = object.get_signal('frequency')

    # convert the complex rectangular signal representation to magnitude and phase
    gain = [20*np.log10(_) for _ in np.abs(signal)]

    # get the ac ressponse measurements
    dc_gain, unity_bandwidth = object.measure_gain_bandwidth(node)

    if not object.plot_init:
        object.dc_gain_arr = [dc_gain]
        object.unity_bandwidth_arr = [unity_bandwidth]
    else:
        object.dc_gain_arr += [dc_gain]
        object.unity_bandwidth_arr += [unity_bandwidth]

    # create the plots
    with plt.style.context('seaborn-notebook'):
        
        # setup subplots
        if not object.plot_init:
            object.fig, object.axes = plt.subplots(sharex='all', ncols=1, nrows=1, 
                                        num='Bode Plot', squeeze=True)

            # set title
            if title:
                object.fig.suptitle(title)

            # if displaying the plot live update 
            if interactive and display:
                plt.ion()
                plt.show()

            # define the scale format
            formatter = FuncFormatter(lambda y, _: '{:.16g}'.format(y))
    
        # plot the gain
        object.axes.plot([_/1e6 for _ in frequency], gain, linewidth=linewidth, alpha=alpha, color='b')

        if not object.plot_init:
            object.axes.set_xscale('log')
            object.axes.set_ylabel('Magnitude (dB)')

            # setup the grids and markers how we want them
            locmaj = matplotlib.ticker.LogLocator(base=10,numticks=12) 
            object.axes.xaxis.set_major_locator(locmaj)
            locmin = matplotlib.ticker.LogLocator(base=10.0,subs=(0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9),numticks=12)
            object.axes.xaxis.set_minor_locator(locmin)
            object.axes.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
            object.axes.xaxis.set_major_formatter(formatter)
            object.axes.grid(True, which="major", ls="-")
            object.axes.grid(True, which="minor", ls="--", alpha=0.5)
            

            # append the gain margin text
            if dc_gain:
                object.text_dc_gain = object.axes.text(0.95, 0.95, "DC Gain: %0.3f dB" % (dc_gain), horizontalalignment='right', verticalalignment='top', transform=object.axes.transAxes)
            if unity_bandwidth:
                object.text_unity_bandwidth = object.axes.text(0.95, 0.90, "Unity Bandwidth: %0.3f MHz" % (unity_bandwidth/1e6), horizontalalignment='right', verticalalignment='top', transform=object.axes.transAxes)

        else:
            object.text_dc_gain.set_text("DC Gain: %0.3f (%0.3f/%0.3f) dB" % (np.mean(object.dc_gain_arr), min(object.dc_gain_arr), max(object.dc_gain_arr)))
            object.text_unity_bandwidth.set_text("Unity Bandwidth: %0.3f (%0.3f/%0.3f) MHz" % (np.mean(object.unity_bandwidth_arr)/1e6, min(object.unity_bandwidth_arr)/1e6, max(object.unity_bandwidth_arr)/1e6))

        # append to existing plot?
        if display:
            if append:
                plt.draw()
                plt.pause(0.001)
            else:
                plt.draw()
                plt.pause(0.001)
                plt.show()

        # save the plot to file
        if save:
            object.fig.savefig(save)

    object.plot_init=True


def plot_tran(object, signals, linewidth=1.0, alpha=1.0, interactive=False, append=False, 
                title=None, display=True, save=False, invert=False):
    '''
        Plot transient signal(s)
    '''

    if not display:
        matplotlib.use('Agg')


    data = object.get_signals(signals, complex_out=True)
    time,   time_units     = object.get_signal('time')

    # create the plots
    with plt.style.context('seaborn-notebook'):
        
        # setup subplots
        if not object.plot_init:
            object.fig, object.axes = plt.subplots(sharex='all', ncols=1, nrows=len(signals), 
                                        num='Transient Plot', squeeze=True)

            # set title
            if title:
                object.fig.suptitle(title)

            # if displaying the plot live update 
            if interactive and display:
                plt.ion()
                plt.show()

            # define the scale format
            formatter = FuncFormatter(lambda y, _: '{:.16g}'.format(y))
    
        # plot the signal(s)
        for subplot, signal in enumerate(data):
            object.axes[subplot].plot(time, data[signal][0], linewidth=linewidth, alpha=alpha, color='b')
            object.axes[subplot].set_ylabel(signal + ' ('+ data[signal][1].capitalize() + ')')
            # object.axes[subplot].set_title(signal)

        # append to existing plot?
        if display:
            if append:
                plt.draw()
                plt.pause(0.001)
            else:
                plt.draw()
                plt.pause(0.001)
                plt.show()

        # save the plot to file
        if save:
            object.fig.savefig(save)

    object.plot_init=True