


    def plot_dc_sweep(self, sweepvar, node, number_plots=1, linewidth=1.0, alpha=1.0, 
                        title=None, axis_titles=None, interactive=False, 
                        append=False, display=True):
        '''
            Plot a bode plot of the signal
        '''

        if not display:
            import matplotlib
            matplotlib.use('Agg')

        # get the results
        data = self.get_signal(node)
        sweep = self.get_signal(sweepvar)

        # create the plots
        with plt.style.context('seaborn-notebook'):
            
            # setup subplots
            if not self.plot_init:
                self.fig, self.axes = plt.subplots(ncols=1, nrows=number_plots, num='Histogram', squeeze=True)

                # set title
                if title:
                    self.fig.suptitle(title)    

                # set the axis titles
                if axis_titles:
                    self.axes.xlabel(axis_titles[0])
                    self.axes.ylabel(axis_titles[1])

                if interactive and display:
                    plt.ion()
                    plt.show()

                formatter = FuncFormatter(lambda y, _: '{:.16g}'.format(y))

            # calculate and plot the histogram
            self.axes.plot(sweep, data, linewidth=linewidth, alpha=alpha, color='b')

            # update the graph
            if display:
                if append:
                    plt.draw()
                    plt.pause(0.001)
                else:
                    plt.draw()
                    plt.pause(0.001)
                    plt.show()

        self.plot_init=True



    def plot_histogram(self, node, number_plots=1, number_bins=64, interactive=False, 
                        title=None, axis_titles=None, display=True, append=False):
        '''
            Plot a bode plot of the signal
        '''

        # get the results
        data = self.get_signal(node)[0]

        # store the data
        if not self.plot_init:
            self.data_arr = [data]
        else:
            self.data_arr += [data]

        # create the plots
        with plt.style.context('seaborn-notebook'):
            
            # setup subplots
            if not self.plot_init:
                self.fig, self.axes = plt.subplots(ncols=1, nrows=number_plots, num='Histogram', squeeze=True)

                if interactive and display:
                    plt.ion()
                    plt.show()

                formatter = FuncFormatter(lambda y, _: '{:.16g}'.format(y))

            # calculate and plot the histogram
            self.axes.cla()
            # n, bins, patches = self.axes.hist(self.data_arr, number_bins, density=1, color = "skyblue", ec="skyblue")
            n, bins, patches = self.axes.hist(self.data_arr, number_bins, density=1)

            # calculate the statistics
            mu = np.mean(self.data_arr)
            sigma = np.std(self.data_arr)

            # add a 'best fit' line
            y = ((1 / (np.sqrt(2 * np.pi) * sigma)) * np.exp(-0.5 * (1 / sigma * (bins - mu))**2))
            self.axes.plot(bins, y, '--')
            self.axes.set_xlabel('Value')
            self.axes.set_ylabel('Probability density')
            self.axes.set_title(r'Histogram. $\mu=%0.3f$, $\sigma=%0.3f$' % (mu, sigma))

            # update the graph
            if display:
                if append:
                    plt.draw()
                    plt.pause(0.001)
                else:
                    plt.draw()
                    plt.pause(0.001)
                    plt.show()

        self.plot_init=True



    def plot_bode(self, node, linewidth=1.0, alpha=1.0, interactive=False, append=False, 
                    title=None, display=True, save=False, invert=False):
        '''
            Plot a bode plot of the signal
        '''

        if not display:
            matplotlib.use('Agg')

        # get the results
        signal = self.get_signal(node, complex_out=True)
        frequency = self.get_signal('frequency')

        # convert the complex rectangular signal representation to magnitude and phase
        gain = [20*np.log10(_) for _ in np.abs(signal)]
        phase = [_*180/np.pi for _ in np.unwrap(np.angle(signal))]

        # get the stability margins
        phase_margin, gain_margin, unity_bandwidth, inverted_frequency = self.measure_phase_gain_margin(node, invert=invert)

        if not self.plot_init:
            self.phase_margin_arr = [phase_margin]
            self.gain_margin_arr = [gain_margin]
            self.unity_bandwidth_arr = [unity_bandwidth]
            self.inverted_frequency_arr = [inverted_frequency]
        else:
            self.phase_margin_arr += [phase_margin]
            self.gain_margin_arr += [gain_margin]
            self.unity_bandwidth_arr += [unity_bandwidth]
            self.inverted_frequency_arr += [inverted_frequency]

        # create the plots
        with plt.style.context('seaborn-notebook'):
            
            # setup subplots
            if not self.plot_init:
                self.fig, self.axes = plt.subplots(sharex='all', ncols=1, nrows=2, 
                                            num='Bode Plot', squeeze=True)

                # set title
                if title:
                    self.fig.suptitle(title)

                # if displaying the plot live update 
                if interactive and display:
                    plt.ion()
                    plt.show()

                # define the scale format
                formatter = FuncFormatter(lambda y, _: '{:.16g}'.format(y))
        
            # plot the gain
            self.axes[0].plot([_/1e6 for _ in frequency], gain, linewidth=linewidth, alpha=alpha, color='b')

            if not self.plot_init:
                self.axes[0].set_xscale('log')
                self.axes[0].set_ylabel('Magnitude (dB)')

                # setup the grids and markers how we want them
                locmaj = matplotlib.ticker.LogLocator(base=10,numticks=12) 
                self.axes[0].xaxis.set_major_locator(locmaj)
                locmin = matplotlib.ticker.LogLocator(base=10.0,subs=(0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9),numticks=12)
                self.axes[0].xaxis.set_minor_locator(locmin)
                self.axes[0].xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
                self.axes[0].xaxis.set_major_formatter(formatter)
                self.axes[0].grid(True, which="major", ls="-")
                self.axes[0].grid(True, which="minor", ls="--", alpha=0.5)
                
                # mark the gain margin point
                if inverted_frequency:
                    self.axes[0].axvline(x=inverted_frequency/1e6, linewidth=1, color='k', ls="--", alpha=0.75)

                # append the gain margin text
                if gain_margin:
                    self.text_gain_margin = self.axes[1].text(0.95, 0.95, "Gain Margin: %0.3f dB" % (gain_margin), horizontalalignment='right', verticalalignment='top', transform=self.axes[1].transAxes)

            else:
                self.text_phase_margin.set_text("Phase Margin: %0.3f (%0.3f/%0.3f) degrees" % (np.mean(self.phase_margin_arr), min(self.phase_margin_arr), max(self.phase_margin_arr)))


            # plot the phase
            self.axes[1].plot([_/1e6 for _ in frequency], phase, linewidth=linewidth, alpha=alpha, color='b')


            if not self.plot_init:
                self.axes[1].set_xscale('log')
                self.axes[1].set_xlabel('Frequency (MHz)')
                self.axes[1].set_ylabel('Phase (degrees)')

                # setup the grids and markers how we want them
                self.axes[1].xaxis.set_major_locator(locmaj)
                self.axes[1].xaxis.set_minor_locator(locmin)
                self.axes[1].xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
                self.axes[1].xaxis.set_major_formatter(formatter)
                self.axes[1].grid(True, which="major", ls="-")
                self.axes[1].grid(True, which="minor", ls="--", alpha=0.5)

                # mark the gain margin point
                if unity_bandwidth:
                    self.axes[1].axvline(x=unity_bandwidth/1e6, linewidth=1, color='k', ls="--", alpha=0.75)

                # append the phase margin text
                if phase_margin:
                    self.text_phase_margin = self.axes[1].text(0.95, 0.95, "Phase Margin: %0.3f degrees" % (phase_margin), horizontalalignment='right', verticalalignment='top', transform=self.axes[0].transAxes)

            else:
                self.text_gain_margin.set_text("Gain Margin: %0.3f (%0.3f/%0.3f) dB" % (np.mean(self.gain_margin_arr), min(self.gain_margin_arr), max(self.gain_margin_arr)))

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
                self.fig.savefig(save)

        self.plot_init=True



    def plot_ac(self, node, linewidth=1.0, alpha=1.0, interactive=False, append=False, 
                    title=None, display=True, save=False, invert=False):
        '''
            Plot a bode plot of the signal
        '''

        if not display:
            matplotlib.use('Agg')

        # get the results
        signal = self.get_signal(node, complex_out=True)
        frequency = self.get_signal('frequency')

        # convert the complex rectangular signal representation to magnitude and phase
        gain = [20*np.log10(_) for _ in np.abs(signal)]

        # get the ac ressponse measurements
        dc_gain, unity_bandwidth = self.measure_gain_bandwidth(node)

        if not self.plot_init:
            self.dc_gain_arr = [dc_gain]
            self.unity_bandwidth_arr = [unity_bandwidth]
        else:
            self.dc_gain_arr += [dc_gain]
            self.unity_bandwidth_arr += [unity_bandwidth]

        # create the plots
        with plt.style.context('seaborn-notebook'):
            
            # setup subplots
            if not self.plot_init:
                self.fig, self.axes = plt.subplots(sharex='all', ncols=1, nrows=1, 
                                            num='Bode Plot', squeeze=True)

                # set title
                if title:
                    self.fig.suptitle(title)

                # if displaying the plot live update 
                if interactive and display:
                    plt.ion()
                    plt.show()

                # define the scale format
                formatter = FuncFormatter(lambda y, _: '{:.16g}'.format(y))
        
            # plot the gain
            self.axes.plot([_/1e6 for _ in frequency], gain, linewidth=linewidth, alpha=alpha, color='b')

            if not self.plot_init:
                self.axes.set_xscale('log')
                self.axes.set_ylabel('Magnitude (dB)')

                # setup the grids and markers how we want them
                locmaj = matplotlib.ticker.LogLocator(base=10,numticks=12) 
                self.axes.xaxis.set_major_locator(locmaj)
                locmin = matplotlib.ticker.LogLocator(base=10.0,subs=(0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9),numticks=12)
                self.axes.xaxis.set_minor_locator(locmin)
                self.axes.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
                self.axes.xaxis.set_major_formatter(formatter)
                self.axes.grid(True, which="major", ls="-")
                self.axes.grid(True, which="minor", ls="--", alpha=0.5)
                

                # append the gain margin text
                if dc_gain:
                    self.text_dc_gain = self.axes.text(0.95, 0.95, "DC Gain: %0.3f dB" % (dc_gain), horizontalalignment='right', verticalalignment='top', transform=self.axes.transAxes)
                if unity_bandwidth:
                    self.text_unity_bandwidth = self.axes.text(0.95, 0.90, "Unity Bandwidth: %0.3f MHz" % (unity_bandwidth/1e6), horizontalalignment='right', verticalalignment='top', transform=self.axes.transAxes)

            else:
                self.text_dc_gain.set_text("DC Gain: %0.3f (%0.3f/%0.3f) dB" % (np.mean(self.dc_gain_arr), min(self.dc_gain_arr), max(self.dc_gain_arr)))
                self.text_unity_bandwidth.set_text("Unity Bandwidth: %0.3f (%0.3f/%0.3f) MHz" % (np.mean(self.unity_bandwidth_arr)/1e6, min(self.unity_bandwidth_arr)/1e6, max(self.unity_bandwidth_arr)/1e6))

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
                self.fig.savefig(save)

        self.plot_init=True
