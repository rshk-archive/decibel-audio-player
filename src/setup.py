from setuptools import setup, find_packages

setup(
    name='Decibel',
    version='',
    packages=find_packages(),
    url='',
    license='GNU GPL v2',
    author='',
    author_email='',
    description='',
    install_requires=[
        'distribute',

        ## todo: check the dependencies and rebuild the list here
        ## we have some issues with building pygtk (must use ./configure && make
        ## instead of setup.py, ...)


        #'dbus',
        #'pygtk',
        #'mutagen',
        #'pil',
    ],
    include_package_data = True,
    entry_points = {
        'console_scripts': [
            'decibel = DecibelPlayer.player:main',
            ],
        },
    #package_data = {
    #    '': ['*.txt'],
    #    }
)
