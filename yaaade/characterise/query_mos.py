from yaaade.characterise.mos import QueryMos

query_obj = QueryMos('results/nmos_1p5.hdf5')

conditions = {  'l'     :   0.15e-6,
                'vbs'   :   0.00,
                'vds'   :   1.5}

query_obj.plot('gm', 'id', conditions)