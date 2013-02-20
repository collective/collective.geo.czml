from setuptools import setup, find_packages
import os

version = '0.1'

setup(name='collective.geo.czml',
      version=version,
      description="czml vector layers for cesium",
      long_description=open("README.rst").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        ],
      keywords='GIS JOSN CZML Cesium Globe',
      author='Christian Ledermann',
      author_email='christian.ledermann@gmail.com',
      url='https://github.com/collective/collective.geo.czml.',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective', 'collective.geo'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'czml',
          'collective.geo.contentlocations',
          'collective.geo.settings',
      ],
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
