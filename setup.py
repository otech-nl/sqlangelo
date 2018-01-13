'''
Flask-SQLAngelo
-----------
'''

from setuptools import setup

setup(name='flask_sqlangelo',
      version='0.1',
      description='',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
      ],
      keywords='flask scaffolding',
      long_description=__doc__,
      url='http://github.com/otech-nl/barrel',
      author='OTech BV',
      author_email='steets@otech.nl',
      license='CC BY-NC-ND',
      packages=['sqlangelo'],
      install_requires=[
          'flask-security',
          'flask-sqlalchemy',
          'inflect'
      ],
      setup_requires=['pytest-runner'],
      tests_require=['pytest', 'behave', 'faker'],
      test_suite='tests',
      include_package_data=True,
      platforms='any',
      zip_safe=False)
