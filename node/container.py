
import jsonpickle

def _encode(area):
    return jsonpickle.encode(area)

def _decode(pickled_area):
    return jsonpickle.decode(pickled_area)

def load_area(filename):
    return _decode(open(filename).read())

def save_area(area, filename):
    encoded = _encode(area)
    out = open(filename, "w")
    out.write(encoded)
    out.close()
