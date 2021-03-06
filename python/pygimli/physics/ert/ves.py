# -*- coding: utf-8 -*-
"""
Vertical electrical sounding (VES) manager class.
"""
import numpy as np
import matplotlib.pyplot as plt

import pygimli as pg
from pygimli.mplviewer import drawModel1D


class VESManager():
    """
    Vertical electrical sounding (VES) manager class.
    """
    def __init__(self,
                 ab2,
                 z,
                 mn2=None,
                 Type='smooth',
                 verbose=False):
        """
        parameters:
        -----------

        ab2: array_like
            Vector of distances between the point of the sounding and the
            current electrodes.

        mn2: array_like [ab2/3]
            Vector of distances between the point of the sounding and the
            potential electrodes.

        z: array_like, case specific
            smooth: z discretisation [m]\n
            block: number of layers
        """
        self.verbose = verbose
        self.type = Type

        self.ab2 = ab2

        self.mn2 = mn2
        if mn2 is None:
            self.mn2 = ab2/3

        self.Z = z  # z discretisation or nlay

        self.FOP = None
        self.INV = None
        self.startmodel = None

        self.createModelTrans()  # creates default as fallback

    def createFOP(self):
        """Creates the forward operator instance."""
        if self.type == 'block':
            self.FOP = pg.DC1dModelling(self.Z, self.ab2, self.mn2)
            mesh1D = pg.createMesh1DBlock(self.Z)

        if self.type == 'smooth':
            self.FOP = pg.DC1dRhoModelling(self.Z, self.ab2, self.mn2)
            mesh1D = pg.createMesh1D(nCells=len(self.Z) + 1)

        self.FOP.setMesh(mesh1D)
        self.applyModelTrans()

    @staticmethod
    def simulate(synmodel, ab2=None, mn2=None, errPerc=3.):
        """
        Simulates a synthetic data set of a vertical electric sounding and
        appends gaussian distributed noise.
        Block only for now.

        Parameters
        ----------

        ab2: array_like
            Vector of distances between the point of the sounding and the
            current electrodes.

        mn2: array_like [ab2/3]
            Vector of distances between the point of the sounding and the
            potential electrodes.

        errPerc: float [3.]
            Percentage Value for the gaussian noise. Default are 3 %.

        Example
        -------

        >>> from pygimli.physics import VESManager as VES
        >>> import numpy as np
        >>> ab2 = np.logspace(-1, 2, 25)
        >>> mn2 = ab2/3
        >>> synModel = [[4, 6, 10], [100., 500., 20., 800.]]
        >>> # 3 layer with 100, 500 and 20 Ohmm
        >>> # and layer thickness of 4, 6, 10 m
        >>> # over a Halfspace of 800 Ohmm
        >>> testData = VES.simulate(synModel, ab2, mn2, errPerc=3.)
        """
        thk = synmodel[0]
        res = synmodel[1]
        if mn2 is None:
            mn2 = ab2/3
        FOP = pg.DC1dModelling(len(res), ab2, mn2)
        syndata = FOP.response(thk + res)
        syndata = syndata * (pg.randn(len(syndata)) * errPerc / 100. + 1.)
        return syndata

    def createINV(self, data, relErrorP=3., startmodel=None, **kwargs):
        """
        parameters:
        -----------

        data: array_like
            Data array you would like to fit with this inverse modelling
            approach.

        relErrorP: float [3.]
            Percentage value of the relative error you assume. Default 3. means
            a 3 % error is assumed. Affects the chi2 criteria during the
            inversion process and therefore the inversion result (Inversion
            tries to fit the given data within the given errors).

        startmodel: array_like [None]
            Optional possibility to define the starting model for the inversion
            routine. The default will be the mean of the given data.

        additional keyword arguments:
        -----------------------------

        Keyword arguments are redirected to the block inversion instance only!

        lambdaFactor: float < 1.0 [0.8]
            Inversion in Marquardt scheme reduces the lambda from initial high
            values down to a certain minimum. The reduction per step is
            represented by this value. Default is a reduction to 80% of the
            previous step (By the way, the default start lambda is 1000).

        robust: boolean [False]
            Recalculation of the errors to reduce the weight of spikes in the
            data. Not necessary for synthetic or "good" field data.
        """
        if self.FOP is None:
            self.createFOP()

        self.INV = pg.RInversion(data,
                                 self.FOP,
                                 False)

        self.applyDataTrans()

        if self.type == 'block':
            print(kwargs.pop('lambdaFactor'))
            self.INV.setMarquardtScheme(kwargs.pop('lambdaFactor', 0.8))
            self.INV.setRobustData(kwargs.pop('robust', False))

        if self.type == 'smooth':
            pass

        self.INV.setRelativeError(relErrorP / 100.0)

        if startmodel is not None:
            self.startmodel = startmodel

        if self.startmodel is None:
            self.createStartModel(data)

        if self.type == 'smooth':
            self.INV.setModel(self.startmodel)

        else:
            self.FOP.region(0).setStartValue(self.startmodel[0])
            self.FOP.region(1).setStartValue(self.startmodel[1])

    def createModelTrans(self,
                         thkBounds=[10., 0.1, 30.],
                         modelBounds=[10, 1.0, 10000.],
                         trans=['log', 'log']):
        """Defines the transformation for the model."""
        self.thkBounds = thkBounds  # thk(start, min, max)
        self.rhoBounds = modelBounds  # rho (model) (start, min, max)
        self.trans = trans
        if self.FOP is not None:
            self.applyModelTrans()

    def applyModelTrans(self):
        """
        Append the previously given bounaries for the model transformation
        to the forward operator.
        """
        if self.FOP is None:
            raise Exception('initialize forward operator before appending proper \
boundaries for the model transformation')

        if self.type == 'smooth':

            self.FOP.region(0).setParameters(self.rhoBounds[0],
                                             self.rhoBounds[1],
                                             self.rhoBounds[2], self.trans[1])
        elif self.type == 'block':

            self.FOP.region(0).setParameters(self.thkBounds[0],
                                             self.thkBounds[1],
                                             self.thkBounds[2], self.trans[0])

            self.FOP.region(1).setParameters(self.rhoBounds[0],
                                             self.rhoBounds[1],
                                             self.rhoBounds[2], self.trans[1])

    def applyDataTrans(self):
        """Apply a logarithmic transformation to the data."""
        self.dataTrans = pg.RTransLog()
        self.INV.setTransData(self.dataTrans)

    def createStartModel(self, data):
        """Creates a default start model for the inversion."""
        if self.type == 'smooth':
            self.startmodel = pg.RVector(len(self.Z) + 1, np.median(data))
        else:
            self.startmodel = [self.getDepth() / self.Z / 2, np.median(data)]

    def invert(self, data, startmodel=None, relErrorP=3., lam=None, **kwargs):
        """
        Creates forward operator, initializes inversion scheme and run
        inversion based on the input parameters. kwargs are redirected to
        the createINV method.
        """
        self.dataToFit = data
        if self.INV is None:
            self.createINV(data,
                           relErrorP=relErrorP,
                           startmodel=startmodel,
                           **kwargs)

        if self.type == 'smooth' and lam is None:
            self.resDistribution = self.INV.runChi1()

        else:
            if lam is None:
                lam = 1000.0
            self.INV.setLambda(lam)
            self.resDistribution = self.INV.run()

        if self.verbose is False:
            self.INV.echoStatus()
        return self.resDistribution

    def splitBlockModel(self):
        """Returns the thickness and ressitivities of the model."""
        z = int(self.Z) - 1
        return self.resDistribution[:z], self.resDistribution[z:]

    def getDepth(self):
        """Rule-of-thumb for Wenner/Schlumberger."""
        return np.max(self.ab2) / 3.  # rule-of-thumb for Wenner/Schlumberger

    def showResults(self, ax=None, syn=None, color=None):
        """Shows the Results of the inversion."""
        if ax is None:
            fig, ax = plt.subplots(ncols=1, figsize=(8, 6))
        if syn is not None:
            drawModel1D(ax, syn[0], syn[1], color='b', label='synthetic',
                        plotfunction='semilogx')
        if color is None:
            color = 'g'
        if self.type == 'smooth':
            drawModel1D(ax, self.Z, self.resDistribution, color=color,
                        label=r'$\lambda$={:2.2f}'
                        .format(self.INV.getLambda()))
        else:
            thk, rho = self.splitBlockModel()
            drawModel1D(ax, thk, rho, color=color,
                        label=r'$\ chi^2$={:2.2f}'
                        .format(self.INV.getChi2()))
        ax.grid(True, which='both')
        ax.legend(loc='best')
        return ax

    def showFit(self, ax=None, color='g', marker='-', syn=True):
        """Visualizes the data fit."""
        if syn is True:
            ax.loglog(self.dataToFit, self.ab2, 'bx-',
                      label='measured/synthetic')
        ax.loglog(self.INV.response(), self.ab2, color, label='fitted')
        ax.set_ylim((max(self.ab2), min(self.ab2)))
        ax.grid(True, which='both')
        ax.set_xlabel(r'$\rho_a$ [$\Omega$m]')
        ax.set_ylabel('AB/2 [m]')
        ax.legend(loc='best')
        return ax

    def showResultsAndFit(self, syn=None):
        """Calls showResults and showFit."""
        fig, ax = plt.subplots(ncols=2, figsize=(8, 6))
        self.showResults(ax=ax[0], syn=syn)
        self.showFit(ax=ax[1])

if __name__ == '__main__':
    pass

# The End
