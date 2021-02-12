# -*- coding: utf-8 -*-
# @Author: Theo Lemaire
# @Email: theo.lemaire@epfl.ch
# @Date:   2019-06-05 14:08:31
# @Last Modified by:   Theo Lemaire
# @Last Modified time: 2021-02-12 17:26:12

from neuron import h

import time
import numpy as np
import matplotlib.pyplot as plt

from .Simulation import Simulation
from ..cells import MyelinatedFiber


class MyelinatedFiberStimulation(Simulation):
    """ Simulation to asses to effect of extracellular/intracellulra stimulation
    on myelinated fibers. """

    def __init__(self, diameter, amplitude, frequency, tstop=100, pulseWidth=0.1):
        """ Object initialization. """
        super().__init__(tstop)

        # Create the fiber
        self._diameter = diameter
        self.fiber = MyelinatedFiber(self._diameter)
        self.fibersPosition = 100  # in um

        # stimulation parameters
        self._stimStartTime = 1
        self._amplitude = amplitude
        self._electrodeOffset = 0.  # centered to the fiber
        self._pulseWidth = pulseWidth  # in ms
        if frequency == 0:
            self._frequency = 0.001
        else:
            self._frequency = frequency  # in Hz
        self._stimulationInterval = 1000. / self._frequency  # in ms

        self._stim = False
        self._iclampStim = False
        self._secondaryStimObjects = []
        self._syn = []
        self._netcons = []

    def Vext(self, r, I):
        return I / (4 * np.pi * r * 2.) * 1e-3

    def toggleStim(self):
        ''' Toggle stim state (ON -> OFF or OFF -> ON) and set appropriate next toggle event. '''
        # OFF -> ON at pulse onset
        if not self._stim:
            self._stim = self.setStimON(True)
            self.cvode.event(h.t + self._pulseWidth, self.toggleStim)
        # ON -> OFF at pulse offset
        else:
            self._stim = self.setStimON(False)
            self.cvode.event(h.t + self._stimulationInterval - self._pulseWidth, self.toggleStim)

        # Re-initialize cvode if active, otherwise update currents
        if self.cvode.active():
            self.cvode.re_init()
        else:
            h.fcurrent()

    def setStimON(self, value):
        print(f't = {h.t:.2f} ms: turning stimulation {"ON" if value else "OFF"}')
        self._set_field(self._amplitude * int(value))
        return value

    def run(self):
        tprobe = h.Vector().record(h._ref_t)
        vprobes = [h.Vector().record(self.fiber.node[j](0.5)._ref_v)
                   for j in range(self.fiber.nNodes)]
        self.ext_stim_vec = []
        self._set_field(0)
        super().run()
        self.ext_stim_vec.append([h.t, 0.])
        self.ext_stim_vec = np.array(self.ext_stim_vec)
        self.tvec = np.array(tprobe.to_python())
        self._membranPot = np.array([v.to_python() for v in vprobes])

    def save_results(self, name=""):
        pass

    def plot(self, name="", block=True):
        """ Plot the simulation results. """
        print('rendering...')
        fig, ax = plt.subplots(2, figsize=(10, 7), sharex=True)

        """ Plot membrane potential in all the nodes as an image"""
        im = ax[0].pcolormesh(self.tvec, np.arange(self.fiber.nNodes), self._membranPot)

        fig.subplots_adjust(right=0.8)
        cbax = fig.add_axes([0.85, 0.6, 0.02, 0.3])
        fig.colorbar(im, cax=cbax)

        ax[0].set_title("Membrane potential")

        ax[0].set_ylabel('Start                          End\n===============\nFiber nodes')
        # Move left spine outward by 10 points
        ax[0].spines['left'].set_position(('outward', 10))
        # Hide the right and top spines
        ax[0].spines['bottom'].set_visible(False)
        ax[0].spines['right'].set_visible(False)
        ax[0].spines['top'].set_visible(False)
        # Only show ticks on the left and bottom spines
        ax[0].yaxis.set_ticks_position('left')
        ax[0].xaxis.set_ticks_position('none')

        """ Plot membrane potential in the selected nodes"""
        nodes = [0, self.fiber.nNodes / 2, self.fiber.nNodes - 1]
        for node in nodes:
            ax[1].plot(self.tvec, self._membranPot[int(node), :], label="node: %d" % (node + 1))

        ax[1].legend(loc=9, bbox_to_anchor=(0.95, 0.9))

        # Move left spines outward by 10 points
        ax[1].spines['left'].set_position(('outward', 10))
        ax[1].spines['bottom'].set_position(('outward', 10))
        # Hide the right and top spines
        ax[1].spines['right'].set_visible(False)
        ax[1].spines['top'].set_visible(False)
        # Only show ticks on the left and bottom spines
        ax[1].yaxis.set_ticks_position('left')
        ax[1].xaxis.set_ticks_position('bottom')

        ax[1].set_ylabel('membrane potential at \n%s (mV)' % (str(nodes)))

        ax[1].set_xlim([0, self._tstop])

        ax[1].set_xlabel('Time (ms)')

        """ Plot stimulation """
        if self._amplitude:
            tvec, Ivec = self.ext_stim_vec.T

            fig.subplots_adjust(bottom=0.3)
            pos = ax[1].get_position()
            stimAx = fig.add_axes([pos.x0, 0.1, pos.width, 0.1])

            stimAx.plot(tvec, Ivec, color='#00ADEE')

            # Move left and bottom spines outward by 5 points
            stimAx.spines['left'].set_position(('outward', 5))
            stimAx.spines['bottom'].set_position(('outward', 5))

            # Hide the right and top spines
            stimAx.spines['right'].set_visible(False)
            stimAx.spines['top'].set_visible(False)

            # Only show ticks on the left and bottom spines
            stimAx.yaxis.set_ticks_position('left')
            stimAx.xaxis.set_ticks_position('bottom')
            stimAx.set_xlim(0, tvec[-1])
            stimAx.set_ylabel('(uA)')
            stimAx.set_xlabel('Time (ms)')
            stimAx.get_shared_x_axes().join(stimAx, ax[1])

        elif self._iclampStim:
            fig.subplots_adjust(bottom=0.3)
            pos = ax[1].get_position()
            stimAx = fig.add_axes([pos.x0, 0.1, pos.width, 0.1])

            stimAx.plot(self._iclampStim[0], self._iclampStim[1], color='#00ADEE')

            # Move left and bottom spines outward by 5 points
            stimAx.spines['left'].set_position(('outward', 5))
            stimAx.spines['bottom'].set_position(('outward', 5))

            # Hide the right and top spines
            stimAx.spines['right'].set_visible(False)
            stimAx.spines['top'].set_visible(False)

            # Only show ticks on the left and bottom spines
            stimAx.yaxis.set_ticks_position('left')
            stimAx.xaxis.set_ticks_position('bottom')

            # stimAx.set_xticks(np.arange(0, self._get_tstop(), 5))
            # stimAx.set_xticklabels(np.arange(0, self._get_tstop(), 5))
            stimAx.set_xlim([0, self._tstop])

            stimAx.set_ylabel('(nA)')
            stimAx.set_xlabel('Time (ms)')

            stimAx.get_shared_x_axes().join(stimAx, ax[1])

        fileName = time.strftime("%Y_%m_%d_neuron_exercise_" + name + ".pdf")
        plt.savefig(self._resultsFolder + fileName, format="pdf", transparent=True)

        plt.show(block=block)

    def _set_field(self, amplitude):
        for segment in self.fiber.segments:
            distance = np.sqrt(((segment[1] - self._electrodeOffset) / 1000000.)**2 + (self.fibersPosition / 1000000.)**2)
            segment[0].e_extracellular = self.Vext(distance, amplitude)
        if self.ext_stim_vec:
            self.ext_stim_vec.append([h.t, self.ext_stim_vec[-1][1]])
        self.ext_stim_vec.append([h.t, amplitude])

    def attach_current_clamp(self, segment, amp=0.1, delay=1, dur=1):
        """ Attach a current Clamp to a segment.

        Keyword arguments:
        segment -- Segment object to attach the current clamp.
        amp -- Magnitude of the current (default = 0.1 in nA).
        delay -- Onset of the injected current (default = 0.1).
        dur -- Duration of the stimulus (default = 1).
        """

        self._secondaryStimObjects.append(h.IClamp(segment(0.5)))
        self._secondaryStimObjects[-1].delay = delay
        self._secondaryStimObjects[-1].dur = dur
        self._secondaryStimObjects[-1].amp = amp
        self._iclampStim = True
        self._iclampStim = [
            [0, delay, delay, delay + dur, delay + dur, self._tstop],
            [0, 0, amp, amp, 0, 0]
        ]

    def attach_netstim(self, segment, stimFreq, nPulses=1000, delay=1):
        """ Attach a Neuron NetStim object to a segment.

        Keyword arguments:
        segment -- Segment object to attach the NetStim.
        stimFreq -- Frequency of stimulation.
        nPulses -- Number of pulses to send (default = 1000).
        delay -- Onset of the stimulation (default = 1).
        """

        self._syn.append(h.ExpSyn(segment(0.5)))
        self._syn[-1].tau = 0.1
        self._syn[-1].e = 50
        self._secondaryStimObjects.append(h.NetStim())
        self._secondaryStimObjects[-1].interval = 1000 / stimFreq
        self._secondaryStimObjects[-1].number = nPulses
        self._secondaryStimObjects[-1].start = delay
        self._secondaryStimObjects[-1].noise = 0
        self._netcons.append(h.NetCon(self._secondaryStimObjects[-1], self._syn[-1]))
        self._netcons[-1].weight[0] = 1
        self._netcons[-1].delay = 1
