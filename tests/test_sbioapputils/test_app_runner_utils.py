import os
import re
import signal

import pytest
import requests

from sbioapputils.app_runner import app_runner_utils
from sbioapputils.app_runner.app_runner_utils import AppRunnerUtils, JobTerminated, SIGTERM_MESSAGE


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(app_runner_utils.time, "sleep", lambda _: None)


@pytest.fixture
def calls(monkeypatch):
    """Record runner side effects in order instead of hitting S3/Backend."""
    recorded = []
    monkeypatch.setattr(AppRunnerUtils, "upload_file",
                        classmethod(lambda cls, job_id, src: recorded.append(("upload", job_id, src))))
    monkeypatch.setattr(AppRunnerUtils, "set_job_completed",
                        classmethod(lambda cls, job_id, files, credit=0: recorded.append(("completed", job_id, files))))
    monkeypatch.setattr(AppRunnerUtils, "set_job_failed",
                        classmethod(lambda cls, job_id, err, credit=0: recorded.append(("failed", job_id, err))))
    return recorded


def _http_error(status: int) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status
    return requests.HTTPError(response=response)


class TestFinishJob:

    def test_uploads_log_before_reporting_failure(self, calls):
        AppRunnerUtils.finish_job("job-1", "job.log", error="boom")
        assert calls == [("upload", "job-1", "job.log"), ("failed", "job-1", "boom")]

    def test_uploads_log_before_reporting_completion(self, calls):
        AppRunnerUtils.finish_job("job-1", "job.log", result_files={"tables": []})
        assert calls == [("upload", "job-1", "job.log"), ("completed", "job-1", {"tables": []})]

    def test_completion_defaults_to_empty_results(self, calls):
        AppRunnerUtils.finish_job("job-1", "job.log")
        assert calls[-1] == ("completed", "job-1", {})

    def test_reports_status_even_when_log_upload_fails(self, calls, monkeypatch):
        def failing_upload(cls, job_id, src):
            calls.append(("upload", job_id, src))
            raise OSError("s3 down")

        monkeypatch.setattr(AppRunnerUtils, "upload_file", classmethod(failing_upload))
        AppRunnerUtils.finish_job("job-1", "job.log", error="boom", retries=2)
        assert calls == [("upload", "job-1", "job.log")] * 2 + [("failed", "job-1", "boom")]

    def test_retries_transient_status_report_failure(self, calls, monkeypatch):
        attempts = []

        def flaky_failed(cls, job_id, err, credit=0):
            attempts.append(err)
            if len(attempts) < 3:
                raise requests.ConnectionError("backend unavailable")

        monkeypatch.setattr(AppRunnerUtils, "set_job_failed", classmethod(flaky_failed))
        AppRunnerUtils.finish_job("job-1", "job.log", error="boom")
        assert attempts == ["boom"] * 3

    def test_does_not_retry_client_error(self, calls, monkeypatch):
        attempts = []

        def rejected(cls, job_id, err, credit=0):
            attempts.append(err)
            raise _http_error(409)

        monkeypatch.setattr(AppRunnerUtils, "set_job_failed", classmethod(rejected))
        with pytest.raises(requests.HTTPError):
            AppRunnerUtils.finish_job("job-1", "job.log", error="boom")
        assert attempts == ["boom"]

    def test_retries_server_error(self, calls, monkeypatch):
        attempts = []

        def unavailable(cls, job_id, err, credit=0):
            attempts.append(err)
            raise _http_error(503)

        monkeypatch.setattr(AppRunnerUtils, "set_job_failed", classmethod(unavailable))
        with pytest.raises(requests.HTTPError):
            AppRunnerUtils.finish_job("job-1", "job.log", error="boom", retries=3)
        assert attempts == ["boom"] * 3


class TestSetJobFailed:

    def test_raises_on_http_error(self, monkeypatch):
        monkeypatch.setattr(AppRunnerUtils, "get_api_token", classmethod(lambda cls: "token"))
        response = requests.Response()
        response.status_code = 500
        monkeypatch.setattr(app_runner_utils.requests, "put", lambda *a, **kw: response)
        with pytest.raises(requests.HTTPError):
            AppRunnerUtils.set_job_failed("job-1", "boom")


class TestSigtermHandler:

    def test_sigterm_raises_job_terminated(self):
        previous = signal.getsignal(signal.SIGTERM)
        try:
            AppRunnerUtils.install_sigterm_handler()
            with pytest.raises(JobTerminated, match=re.escape(SIGTERM_MESSAGE)):
                os.kill(os.getpid(), signal.SIGTERM)
        finally:
            signal.signal(signal.SIGTERM, previous)
