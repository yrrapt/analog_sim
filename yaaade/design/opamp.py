

class FiveTransistorOTA():
    '''

    '''

    def __init__(self, device, specification):
        '''
            Setup the query object to retrieve characterisation info
        '''

        self.device = device
        self.specification = specification


    def design(self):
        '''
            Design the op-amp
        '''

        a_dc = 60       # dB
        f_u  = 10e6     # Hz
        C_l  = 10e-12   # F

        # let
        C_c = 1e-12

        gm1 = 2 * np.pi * f_u * C_c

        # gm7 = a_dc / (gm1 * (1/(gds1 + gds3)) * (1/(gds7 + gds8)))
        # a_dc = (gm1/gds1) * (gm7/gds7)
        (gm7/gds7) = a_dc / (gm1/gds1)

        gds3 = 0.1 * gds1
        gds8 = 0.1 * gds7

        # p1 = 1 / ( 2 * gm1 * RA * RB * Cc )
        # p1 = 1 / ( 2 * a_dc * Cc / gm7)

        # p2 = gm1 * Cc / 2 * Ca * Cl

        # p2 = 1.73 * fu = 1.73 / gm1 * 2pi * Cc = gm1 * Cc / 2 * Ca * Cl
        #
        # 1.73 * Ca * Cl = pi^2 * gm1^2 * Cc^2
        #
        # Cc = sqrt( 1.73 * Ca * Cl ) / (pi * gm1)
        #
        # gm1 / (2 * pi * fu) = sqrt( 1.73 * Ca * Cl ) / (pi * gm1)
        #
        # gm1^2 = 2 * fu * sqrt( 1.73 * Ca * Cl )



    