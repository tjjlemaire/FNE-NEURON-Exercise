# -*- coding: utf-8 -*-
# @Author: Theo Lemaire
# @Email: theo.lemaire@epfl.ch
# @Date:   2019-06-05 14:08:31
# @Last Modified by:   Theo Lemaire
# @Last Modified time: 2021-02-12 17:29:12

import sys

from FNE_NEURON.simulations import MyelinatedFiberStimulation


def main():
    """ This script to asses the effect of extracellular electrical stimulation
    on the membrane potential of a modeled myelinated fiber.
    The plot resulting from this simulation are saved in the Results folder.
    """

    if len(sys.argv) < 3:
        print("Error in arguments. Required arguments:")
        print("\t Fiber diameter (um)")
        print("\t Pulse width (ms)")
        print("\t Simulation amplitude (uA)")
        print("Optional arguments:")
        print("\t Output name")
        sys.exit(-1)

    fiberDiameter = float(sys.argv[1])  # um
    pulseWidth = float(sys.argv[2])  # ms
    stimulationAmplitude = float(sys.argv[3])  # uA
    if len(sys.argv) > 3:
        name = sys.argv[3]
    else:
        name = "part2"
    stimulationFrequency = 0  # Hz
    tstop = 15  # ms

    print("\nSimulation parameters:")
    print("\tFiber diameter: %f um" % (fiberDiameter))
    print("\tStimulation amplitude: %f uA" % (stimulationAmplitude))

    simulation = MyelinatedFiberStimulation(
        fiberDiameter, stimulationAmplitude, stimulationFrequency, tstop, pulseWidth)
    simulation.run()
    simulation.plot(name)


if __name__ == '__main__':
    main()
