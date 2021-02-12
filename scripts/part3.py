# -*- coding: utf-8 -*-
# @Author: Theo Lemaire
# @Email: theo.lemaire@epfl.ch
# @Date:   2019-06-05 14:08:31
# @Last Modified by:   Theo Lemaire
# @Last Modified time: 2021-02-12 17:27:48

import sys
from FNE_NEURON.simulations import MyelinatedFiberStimulation


def main():
    """ This script to asses the effect of intracellular stimulation (current clamp)
    on the membrane potential of a modeled myelinated fiber.
    The plot resulting from this simulation are saved in the Results folder.
    """

    if len(sys.argv) < 2:
        print("Error in arguments. Required arguments:")
        print("\t Fiber diameter (um)")
        print("\t Pulse width (ms)")
        print("\t Simulation amplitude (nA)")
        print("Optional arguments:")
        print("\t Output name")
        sys.exit(-1)

    fiberD = float(sys.argv[1])  # um
    pulse_width = float(sys.argv[2])  # ms
    stim_amp = float(sys.argv[3])  # nA

    if len(sys.argv) > 2:
        name = sys.argv[2]
    else:
        name = "part3"

    tstop = 15  # ms

    print("\nSimulation parameters:")
    print("\tFiber diameter: %f um" % (fiberD))
    print("\tStimulation amplitude: %f nA" % (stim_amp))

    simulation = MyelinatedFiberStimulation(fiberD, 0, 0, tstop, 0)
    stimulatedSegment = simulation.fiber.node[simulation.fiber.nNodes // 2]
    simulation.attach_current_clamp(
        stimulatedSegment, stim_amp, simulation._stimStartTime, pulse_width)
    simulation.run()
    simulation.plot(name)


if __name__ == '__main__':
    main()
