from PyQt5 import QtWidgets, uic
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import sys
from analog_sim.characterise.mos import QueryMos


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')


        #Load the UI Page
        uic.loadUi('mainwindow.ui', self)

        self.plot()

    def plot(self):



        # p1 = self.graphWidget.plot()
        pw = self.graphWidget
        # p1 = pw.plot(pen=(0, 0, 0))
        p1 = pw.plot()

        # vb = pw.getViewBox()
        # vb.setBackgroundColor('w')


        query_obj = QueryMos('../../__development/results/sky130_fd_pr__nfet_01v8.hdf5')
        l = query_obj.get_parameter_values('l')
        for l_i in l:

            conditions = {  'l'     :   l_i,
                            'vbs'   :   0.00,
                            'vds'   :   5.00}

            id = [_ for _ in query_obj.query_mos_op('id', conditions)]
            gm = [_ for _ in query_obj.query_mos_op('gm', conditions)]
            gds = [_ for _ in query_obj.query_mos_op('gds', conditions)]
            vgs = [_ for _ in query_obj.query_mos_op('vgs', conditions)]
            vdsat = [_ for _ in query_obj.query_mos_op('vdsat', conditions)]
            noise_thermal = [_ for _ in query_obj.query_mos_op('noise_thermal', conditions)]
            noise_corner = [_ for _ in query_obj.query_mos_op('noise_corner', conditions)]

        x = [gm[_]/id[_] for _ in range(len(gm))]
        y = [gm[_]/gds[_] for _ in range(len(gm))]

        p1.setData(x=x, y=y, pen=pg.mkPen('k', width=2))

        # plt.semilogy([gm[_]/id[_] for _ in range(len(gm))], [gm[_]/gds[_] for _ in range(len(gm))])

        pw.setLabel('left', 'Value', units='V')
        pw.setLabel('bottom', 'Time', units='s')
        # pw.setXRange(0, 2)
        # pw.setYRange(0, 1e-10)

        ay = pw.getAxis('left')  # This is the trick

        # ay.setTickSpacing(1,0.1)
        # # # dy = [(value, str(value)) for value in list((range(int(min(y)), int(max(y)+1))))]
        dy = [1, 2, 3, 4, 5]
        dy_m = [0.1, 0.2, 0.3, 0.4, 0.5]
        # print('dy', dy)
        # ay.setTicks([dy, dy_m])
        ay.setTicks([[(v, str(v)) for v in dy], [(v, str(v)) for v in dy_m]])

        pw.setLogMode(False, True)
        pw.showGrid(x=True, y=True, alpha=0.5)


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())



if __name__ == '__main__':         
    main()