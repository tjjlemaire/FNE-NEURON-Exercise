# -*- coding: utf-8 -*-
# @Author: Theo Lemaire
# @Email: theo.lemaire@epfl.ch
# @Date:   2019-06-05 14:08:31
# @Last Modified by:   Theo Lemaire
# @Last Modified time: 2020-03-23 16:11:08

import os
import time
from neuron import h


class Simulation:
    """ Interface class to design different types of neuronal simulation.

        The simulations are based on the python Neuron module and
        can be executed in parallel using MPI.
    """

    def __init__(self, tstop):
        """ Object initialization. """
        # Simulation parameters
        h.celsius = 36.  # Celsius
        h.dt = 0.01  # 0.025 (ms)
        self._tstop = tstop  # ms

        self._resultsFolder = "results/"
        if not os.path.exists(self._resultsFolder):
            os.makedirs(self._resultsFolder)

    def run(self):
        """ Run the simulation. """
        # Set integration parameters
        self.cvode = h.CVode()
        self.cvode.active(0)
        print(f'fixed time step integration (dt = {h.dt} ms)')

        self._start = time.time()

        # Initialize
        h.finitialize(-80)
        if self._amplitude:
            self.cvode.event(self._stimStartTime, self.toggleStim)

        # Integrate
        while h.t < self._tstop:
            h.fadvance()

        self.simulationTime = time.time() - self._start
        print("tot simulation time: " + str(int(self.simulationTime)) + "s")

    def set_results_folder(self, resultsFolderPath):
        """ Set a new folder in which to save the results """
        self._resultsFolder = resultsFolderPath
        if not os.path.exists(self._resultsFolder):
            os.makedirs(self._resultsFolder)

    def save_results(self, name=""):
        """ Save the simulation results.

        Keyword arguments:
        name -- string to add at predefined file name (default = "").
        """
        raise Exception("pure virtual function")

    def plot(self):
        """ Plot the simulation results. """
        raise Exception("pure virtual function")
