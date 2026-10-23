import setuptools

setuptools.setup(
    name="dfmt",
    version="1.0",
    description="An api used to create hash databases of disk images and query files on those images.",
    install_requires=['Click'],
    packages=setuptools.find_packages(),
    entry_points='''
        [console_scripts]
        dfmt=dfmt.main:cli
    ''',
    include_package_data=True,
)