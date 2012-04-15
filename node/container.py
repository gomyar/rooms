
import jsonpickle

def load_area(filename):
    return jsonpickle.decode(open(filename).read())

def save_area(area, filename):
    encoded = jsonpickle.encode(area)
    out = open(filename, "w")
    out.write(encoded)
    out.close()
