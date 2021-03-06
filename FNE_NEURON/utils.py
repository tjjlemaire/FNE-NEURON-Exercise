import platform
import os
from neuron import h
from neuron import load_mechanisms as load_mechanisms_native


nrn_dll_loaded = []


def getNmodlDir():
    ''' Return path to directory containing MOD files and compiled mechanisms files. '''
    selfdir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(selfdir, 'nmodl')


def load_mechanisms(path, mechname=None):
    ''' Rewrite of NEURON's native load_mechanisms method to ensure Windows and Linux compatibility.

        :param path: full path to directory containing the MOD files of the mechanisms to load.
        :param mechname (optional): name of specific mechanism to check for untracked changes
        in source file.
    '''

    # Get OS
    OS = platform.system()

    # If Darwin, call native NEURON function and return
    if OS == 'Darwin':
        return load_mechanisms_native(path)

    # Otherwise, get platform-dependent path to compiled library file
    if OS == 'Windows':
        lib_path = os.path.join(path, 'nrnmech.dll')
    elif OS == 'Linux':
        lib_path = os.path.join(path, platform.machine(), '.libs', 'libnrnmech.so')
    else:
        raise OSError('Mechanisms loading on "{}" currently not handled.'.format(platform.system()))
    if not os.path.isfile(lib_path):
        raise RuntimeError('Compiled library file not found for mechanisms in "{}"'.format(path))

    # If mechanisms of input path are already loaded, return silently
    global nrn_dll_loaded
    if path in nrn_dll_loaded:
        return

    # If mechanism name is provided, check for untracked changes in source file
    if mechname is not None:
        mod_path = os.path.join(path, '{}.mod'.format(mechname))
        if not os.path.isfile(mod_path):
            raise RuntimeError('"{}.mod" not found in "{}"'.format(mechname, path))
        if os.path.getmtime(mod_path) > os.path.getmtime(lib_path):
            raise UserWarning('"{}.mod" more recent than compiled library'.format(mechname))

    # Load library file and add directory to list of loaded libraries
    h.nrn_load_dll(lib_path)
    nrn_dll_loaded.append(path)
