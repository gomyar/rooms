
from .intersect import is_between_tuple


def triarea2(a, b, c):
    ax = b[0] - a[0]
    ay = b[1] - a[1]
    bx = c[0] - a[0]
    by = c[1] - a[1]
    return bx*ay - ax*by


def funnel_poly_chain(portals, from_pos, to_pos):
    pts = []
    # Find straight path.

    # setup portals list
    portals.insert(0, (from_pos, from_pos))
    portals.append((to_pos, to_pos))

    # Init scan state
    portalApex = from_pos
    portalLeft, portalRight = from_pos, from_pos

    # Add start point.
    pts.append(from_pos)

    leftIndex = 0
    rightIndex = 0
    apexIndex = 0
    index = 0
    while index < len(portals):
        right, left = portals[index]

        # Update right vertex.
        if triarea2(portalApex, portalRight, right) <= 0.0:
            if portalApex == portalRight or triarea2(portalApex, portalLeft, right) > 0.0 or is_between_tuple(portalLeft, right, portalApex):
                # Tighten the funnel.
                portalRight = right
                rightIndex = index
            else:
                # Right over left, insert left to path and restart scan from portal left point.
                pts.append(portalLeft)
                # Make current left the new apex.
                portalApex = portalLeft
                apexIndex = leftIndex
                # Reset portal
                portalLeft = portalApex
                portalRight = portalApex
                leftIndex = apexIndex
                rightIndex = apexIndex
                # Restart scan
                index = apexIndex + 1
                continue

        # Update left vertex.
        if triarea2(portalApex, portalLeft, left) >= 0.0:
            if portalApex == portalLeft or triarea2(portalApex, portalRight, left) < 0.0 or is_between_tuple(portalRight, left, portalApex):
                # Tighten the funnel.
                portalLeft = left
                leftIndex = index
            else:
                # Left over right, insert right to path and restart scan from portal right point.
                pts.append(portalRight)
                # Make current right the new apex.
                portalApex = portalRight
                apexIndex = rightIndex
                # Reset portal
                portalLeft = portalApex
                portalRight = portalApex
                leftIndex = apexIndex
                rightIndex = apexIndex
                # Restart scan
                index = apexIndex + 1
                continue

        index += 1

    pts.append(to_pos)
    return pts
