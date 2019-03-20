from setuptools import setup


setup(
    name='FNE_NEURON',
    author='Théo Lemaire / Emanuele Formento',
    author_email='theo.lemaire@epfl.ch',
    license='MIT',
    packages=['FNE_NEURON'],
    install_requires=[
        'numpy>=1.10',
        'matplotlib>=2'
    ],
    zip_safe=False
)
