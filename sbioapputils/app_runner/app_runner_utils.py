import boto3
import logging
import os
import requests
from logging.handlers import WatchedFileHandler

from sbioapputils.app_runner.s3_transfer import multipart_download, multipart_upload


class AppRunnerUtils:

    @classmethod
    def get_s3_bucket(cls, external_bucket=None):
        if external_bucket:
            role_arn = os.environ.get("ROLE_ARN")
            credentials = cls.assume_role(role_arn)
            session = boto3.session.Session(aws_access_key_id=credentials['AccessKeyId'],
                                            aws_secret_access_key=credentials['SecretAccessKey'],
                                            aws_session_token=credentials['SessionToken'])
            s3 = session.resource('s3')
            return s3.Bucket(external_bucket)
        else:
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
    def get_s3_client(cls, external_bucket=None):
        """Return a boto3 S3 **client** and the resolved bucket name.

        Unlike ``get_s3_bucket`` (which returns a *resource* Bucket object),
        this method returns a low-level client suitable for
        ``download_file`` / ``upload_file`` with ``TransferConfig``.

        Returns:
            tuple: (s3_client, bucket_name)
        """
        if external_bucket:
            role_arn = os.environ.get("ROLE_ARN")
            credentials = cls.assume_role(role_arn)
            s3_client = boto3.client(
                's3',
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
                region_name=os.environ.get("AWS_REGION"),
            )
            return s3_client, external_bucket
        else:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                region_name=os.environ.get("AWS_REGION"),
            )
            return s3_client, os.environ.get("AWS_DATASET_BUCKET")

    @classmethod
    def assume_role(cls, role_arn):
        sts_client = boto3.client('sts')
        assumed_role = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="YourSessionName"
        )
        credentials = assumed_role['Credentials']
        return credentials

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
        src_files.extend(cls._build_file_list(results.get('pdbs')))
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
        external_bucket = None
        if "EXTERNAL_BUCKET" in os.environ and os.environ.get("SAVE_RESULTS_TO_USER_DATA", "").lower() in ("true", "1", "yes"):
            external_bucket = os.environ.get("EXTERNAL_BUCKET")
        s3_client, bucket_name = cls.get_s3_client(external_bucket)
        for src_file in src_files:
            cls._upload(s3_client, bucket_name, src_file, dest)

    @classmethod
    def upload_file(cls, job_id: str, src_file: str):
        dest = cls.get_job_folder(job_id)
        external_bucket = None
        if "EXTERNAL_BUCKET" in os.environ and os.environ.get("SAVE_RESULTS_TO_USER_DATA", "").lower() in ("true", "1", "yes"):
            external_bucket = os.environ.get("EXTERNAL_BUCKET")
        s3_client, bucket_name = cls.get_s3_client(external_bucket)
        cls._upload(s3_client, bucket_name, src_file, dest)

    @classmethod
    def _upload(cls, s3_client, bucket_name: str, src: str, dest_folder: str):
        dest_file = f'{dest_folder}{src}'
        multipart_upload(s3_client, bucket_name, src, dest_file)
        logging.info(f'Uploaded a file {dest_file}')

    @classmethod
    def download_file(cls, source_file_path: str, dest_file_path: str):
        config_v2 = cls.get_job_config_v2(os.environ.get("JOB_ID"))
        external_bucket = None
        if "EXTERNAL_BUCKET" in os.environ and cls.get_file_is_remote(source_file_path, config_v2):
            external_bucket = os.environ.get("EXTERNAL_BUCKET")

        s3_client, bucket_name = cls.get_s3_client(external_bucket)
        multipart_download(s3_client, bucket_name, source_file_path, dest_file_path)

    @classmethod
    def load_file(cls, source_file_path: str):
        config_v2 = cls.get_job_config_v2(os.environ.get("JOB_ID"))
        external_bucket = None
        if "EXTERNAL_BUCKET" in os.environ and cls.get_file_is_remote(source_file_path, config_v2):
            external_bucket = os.environ.get("EXTERNAL_BUCKET")

        bucket = cls.get_s3_bucket(external_bucket)
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
            return eval(os.environ.get("JOB_CONFIG", "{}"))
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
    def get_file_is_remote(cls, file_path: str, config):
        for key, items in config['input_files'].items():
            for item in items:
                if item["path"] == file_path:
                    return item["additional_info"].get('user_data', False)

    @classmethod
    def get_job_run_by_admin(cls):
        if "RUN_BY_ADMIN" in os.environ:
            return eval(os.environ.get("RUN_BY_ADMIN", "False"))
        else:
            return False

    @classmethod
    def get_job_config_v2(cls, job_id: str):
        if "JOB_CONFIG" in os.environ:
            return eval(os.environ.get("JOB_CONFIG", "{}"))
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
    def set_job_completed(cls, job_id: str, result_files: dict, credit=0):
        token = cls.get_api_token()
        api_url = os.environ.get("SBIO_API_URL")
        headers = {'Authorization': f'Bearer {token}'}
        payload = {'result_files': {'files': result_files}}
        if credit > 0:
            payload['credits'] = credit
        requests.put(f'{api_url}/api/jobs/{job_id}/completed', headers=headers, json=payload)

    @classmethod
    def set_job_failed(cls, job_id: str, err_msg: str, credit=0):
        token = cls.get_api_token()
        api_url = os.environ.get("SBIO_API_URL")
        headers = {'Authorization': f'Bearer {token}'}
        payload = {'error_message': err_msg}
        if credit > 0:
            payload['credits'] = credit
        requests.put(f'{api_url}/api/jobs/{job_id}/failed', headers=headers, json=payload)

    @classmethod
    def verify_user_has_enough_credits(cls, job_id: str, expected_credit_usage: int):
        token = cls.get_api_token()
        api_url = os.environ.get("SBIO_API_URL")
        headers = {'Authorization': f'Bearer {token}'}
        payload = {'job_id': job_id, 'expected_credit_usage': expected_credit_usage}
        response = requests.get(f'{api_url}/api/verify_enough_credits', headers=headers, params=payload)
        if response.status_code == 200:
            return response.json()['has_enough_credits']
        else:
            logging.error(response)
