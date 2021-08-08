import setuptools

with open("README.md", "r") as readme_file:
    long_description = readme_file.read()

setuptools.setup(
    name="GX",
    version="0.0.1",
    author="Joan-Roch Sala",
    description="Describe and execute a DAG of jobs in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jrsala/gx",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires='>=3.9, <4', # TODO test with older Pythons
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Topic :: Software Development :: Build Tools"
    ]
)
