import uuid

def generate_name(ext):
    filename = str(uuid.uuid4()) + "." + ext
    return filename


