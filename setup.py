from setuptools import setup


setup(
      name="sbioapputils",
      version="1.0.32",
      description="Superbio app runner utils",
      author="Superbio AI",
      author_email="smorgan@superbio.ai",
      url='https://github.com/Superbio-ai/app-sbioutils',
      install_requires=['requests==2.22.0', 'boto3==1.21.27', 'pyflakes', 'pycodestyle', 'pandas>=1.2.5',
                        'anndata>=0.8.0', 'numpy>=1.22', 'file-process', 'openai', 'pyyaml'],
      packages=['sbioapputils', 'sbioapputils.app_runner', 'sbioapputils.load']
)
