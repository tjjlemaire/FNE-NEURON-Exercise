# -*- coding: utf-8 -*-
# @Author: Theo Lemaire
# @Email: theo.lemaire@epfl.ch
# @Date:   2019-06-05 14:08:31
# @Last Modified by:   Theo Lemaire
# @Last Modified time: 2021-02-12 17:30:16

from neuron import h
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from .Cell import Cell
from ..utils import load_mechanisms, getNmodlDir


class MyelinatedFiber(Cell):
    """ Neuron Biophysical myelinated fiber model.

    The model integrates an axon model developed by McIntyre 2002.
    This extends the McIntyre model to allow any diameter to be used
    """

    def __init__(self, diameter=5):
        """ Object initialization.

        Keyword arguments:
        diameter -- fiber diameter in micrometers [3-20]
        """

        load_mechanisms(getNmodlDir())

        Cell.__init__(self)

        self._init_parameters(diameter)
        self._create_sections()
        self._build_topology()
        self._define_biophysics()

    def __repr__(self):
        return f'{self.__class__.__name__}({self.fiberD:.1f}um)'

    def __del__(self):
        """ Object destruction. """
        Cell.__del__(self)

    """
    Specific Methods of this class
    """

    def interpolate(self, x, y):
        # return np.poly1d(np.polyfit(x, y, 3))
        return interp1d(x, y, kind='linear', assume_sorted=True, fill_value='extrapolate')

    def _init_parameters(self, diameter):
        """ Initialize all cell parameters. """

        # topological parameters
        self.nNodes = 101
        self._axonNodes = self.nNodes
        self._paraNodes1 = 2 * (self.nNodes - 1)
        self._paraNodes2 = 2 * (self.nNodes - 1)
        self._axonInter = 6 * (self.nNodes - 1)
        self.axonTotal = self.nNodes + self._paraNodes1 + self._paraNodes2 + self._axonInter

        # morphological parameters
        self.fiberD = diameter
        self._paraLength1 = 3
        self._nodeLength = 1.0
        self._spaceP1 = 0.002
        self._spaceP2 = 0.004
        self._spaceI = 0.004

        # electrical parameters
        self._rhoa = 0.7e6  # Ohm-um
        self._mycm = 0.1  # uF/cm2/lamella membrane
        self._mygm = 0.001  # S/cm2/lamella membrane

        # fit the parameters with polynomials to allow any diameter
        experimentalDiameters = [5.7, 7.3, 8.7, 10.0, 11.5, 12.8, 14.0, 15.0, 16.0]
        experimentalAxonD = [3.4, 4.6, 5.8, 6.9, 8.1, 9.2, 10.4, 11.5, 12.7]
        experimentalNodeD = [1.9, 2.4, 2.8, 3.3, 3.7, 4.2, 4.7, 5.0, 5.5]
        experimentalParaD1 = [1.9, 2.4, 2.8, 3.3, 3.7, 4.2, 4.7, 5.0, 5.5]
        experimentalParaD2 = [3.4, 4.6, 5.8, 6.9, 8.1, 9.2, 10.4, 11.5, 12.7]
        experimentalDeltaX = [500, 750, 1000, 1150, 1250, 1350, 1400, 1450, 1500]
        experimentalParaLength2 = [35, 38, 40, 46, 50, 54, 56, 58, 60]
        experimentalNl = [80, 100, 110, 120, 130, 135, 140, 145, 150]

        # interpolate
        fit_axonD = self.interpolate(experimentalDiameters, experimentalAxonD)
        fit_nodeD = self.interpolate(experimentalDiameters, experimentalNodeD)
        fit_paraD1 = self.interpolate(experimentalDiameters, experimentalParaD1)
        fit_paraD2 = self.interpolate(experimentalDiameters, experimentalParaD2)
        fit_deltax = self.interpolate(experimentalDiameters, experimentalDeltaX)
        fit_paraLength2 = self.interpolate(experimentalDiameters, experimentalParaLength2)
        fit_nl = self.interpolate(experimentalDiameters, experimentalNl)

        self._axonD = fit_axonD(self.fiberD)
        self._nodeD = fit_nodeD(self.fiberD)
        self._paraD1 = fit_paraD1(self.fiberD)
        self._paraD2 = fit_paraD2(self.fiberD)
        self._deltax = fit_deltax(self.fiberD)
        self._paraLength2 = fit_paraLength2(self.fiberD)
        self._nl = fit_nl(self.fiberD)

        self._Rpn0 = (self._rhoa * .01) / \
            (np.pi * ((((self._nodeD / 2) + self._spaceP1)**2) - ((self._nodeD / 2)**2)))
        self._Rpn1 = (self._rhoa * .01) / \
            (np.pi * ((((self._paraD1 / 2) + self._spaceP1)**2) - ((self._paraD1 / 2)**2)))
        self._Rpn2 = (self._rhoa * .01) / \
            (np.pi * ((((self._paraD2 / 2) + self._spaceP2)**2) - ((self._paraD2 / 2)**2)))
        self._Rpx = (self._rhoa * .01) / \
            (np.pi * ((((self._axonD / 2) + self._spaceI)**2) - ((self._axonD / 2)**2)))
        self._interLength = (self._deltax - self._nodeLength -
                             (2 * self._paraLength1) - (2 * self._paraLength2)) / 6

        self.nodeToNodeDistance = self._nodeLength + 2 * (self._paraLength1 + self._paraLength2) + 6 * self._interLength
        self.totalFiberLength = self._nodeLength * self._axonNodes + self._paraNodes1 * \
            self._paraLength1 + self._paraNodes2 * self._paraLength2 + self._interLength * self._axonInter

    def _create_sections(self):
        """ Create the sections of the cell. """

        # NOTE: cell=self is required to tell NEURON of this object.
        self.node = [h.Section(name=f'node{x}', cell=self) for x in range(self._axonNodes)]
        self.mysa = [h.Section(name=f'mysa{x}', cell=self) for x in range(self._paraNodes1)]
        self.flut = [h.Section(name=f'flut{x}', cell=self) for x in range(self._paraNodes2)]
        self.stin = [h.Section(name=f'stin{x}', cell=self) for x in range(self._axonInter)]
        self.segments = []

        # Positions
        delta_node_mysa = 0.5 * (self._nodeLength + self._paraLength1)
        delta_mysa_flut = 0.5 * (self._paraLength1 + self._paraLength2)
        xnodes = self.nodeToNodeDistance * np.arange(self.nNodes)
        xnodes -= xnodes[int((self.nNodes - 1) / 2)]
        xmysa = np.ravel(np.column_stack((xnodes[:-1] + delta_node_mysa, xnodes[1:] - delta_node_mysa)))
        xflut = np.ravel(np.column_stack((xmysa[::2] + delta_mysa_flut, xmysa[1::2] - delta_mysa_flut)))
        xref = xflut[::2] + 0.5 * (self._paraLength2 + self._interLength)
        xstin = np.ravel([xref + i * self._interLength for i in range(6)], order='F')
        for i, node in enumerate(self.node):
            self.segments.append([node, xnodes[i], 'node'])
        for i, mysa in enumerate(self.mysa):
            self.segments.append([mysa, xmysa[i], 'mysa'])
        for i, flut in enumerate(self.flut):
            self.segments.append([flut, xflut[i], 'flut'])
        for i, stin in enumerate(self.stin):
            self.segments.append([stin, xstin[i], 'stin'])

    def _define_biophysics(self):
        """ Assign the membrane properties across the cell. """
        for node in self.node:
            node.nseg = 1
            node.diam = self._nodeD
            node.L = self._nodeLength
            node.Ra = self._rhoa / 10000
            node.cm = 2
            node.insert('MRGnode')
            node.insert('extracellular')
            node.xraxial[0] = self._Rpn0
            node.xg[0] = 1e10
            node.xc[0] = 0

        for mysa in self.mysa:
            mysa.nseg = 1
            mysa.diam = self.fiberD
            mysa.L = self._paraLength1
            mysa.Ra = self._rhoa * (1 / (self._paraD1 / self.fiberD)**2) / 10000
            mysa.cm = 2 * self._paraD1 / self.fiberD
            mysa.insert('pas')
            mysa.g_pas = 0.001 * self._paraD1 / self.fiberD
            mysa.e_pas = -80
            mysa.insert('extracellular')
            mysa.xraxial[0] = self._Rpn1
            mysa.xg[0] = self._mygm / (self._nl * 2)
            mysa.xc[0] = self._mycm / (self._nl * 2)

        for flut in self.flut:
            flut.nseg = 1
            flut.diam = self.fiberD
            flut.L = self._paraLength2
            flut.Ra = self._rhoa * (1 / (self._paraD2 / self.fiberD)**2) / 10000
            flut.cm = 2 * self._paraD2 / self.fiberD
            flut.insert('pas')
            flut.g_pas = 0.0001 * self._paraD2 / self.fiberD
            flut.e_pas = -80
            flut.insert('extracellular')
            flut.xraxial[0] = self._Rpn2
            flut.xg[0] = self._mygm / (self._nl * 2)
            flut.xc[0] = self._mycm / (self._nl * 2)

        for stin in self.stin:
            stin.nseg = 1
            stin.diam = self.fiberD
            stin.L = self._interLength
            stin.Ra = self._rhoa * (1 / (self._axonD / self.fiberD)**2) / 10000
            stin.cm = 2 * self._axonD / self.fiberD
            stin.insert('pas')
            stin.g_pas = 0.0001 * self._axonD / self.fiberD
            stin.e_pas = -80
            stin.insert('extracellular')
            stin.xraxial[0] = self._Rpx
            stin.xg[0] = self._mygm / (self._nl * 2)
            stin.xc[0] = self._mycm / (self._nl * 2)

    def details(self):
        row_labels = ['node', 'MYSA', 'FLUT', 'STIN']
        col_labels = ['nsec', 'nseg', 'diam', 'L', 'cm', 'Ra', 'xr', 'xg', 'xc']
        d = []
        for seclist in [self.node, self.mysa, self.flut, self.stin]:
            sec = seclist[0]
            d.append([len(seclist), sec.nseg, sec.diam, sec.L, sec.cm, sec.Ra,
                      sec.xraxial[0], sec.xg[0], sec.xc[0]])
        return pd.DataFrame(data=np.array(d), index=row_labels, columns=col_labels)

    def _build_topology(self):
        """ connect the sections together """
        # childSection.connect(parentSection, [parentX], [childEnd])
        for i in range(self._axonNodes - 1):
            self.node[i].connect(self.mysa[2 * i], 1, 0)
            self.mysa[2 * i].connect(self.flut[2 * i], 1, 0)
            self.flut[2 * i].connect(self.stin[6 * i], 1, 0)
            self.stin[6 * i].connect(self.stin[6 * i + 1], 1, 0)
            self.stin[6 * i + 1].connect(self.stin[6 * i + 2], 1, 0)
            self.stin[6 * i + 2].connect(self.stin[6 * i + 3], 1, 0)
            self.stin[6 * i + 3].connect(self.stin[6 * i + 4], 1, 0)
            self.stin[6 * i + 4].connect(self.stin[6 * i + 5], 1, 0)
            self.stin[6 * i + 5].connect(self.flut[2 * i + 1], 1, 0)
            self.flut[2 * i + 1].connect(self.mysa[2 * i + 1], 1, 0)
            self.mysa[2 * i + 1].connect(self.node[i + 1], 1, 0)

    """
    Redefinition of inherited methods
    """

    def connect_to_target(self, target, nodeN=-1):
        nc = h.NetCon(self.node[nodeN](1)._ref_v, target, sec=self.node[nodeN])
        nc.threshold = -30
        nc.delay = 0
        return nc

    def is_artificial(self):
        """ Return a flag to check whether the cell is an integrate-and-fire or artificial cell. """
        return 0
