'''Setup script for installing doi2bibtex through pip.'''
import os
import setuptools

with open("README.md") as fh:
    long_description = fh.read()

setuptools.setup(name='doi2bibtex',
                 version='0.2',
                 description='Convert dois to bibtex and save to library.',
                 classifiers=['Development Status :: Beta',
                              'Intended Audience :: Science/Research',
                              'License :: OSI Approved :: MIT License',
                              'Programming Language :: Python :: 3',
                              'Topic :: Bibliographic :: BibTex',
                              ],
                 package_dir={"": "src"},
                 packages=setuptools.find_packages(where="src"),
                 python_requires=">=3.2",
                 keywords='bibtex abbreviate',
                 url='https://github.com/rchiechi/doi2bibtex',
                 author='Ryan C. Chiechi',
                 author_email='ryan.chiechi@ncsu.edu',
                 license='MIT',
                 install_requires=['bibtexparser>=2.0.0b7',
                                   'colorama>=0.4.6',
                                   'python-Levenshtein>=0.23.0',
                                   'titlecase>=2.4.1',
                                   'pyperclip>=1.8.2',
                                   'pylatexenc>=2.10',
                                   'iso4>=0.0.2',
                                   'argcomplete>=3.3.0',
                                   'flask>=3.0.3',
                                   'waitress>=3.0.0'
                                   ],
                 include_package_data=True,
                 scripts=[os.path.join("src", 'doi2bibtex')]
                 )
