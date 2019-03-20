import sys

from FNE_NEURON.simulations import MyelinatedFiberStimulation


def main():
    """ This script to asses the effect of intracellular stimulation (current clamp)
    on the membrane potential of a modeled myelinated fiber.
    The plot resulting from this simulation are saved in the Results folder.
    """

    if len(sys.argv) < 2:
        print("Error in arguments. Required arguments:")
        print("\t Simulation amplitude (nA)")
        print("Optional arguments:")
        print("\t Output name")
        sys.exit(-1)

    stimulatioAmplitude = float(sys.argv[1])  # mA
    if len(sys.argv) > 2:
        name = sys.argv[2]
    else:
        name = "part3"

    fiberDiameter = 20  # um
    pulseWidth = 0.1  # ms
    tstop = 30  # ms
    startStim = 16.7

    print("\nSimulation parameters:")
    print("\tFiber diameter: %f um" % (fiberDiameter))
    print("\tStimulation amplitude: %f nA" % (stimulatioAmplitude))

    simulation = MyelinatedFiberStimulation(fiberDiameter, 0, 0, tstop, 0)

    stimulatedSegment = simulation.fiber.node[50]
    simulation.attach_current_clamp(stimulatedSegment, stimulatioAmplitude, startStim, pulseWidth)

    simulation.run()
    simulation.plot(name)


if __name__ == '__main__':
    main()
