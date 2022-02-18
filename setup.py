from setuptools import setup, find_packages
import hermes

with open('./README.md' , 'r', encoding = 'utf-8') as f:
    readme = f.read()

setup(
    name='hermes',
    version=hermes.__version__,
    author=hermes.__author__,
    author_email='contact@gabrielearmento.com',
    description='A signal parser to understand human trading signals',
    long_description_content_type='text/markdown',
    long_description=readme,
    packages=find_packages(where='hermes'),
    url='https://github.com/965311532/hermes',
    license=None,
    install_requires=['spacy'],
    python_requires='>=3.6'
    )