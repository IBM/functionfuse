import uuid


def generate_name():
    filename = str(uuid.uuid4())
    return filename


FILE_PROTOCOL = "file_protocol"
S3_PROTOCOL = "s3 protocol"
