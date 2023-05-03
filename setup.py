from setuptools import setup

setup(name="sbioapputils",
      version="1.0.1",
      description="SBIO app runner utils",
      license='MIT',
      author="superbio.ai",
      authoer_email="",
      url='https://github.com/Superbio-ai/app-sbioutils',
      install_requires=['requests==2.22.0', 'boto3==1.21.27','pandas==1.2.5', 'anndata==0.8.0', 'scanpy==1.9.1', 'numpy==1.21'],
      packages=['sbioapputils']
)
