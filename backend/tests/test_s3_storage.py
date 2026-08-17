from pathlib import Path

from app.ingestion.storage import S3SourceStorage
from app.jobs.storage import S3HtmlStorage


class MemoryBody:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def read(self) -> bytes:
        return self.content


class FakeS3:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}

    def put_object(self, *, Bucket: str, Key: str, Body, **kwargs) -> None:
        self.objects[(Bucket, Key)] = Body if isinstance(Body, bytes) else bytes(Body)

    def delete_object(self, *, Bucket: str, Key: str) -> None:
        self.objects.pop((Bucket, Key), None)

    def download_file(self, bucket: str, key: str, destination: str) -> None:
        Path(destination).write_bytes(self.objects[(bucket, key)])

    def get_object(self, *, Bucket: str, Key: str):
        return {"Body": MemoryBody(self.objects[(Bucket, Key)])}

    def head_object(self, *, Bucket: str, Key: str):
        return {"ContentLength": len(self.objects[(Bucket, Key)])}

    def generate_presigned_url(self, operation: str, Params: dict, ExpiresIn: int) -> str:
        assert operation == "put_object"
        assert ExpiresIn == 900
        return f"https://storage.invalid/{Params['Key']}"


def test_s3_source_round_trip_uses_opaque_key() -> None:
    client = FakeS3()
    storage = S3SourceStorage(client=client, bucket="synthetic-bucket")

    source_id = storage.save(".mp3", b"ID3synthetic")
    with storage.materialize(source_id, ".mp3") as source:
        assert source.read_bytes() == b"ID3synthetic"

    key = next(iter(client.objects))[1]
    assert key == f"sources/{source_id}.mp3"
    storage.delete(source_id, ".mp3")
    assert client.objects == {}


def test_s3_source_creates_presigned_upload_and_reads_size() -> None:
    client = FakeS3()
    storage = S3SourceStorage(client=client, bucket="synthetic-bucket")
    source_id = "46b91c44-1cd0-49fe-a915-e7b721fd3855"

    url = storage.create_upload(source_id, ".mp4", "video/mp4", 900)
    client.objects[("synthetic-bucket", f"sources/{source_id}.mp4")] = b"synthetic"

    assert url.endswith(f"sources/{source_id}.mp4")
    assert storage.size(source_id, ".mp4") == 9


def test_s3_html_round_trip() -> None:
    client = FakeS3()
    storage = S3HtmlStorage(client=client, bucket="synthetic-bucket")

    key = storage.save("job-id", "<!doctype html><title>Sintético</title>")

    assert key == "html/job-id.html"
    assert storage.load(key).decode().startswith("<!doctype html>")
    storage.delete(key)
    assert client.objects == {}
