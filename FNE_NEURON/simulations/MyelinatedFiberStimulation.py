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
        """ Object initialization.

        """

        Simulation.__init__(self)

        h.dt = 0.025
        self._diameter = diameter

        # Create the fiber
        self.fiber = MyelinatedFiber(self._diameter)
        self.fibersPosition = 100  # in um

        # stimulation parameters
        self._stimStartTime = 5
        self._amplitude = amplitude
        self._electrodeOffset = self.fiber.nodeToNodeDistance * 50.  # centered to the fiber
        self._pulseWidth = pulseWidth  # in ms
        if frequency == 0:
            self._frequency = 0.001
        else:
            self._frequency = frequency  # in Hz
        self._stimulationInterval = 1000. / self._frequency  # in ms

        self._stim = False
        self._stimParameters = []
        self._set_field(0)

        # Iclam stimulation
        self._iclampStim = False

        # Initialize lists for netStim
        self._secondaryStimObjects = []
        self._syn = []
        self._netcons = []

        self._set_tstop(tstop)
        # To plot the results with a high resolution we use an integration step equal to the Neuron dt
        self._set_integration_step(h.dt)

        self._set_print_period(5)

        # Initialize a 2d numpy array to hold the membrane potentials of the whole fiber over time
        self._membranPot = np.nan * np.zeros((
            self.fiber.nNodes,
            int(np.ceil(self._get_tstop() / self._get_integration_step() + 1))
        ))
        self._count = 0

    """
    Redefinition of inherited methods
    """

    def foo(self, x1, x2):
        return x2 / (4 * np.pi * x1 * 2.) * 1e-3

    def _update(self):
        """ Record membrane potential and update simulation parameters. """
        # Record membrane potential
        for j in range(self.fiber.nNodes):
            self._membranPot[j, self._count] = self.fiber.node[j](0.5).v
        self._count += 1

        # extracellular stimulation
        if self._amplitude:
            if h.t > self._stimStartTime and h.t % self._stimulationInterval < self._pulseWidth and not self._stim:
                self._set_field(self._amplitude)
                self._stim = True
            elif h.t % self._stimulationInterval >= self._pulseWidth and self._stim:
                self._set_field(0)
                self._stim = False


    def save_results(self, name=""):
        pass

    def plot(self, name="", block=True):
        """ Plot the simulation results. """
        fig, ax = plt.subplots(2, figsize=(10, 7), sharex=True)

        """ Plot membrane potential in all the nodes as an image"""
        im = ax[0].imshow(self._membranPot, interpolation='nearest', origin='lower', aspect='auto')

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
            ax[1].plot(self._membranPot[int(node), :], label="node: %d" % (node + 1))

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

        ax[1].set_xticks(np.arange(0, self._get_tstop() / self._get_integration_step(),
                                   5. / self._get_integration_step()))
        ax[1].set_xticklabels(np.arange(0, self._get_tstop(), 5))
        ax[1].set_xlim([0, self._get_tstop() / self._get_integration_step()])

        ax[1].set_xlabel('Time (ms)')

        """ Plot stimulation """
        if self._amplitude:
            fig.subplots_adjust(bottom=0.3)
            pos = ax[1].get_position()
            stimAx = fig.add_axes([pos.x0, 0.1, pos.width, 0.1])

            stimAx.plot(self._stimParameters[:, 0], self._stimParameters[:, 1], color='#00ADEE')

            # Move left and bottom spines outward by 5 points
            stimAx.spines['left'].set_position(('outward', 5))
            stimAx.spines['bottom'].set_position(('outward', 5))

            # Hide the right and top spines
            stimAx.spines['right'].set_visible(False)
            stimAx.spines['top'].set_visible(False)

            # Only show ticks on the left and bottom spines
            stimAx.yaxis.set_ticks_position('left')
            stimAx.xaxis.set_ticks_position('bottom')

            stimAx.set_xticks(np.arange(0, self._get_tstop(), 5))
            stimAx.set_xticklabels(np.arange(0, self._get_tstop(), 5))
            stimAx.set_xlim([0, self._stimParameters[-1, 0]])

            stimAx.set_ylabel('(uA)')
            stimAx.set_xlabel('Time (ms)')

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

            stimAx.set_xticks(np.arange(0, self._get_tstop(), 5))
            stimAx.set_xticklabels(np.arange(0, self._get_tstop(), 5))
            stimAx.set_xlim([0, self._get_tstop()])

            stimAx.set_ylabel('(nA)')
            stimAx.set_xlabel('Time (ms)')

        fileName = time.strftime("%Y_%m_%d_neuron_exercise_" + name + ".pdf")
        plt.savefig(self._resultsFolder + fileName, format="pdf", transparent=True)

        plt.show(block=block)

    def _end_integration(self):
        Simulation._end_integration(self)
        if self._amplitude:
            self._stimParameters.append([self._stimParameters[-1][0], 0])
            self._stimParameters.append([self._get_tstop(), 0])
            self._stimParameters = np.array(self._stimParameters)

    """
    Specific Methods of this class
    """

    def _set_field(self, amplitude):
        plotFleg = False
        field = []
        x = []
        for segment in self.fiber.segments:
            distance = np.sqrt(((segment[1] - self._electrodeOffset) / 1000000.)**2 + (self.fibersPosition / 1000000.)**2)
            segment[0].e_extracellular = self.foo(distance, amplitude)
            if segment[2] == 'node':
                field.append(segment[0].e_extracellular)
                x.append((segment[1]))
        if amplitude is not 0 and plotFleg:
            plt.plot(x, field)
            plt.show()
        if self._stimParameters:
            self._stimParameters.append([h.t - self._get_integration_step(), self._stimParameters[-1][1]])
        self._stimParameters.append([h.t, amplitude])

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
            [0, delay, delay, delay + dur, delay + dur, self._get_tstop()],
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
