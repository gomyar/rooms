
import math

DET_TOLERANCE = 0.00000001


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


def intersection_point(pt1, pt2, ptA, ptB, include_endpoints=True):
    """ this returns the intersection of Line(pt1,pt2) and Line(ptA,ptB)
        returns a tuple: (xi, yi, valid, r, s), where
        (xi, yi) is the intersection
        r is the scalar multiple such that (xi,yi) = pt1 + r*(pt2-pt1)
        s is the scalar multiple such that (xi,yi) = pt1 + s*(ptB-ptA)
            valid == 0 if there are 0 or inf. intersections (invalid)
            valid == 1 if it has a unique intersection ON the segment    """

    # DET_TOLERANCE = 0.00000001

    # the first line is pt1 + r*(pt2-pt1)
    # in component form:
    x1, y1 = pt1
    x2, y2 = pt2
    dx1 = x2 - x1
    dy1 = y2 - y1

    # the second line is ptA + s*(ptB-ptA)
    x, y = ptA
    xB, yB = ptB
    dx = xB - x
    dy = yB - y

    # we need to find the (typically unique) values of r and s
    # that will satisfy
    #
    # (x1, y1) + r(dx1, dy1) = (x, y) + s(dx, dy)
    #
    # which is the same as
    #
    #    [ dx1  -dx ][ r ] = [ x-x1 ]
    #    [ dy1  -dy ][ s ] = [ y-y1 ]
    #
    # whose solution is
    #
    #    [ r ] = _1_  [  -dy   dx ] [ x-x1 ]
    #    [ s ] = DET  [ -dy1  dx1 ] [ y-y1 ]
    #
    # where DET = (-dx1 * dy + dy1 * dx)
    #
    # if DET is too small, they're parallel
    #
    DET = (-dx1 * dy + dy1 * dx)

    if math.fabs(DET) < DET_TOLERANCE:
        return None

    # now, the determinant should be OK
    DETinv = 1.0/DET

    # find the scalar amount along the "self" segment
    r = DETinv * (-dy  * (x-x1) +  dx * (y-y1))

    # find the scalar amount along the input line
    s = DETinv * (-dy1 * (x-x1) + dx1 * (y-y1))

    # return the average of the two descriptions
    xi = (x1 + r*dx1 + x + s*dx)/2.0
    yi = (y1 + r*dy1 + y + s*dy)/2.0

    # added by ray - filters out endpoint intersects
    if include_endpoints:
        if r < 0 or s < 0:
            return None
        if r > 1.0 or s > 1.0:
            return None
    else:
        if r <= DET_TOLERANCE or s <= DET_TOLERANCE:
            return None
        if r >= (1.0-DET_TOLERANCE) or s >= (1.0-DET_TOLERANCE):
            return None

    return ( xi, yi) #, 1, r, s )


def intersect(x1, y1, x2, y2, x3, y3, x4, y4):
    return intersection_point((x1, y1), (x2, y2), (x3, y3), (x4, y4), False) is not None
