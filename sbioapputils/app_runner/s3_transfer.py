import logging
import os
import time

from boto3.s3.transfer import TransferConfig

logger = logging.getLogger(__name__)

MB = 1024 * 1024
GB = 1024 * MB


def get_transfer_config(file_size):
    """Return a dynamic TransferConfig based on file size.

    Small files  (< 1 GB):  16 MB chunks, 10 threads
    Medium files (< 10 GB): 64 MB chunks, 15 threads
    Large files  (>= 10 GB): 256 MB chunks, 20 threads
    """
    if file_size < 1 * GB:
        chunk, concurrency = 16 * MB, 10
    elif file_size < 10 * GB:
        chunk, concurrency = 64 * MB, 15
    else:
        chunk, concurrency = 256 * MB, 20

    config = TransferConfig(
        multipart_threshold=16 * MB,
        multipart_chunksize=chunk,
        max_concurrency=concurrency,
        use_threads=True,
    )
    return config, chunk, concurrency


def multipart_download(s3_client, bucket, s3_key, local_path, progress=True):
    """Download a file from S3 using multipart transfer with progress logging.

    Args:
        s3_client: A boto3 S3 client instance.
        bucket: The S3 bucket name.
        s3_key: The S3 object key to download.
        local_path: The local file path to save the downloaded file.
        progress: Whether to log download progress (default True).
    """
    os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)

    head = s3_client.head_object(Bucket=bucket, Key=s3_key)
    file_size = head["ContentLength"]
    file_size_gb = file_size / GB
    filename = os.path.basename(s3_key)

    config, chunk, concurrency = get_transfer_config(file_size)
    logger.info(
        "Downloading %s (%.2f GB) [%d MB x %d threads]",
        filename, file_size_gb, chunk // MB, concurrency,
    )

    state = {"bytes": 0, "last_pct": 0}
    start = time.time()

    def _callback(n):
        state["bytes"] += n
        pct = int(state["bytes"] / file_size * 100) if file_size > 0 else 100
        if pct >= state["last_pct"] + 5:
            state["last_pct"] = pct
            elapsed = time.time() - start
            speed = (state["bytes"] / MB) / elapsed if elapsed > 0 else 0
            gb_done = state["bytes"] / GB
            logger.info(
                "  %s: %.2f/%.2f GB (%d%%) - %.0f MB/s",
                filename, gb_done, file_size_gb, pct, speed,
            )

    callback = _callback if progress else None

    s3_client.download_file(
        Bucket=bucket, Key=s3_key, Filename=local_path,
        Config=config, Callback=callback,
    )

    elapsed = time.time() - start
    mins, secs = int(elapsed // 60), int(elapsed % 60)
    avg = file_size_gb / (elapsed / 60) if elapsed > 0 else 0
    logger.info(
        "  %s downloaded in %dm %ds (%.2f GB/min)",
        filename, mins, secs, avg,
    )


def multipart_upload(s3_client, bucket, local_path, s3_key, progress=True):
    """Upload a file to S3 using multipart transfer with progress logging.

    Args:
        s3_client: A boto3 S3 client instance.
        bucket: The S3 bucket name.
        local_path: The local file path to upload.
        s3_key: The S3 object key for the destination.
        progress: Whether to log upload progress (default True).
    """
    file_size = os.path.getsize(local_path)
    file_size_gb = file_size / GB
    filename = os.path.basename(local_path)

    config, chunk, concurrency = get_transfer_config(file_size)
    logger.info(
        "Uploading %s (%.2f GB) -> %s [%d MB x %d threads]",
        filename, file_size_gb, s3_key, chunk // MB, concurrency,
    )

    state = {"bytes": 0, "last_pct": 0}
    start = time.time()

    def _callback(n):
        state["bytes"] += n
        pct = int(state["bytes"] / file_size * 100) if file_size > 0 else 100
        if pct >= state["last_pct"] + 5:
            state["last_pct"] = pct
            elapsed = time.time() - start
            speed = (state["bytes"] / MB) / elapsed if elapsed > 0 else 0
            gb_done = state["bytes"] / GB
            logger.info(
                "  %s: %.2f/%.2f GB (%d%%) - %.0f MB/s",
                filename, gb_done, file_size_gb, pct, speed,
            )

    callback = _callback if progress else None

    s3_client.upload_file(
        Filename=local_path, Bucket=bucket, Key=s3_key,
        Config=config, Callback=callback,
    )

    elapsed = time.time() - start
    mins, secs = int(elapsed // 60), int(elapsed % 60)
    avg = file_size_gb / (elapsed / 60) if elapsed > 0 else 0
    logger.info(
        "  %s uploaded in %dm %ds (%.2f GB/min)",
        filename, mins, secs, avg,
    )
