from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in leistertech/__init__.py
from leistertech import __version__ as version

setup(
	name="leistertech",
	version=version,
	description="leistertech",
	author="rakesh",
	author_email="bhardwajrakesh976@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
