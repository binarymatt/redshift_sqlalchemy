from setuptools import setup

setup(
    name='redshift-sqlalchemy',
    version='0.1.2',
    description='Amazon Redshift Dialect for sqlalchemy',
    long_description=open("README.rst").read(),
    author='Matt George',
    author_email='mgeorge@gmail.com',
    license="MIT",
    url='https://github.com/sqlalchemy-redshift/sqlalchemy-redshift',
    packages=[],
    install_requires=['sqlalchemy-redshift==0.1.2'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
)

