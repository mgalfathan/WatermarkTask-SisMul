from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='dwt-watermark',
    version='0.1.0',
    author='Muhammad Ghiffary Alfathan',
    description='Invisible image watermark using DWT Spread Spectrum',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/mgalfathan/WatermarkTask-SisMul.git',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        'opencv-python>=4.5',
        'numpy>=1.21',
        'PyWavelets>=1.1',
        'matplotlib>=3.4',
    ],
    entry_points={
        'console_scripts': [
            'dwt-watermark=dwt_watermark.__main__:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Multimedia :: Graphics',
    ],
)
