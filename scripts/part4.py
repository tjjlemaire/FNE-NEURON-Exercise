import sys

from FNE_NEURON.simulations import MyelinatedFiberStimulation


def main():
    """ Within this simulation, extracellular electrical stimulation is imposed on
    a myelinated fiber while naturally firing at 55 Hz.
    The plot resulting from this simulation are saved in the Results folder.
    """

    if len(sys.argv) > 1:
        name = sys.argv[1]
    else:
        name = "part4"

    fiberDiameter = 20  # um
    stimulatioAmplitude = -80  # uA
    stimulationFrequency = 100  # Hz
    pulseWidth = 0.1  # ms
    tstop = 50  # ms

    simulation = MyelinatedFiberStimulation(
        fiberDiameter, stimulatioAmplitude, stimulationFrequency, tstop, pulseWidth)

    # The fiber is naturally firing at 55 Hz
    segmentStart = simulation.fiber.node[0]
    simulation.attach_netstim(segmentStart, 55, 10, 19)

    simulation.run()
    simulation.plot(name)


if __name__ == '__main__':
    main()
