from setuptools import setup

setup(name="sbioapputils",
      description="Superbio app runner utils",
      author="Superbio AI",
      author_email="smorgan@superbio.ai",
      url='https://github.com/Superbio-ai/app-sbioutils',
      install_requires=['requests==2.22.0', 'boto3==1.21.27'],
      packages=['sbioapputils','sbioapputils.app_runner','sbioapputils.file_process','sbioapputils.file_process.h5ad','sbioapputils.file_process.csv']
)
