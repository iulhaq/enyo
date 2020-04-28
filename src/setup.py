from setuptools import setup


setup(
    name = 'enyo',
    version = '0.1.0',
    description='A useful module',
    author='Ihtisham ul Haq',
    author_email='iulhaq@suse.com',
    packages = setuptools.find_packages(),
    entry_points = {
        'console_scripts': [
            'enyo = enyo.cli.main:__main__'
        ]
    })