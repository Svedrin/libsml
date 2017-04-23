# -*- coding: utf-8 -*-

from distutils.core import setup, Extension

ffmpegmodule = Extension(
	'sml',
	sources   = ['smlmodule.c'],
	libraries = ["sml", "uuid"],
	include_dirs = ["../sml/include"],
	library_dirs = ["../sml/lib"]
	)

setup(
	name = 'sml',
	version = '1.0',
	description = "Python module to interface libsml",
	ext_modules = [ffmpegmodule],
	scripts     = ["../examples/ehzpoll"],
	author="Michael Ziegler",
	author_email='diese-addy@funzt-halt.net'
)

