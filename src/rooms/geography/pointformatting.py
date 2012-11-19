
def format_point(astar, point_map):
    out = "\nPointMap: width: %s, height: %s\n" % (
        point_map.width, point_map.height)

    for y in range(point_map.top, point_map.top+ point_map.height, point_map.point_spacing):
        for x in range(point_map.left, point_map.left+ point_map.width, point_map.point_spacing):
            point = point_map._points[x, y]
            out += "%3d      |" % (point.f(),)
        out += "\n"
        for x in range(point_map.left, point_map.left+ point_map.width, point_map.point_spacing):
            point = point_map._points[x, y]
            out += "         |"
        out += "\n"
        for x in range(point_map.left, point_map.left+ point_map.width, point_map.point_spacing):
            point = point_map._points[x, y]
            if point.passable:
                if point in astar.open_list:
                    out += "    O    |"
                elif point in astar.closed_list:
                    out += "    C    |"
                else:
                    out += "         |"
            else:
                out += "    X    |"
        out += "\n"
        for x in range(point_map.left, point_map.left+ point_map.width, point_map.point_spacing):
            point = point_map._points[x, y]
            out += "         |"
        out += "\n"
        for x in range(point_map.left, point_map.left+ point_map.width, point_map.point_spacing):
            point = point_map._points[x, y]
            out += "%3d   %3d|" % (point._g,point._h)
        out += "\n"
        for x in range(point_map.left, point_map.left+ point_map.width, point_map.point_spacing):
            out += "----------"
        out += "\n"
    return out
