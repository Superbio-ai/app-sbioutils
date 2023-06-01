# -*- coding: utf-8 -*-
import os


def get_credentials():
    os.environ["AWS_ACCESS_KEY_ID"] = 'XXX'
    os.environ["AWS_SECRET_ACCESS_KEY"] = 'xxx'
    os.environ["AWS_REGION"] = 'us-west-2'
    os.environ["AWS_DATASET_BUCKET"] = 'dev.superbio.ai'