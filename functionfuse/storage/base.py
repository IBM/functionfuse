# checksum is copied from
# https://stackoverflow.com/questions/1653897/if-pickling-was-interrupted-will-unpickling-necessarily-always-fail-python

import hashlib
import pickle
import io, copyreg


class StorageWithSerializers:
    def __init__(self):
        self.reduced_serializers = {}
        self.persistent_serializers = {}
        self.persistent_classes = {}

    def have_serializers(self):
        return bool(self.persistent_serializers) or bool(self.reduced_serializers)

    def register_persistent_serializers(self, *serializers):
        self.persistent_serializers.update({i.serializer_class: i for i in serializers})
        self.persistent_classes.update({i.name: i for i in serializers})

    def pickle(self, obj, protocols):
        return safepickle(
            obj, self.persistent_serializers, protocols, self.reduced_serializers
        )

    def unpickle(self, data, protocols):
        return safeunpickle(data, self.persistent_classes, protocols)

    def remove_persistent_storage(self, data, protocols):
        remove(data, self.persistent_classes, protocols)


_HASHLEN = 20


class InvalidPickle(ValueError):
    pass


class PersistentPickler(pickle.Pickler):
    def __init__(self, stream, serializers, protocols):
        super(PersistentPickler, self).__init__(stream)
        self.serializers = serializers
        self.protocols = protocols

    def persistent_id(self, obj):
        serializer = self.serializers.get(type(obj), None)
        if serializer:
            return serializer.pickle(obj, self.protocols)
        else:
            return None


class PersistentUnpickler(pickle.Unpickler):
    def __init__(self, file, serializers, protocols):
        super().__init__(file)
        self.serializers, self.protocols = serializers, protocols

    def persistent_load(self, pid):
        tag, unpickle_pid = pid
        serializer = self.serializers.get(tag, None)

        if serializer:
            return serializer.unpickle(unpickle_pid, self.protocols)
        else:
            raise pickle.UnpicklingError(
                f"Deserialization error, unsupported persistent object {tag}."
            )


class PersistentUnpicklerRemover(pickle.Unpickler):
    def __init__(self, file, serializers, protocols):
        super().__init__(file)
        self.serializers, self.protocols = serializers, protocols

    def persistent_load(self, pid):
        tag, unpickle_pid = pid
        serializer = self.serializers.get(tag, None)

        if serializer:
            return serializer.remove(unpickle_pid, self.protocols)
        else:
            raise pickle.UnpicklingError(
                f"Deserialization error, unsupported persistent object {tag}."
            )


def init_serializers(serializer_classes, path, node_name):
    serializers = [i(path, node_name) for i in serializer_classes]
    return serializers


def safepickle(obj, persistent_serializers, protocols, reduced_serializers):
    if persistent_serializers or reduced_serializers:
        stream = io.BytesIO()
        p = (
            PersistentPickler(stream, persistent_serializers, protocols)
            if persistent_serializers
            else pickle.Pickler(stream)
        )

        if reduced_serializers:
            p.dispatch_table = copyreg.dispatch_table.copy()
            for i in reduced_serializers:
                p.dispatch_table[i.serializer_class] = i.reduce

        p.dump(obj)
        stream.seek(0)
        s = stream.read()
    else:
        s = pickle.dumps(obj)
    s += hashlib.sha1(s).digest()
    return s


def safeunpickle(pstr, persistent_serializers, protocols):
    data, checksum = pstr[:-_HASHLEN], pstr[-_HASHLEN:]
    if hashlib.sha1(data).digest() != checksum:
        raise InvalidPickle("Pickle hash does not match!")
    if persistent_serializers:
        stream = io.BytesIO(data)
        obj = PersistentUnpickler(stream, persistent_serializers, protocols).load()
        return obj
    return pickle.loads(data)


def remove(pstr, persistent_serializers, protocols):
    data, checksum = pstr[:-_HASHLEN], pstr[-_HASHLEN:]
    if hashlib.sha1(data).digest() != checksum:
        return

    stream = io.BytesIO(data)
    PersistentUnpicklerRemover(stream, persistent_serializers, protocols).load()
