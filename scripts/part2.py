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
        print("\t Simulation amplitude (uA)")
        print("Optional arguments:")
        print("\t Output name")
        sys.exit(-1)

    fiberDiameter = float(sys.argv[1])  # um
    stimulatioAmplitude = float(sys.argv[2])  # mA
    if len(sys.argv) > 3:
        name = sys.argv[3]
    else:
        name = "part2"
    stimulationFrequency = 60  # Hz
    pulseWidth = 0.1  # ms
    tstop = 30  # ms

    print("\nSimulation parameters:")
    print("\tFiber diameter: %f um" % (fiberDiameter))
    print("\tStimulation amplitude: %f uA" % (stimulatioAmplitude))

    simulation = MyelinatedFiberStimulation(
        fiberDiameter, stimulatioAmplitude, stimulationFrequency, tstop, pulseWidth)
    simulation.run()
    simulation.plot(name)


if __name__ == '__main__':
    main()
