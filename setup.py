''' Flask-SQLAngelo '''
from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


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
      keywords='sqlalchemy flask',
      long_description=__doc__,
      url='http://github.com/otech-nl/sqlangelo',
      author='OTech BV',
      author_email='steets@otech.nl',
      license='CC BY-NC-ND',
      packages=['sqlangelo'],
      install_requires=[
          'flask-sqlalchemy',
          'inflect'
      ],
      extras_require={
          'dev': ['sphinx', 'sphinx-autobuild'],
          'test': ['faker'],
      },
      test_suite='tests',
      include_package_data=True,
      platforms='any',
      zip_safe=False
)
