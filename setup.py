from setuptools import setup, find_packages

setup(
    name='somfy',
    version='0.1',
    description='',
    author='Gregoire Mahe',
    author_email='gregoire@mahe.lt',
    zip_safe=False,
    packages=['somfy'],
    install_requires=[
        'pigpio'
    ],
    keywords='Somfy blinds',
    dependency_links=[]
)
