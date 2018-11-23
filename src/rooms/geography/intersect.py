def intersect(x1, y1, x2, y2, x3, y3, x4, y4):
    if (x1, y1) in ( (x3, y3), (x4, y4) ) or (x2, y2) in ( (x3, y3), (x4, y4) ):
        return False
    def same_sign(a, b):
        return a * b > 0

    a1 = y2 - y1
    b1 = x1 - x2
    c1 = (x2 * y1) - (x1 * y2)

    r3 = ((a1 * x3) + (b1 * y3) + c1)
    r4 = ((a1 * x4) + (b1 * y4) + c1)

    if (r3 != 0) and (r4 != 0) and same_sign(r3, r4):
        return False

    a2 = y4 - y3
    b2 = x3 - x4
    c2 = (x4 * y3) - (x3 * y4)

    r1 = (a2 * x1) + (b2 * y1) + c2
    r2 = (a2 * x2) + (b2 * y2) + c2

    if (r1 != 0) and (r2 != 0) and (same_sign(r1, r2)):
        return False

    denom = (a1 * b2) - (a2 * b1)

    if denom == 0:
        return False

    return True


def vertex_intersect(v1, v2, v3, v4):
    return intersect(
        v1.position.x, v1.position.y,
        v2.position.x, v2.position.y,
        v3.position.x, v3.position.y,
        v4.position.x, v4.position.y)
