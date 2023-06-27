import boto3
import logging
import os
import requests
from logging.handlers import WatchedFileHandler


class AppRunnerUtils:

    @classmethod
    def get_s3_bucket(cls):
        key_id = os.environ.get("AWS_ACCESS_KEY_ID")
        secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        region = os.environ.get("AWS_REGION")
        bucket = os.environ.get("AWS_DATASET_BUCKET")
        session = boto3.session.Session(aws_access_key_id=key_id,
                                        aws_secret_access_key=secret_key,
                                        region_name=region)
        s3 = session.resource('s3')
        return s3.Bucket(bucket)

    @classmethod
    def upload_results(cls, job_id: str, results: dict):
        src_files = cls._build_result_file_list(results)
        cls.upload_result_files(job_id, src_files)

    @classmethod
    def _build_result_file_list(cls, results: dict):
        # currently we have 4 keywords for results: images, figures, tables, and download
        # images, figures and tables are list of list
        src_files = []
        src_files.extend(cls._build_file_list(results.get('images')))
        src_files.extend(cls._build_file_list(results.get('figures')))
        src_files.extend(cls._build_file_list(results.get('tables')))
        # download is a list of dict
        if results.get('download'):
            for file_dict in results.get('download'):
                src_files.append(file_dict['file'])
        return src_files

    @classmethod
    def _build_file_list(cls, file_lists: list):
        files = []
        if file_lists:
            for file_list in file_lists:
                for file_dict in file_list:
                    files.append(file_dict['file'])
        return files

    @classmethod
    def upload_result_files(cls, job_id: str, src_files: list):
        dest = cls.get_job_folder(job_id)
        bucket = cls.get_s3_bucket()
        for src_file in src_files:
            cls._upload(bucket, src_file, dest)

    @classmethod
    def upload_file(cls, job_id: str, src_file: str):
        dest = cls.get_job_folder(job_id)
        bucket = cls.get_s3_bucket()
        cls._upload(bucket, src_file, dest)

    @classmethod
    def _upload(cls, bucket, src: str, dest_folder: str):
        f = open(src, "rb")
        dest_file = f'{dest_folder}{src}'
        bucket.put_object(Key=dest_file, Body=f.read())
        f.close()
        logging.info(f'Uploaded a file {dest_file}')

    @classmethod
    def download_file(cls, source_file_path: str, dest_file_path: str):
        bucket = cls.get_s3_bucket()
        obj = bucket.Object(source_file_path)
        f = open(dest_file_path, "wb")
        f.write(obj.get()['Body'].read())
        f.close()
    
    @classmethod
    def load_file(cls, source_file_path: str):
        bucket = cls.get_s3_bucket()
        obj = bucket.Object(source_file_path)
        body = obj.get()['Body'].read()
        return body

    @classmethod
    def set_logging(cls, log_file: str):
        handler = WatchedFileHandler(log_file)
        formatter = logging.Formatter(
                    "%(asctime)s  [%(levelname)s]\n%(message)s",
                        "%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.setLevel("INFO")
        root.addHandler(handler)

    @classmethod
    def get_api_token(cls):
        user = os.environ.get("APP_USER")
        password = os.environ.get("APP_USER_PASSWORD")
        api_url = os.environ.get("SBIO_API_URL")
        payload = {"email": user, "password": password}
        r = requests.post(f'{api_url}/login', json=payload)
        return r.json()['access_token']

    @classmethod
    def get_job_folder(cls, job_id: str):
        token = cls.get_api_token()
        api_url = os.environ.get("SBIO_API_URL")
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f'{api_url}/api/jobs/{job_id}/folder', headers=headers)
        if response.status_code == 200:
            return response.json()['folder']
        else:
            logging.error(response)
 
    @classmethod
    def get_job_config(cls, job_id: str):
        if "JOB_CONFIG" in os.environ:
            response =  eval(os.environ.get("JOB_CONFIG"))
            return response
        else:
            token = cls.get_api_token()
            api_url = os.environ.get("SBIO_API_URL")
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(f'{api_url}/api/jobs/{job_id}/config', headers=headers)
            if response.status_code == 200:
                return response.json()['config']          
            else:
                logging.error(response)

    @classmethod
    def get_job_config_v2(cls, job_id: str):
        if "JOB_CONFIG" in os.environ:
            response =  eval(os.environ.get("JOB_CONFIG"))
            return response
        else:
            token = cls.get_api_token()
            api_url = os.environ.get("SBIO_API_URL")
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(f'{api_url}/api/jobs/{job_id}/config?version=v2', headers=headers)
            if response.status_code == 200:
                return response.json()['config']
            else:
                logging.error(response)

    @classmethod
    def set_job_running(cls, job_id: str):
        token = cls.get_api_token()
        api_url = os.environ.get("SBIO_API_URL")
        headers = {'Authorization': f'Bearer {token}'}
        requests.put(f'{api_url}/api/jobs/{job_id}/running', headers=headers)

    @classmethod
    def set_job_completed(cls, job_id: str, result_files: dict):
        token = cls.get_api_token()
        api_url = os.environ.get("SBIO_API_URL")
        headers = {'Authorization': f'Bearer {token}'}
        payload = {'result_files': {'files': result_files}}
        requests.put(f'{api_url}/api/jobs/{job_id}/completed', headers=headers, json=payload)

    @classmethod
    def set_job_failed(cls, job_id: str, err_msg: str):
        token = cls.get_api_token()
        api_url = os.environ.get("SBIO_API_URL")
        headers = {'Authorization': f'Bearer {token}'}
        payload = {'error_message': err_msg}
        requests.put(f'{api_url}/api/jobs/{job_id}/failed', headers=headers, json=payload)
