#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(name="telescope_scheduler",
      version="2026.7",
      description="Software to schedule telescope observations",
      long_description=open("README.md", "rt").read(),
      long_description_content_type='text/markdown',
      #scripts=glob.glob("scripts/pyharm*"),

      install_requires=[
          "numpy",
          "matplotlib",
          "click",
          "pandas",
          "astropy"  
          "astroplan"],

      author="J.S.Stanway",
      packages=find_packages(),
      )