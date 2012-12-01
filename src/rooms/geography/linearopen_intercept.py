
from rooms.waypoint import Path


def plot_intercept_point(position, speed, targetPos, targetDest,
        targetSpeed):
    target_start_point = targetPos
    halfway_point = targetDest
    for i in range(20):
        halfway_point = (targetPos[0] + (targetDest[0] - targetPos[0]) / 2.0,
            targetPos[1] + (targetDest[1] - targetPos[1]) / 2.0)
        halfway_eta = calculate_time_to_dest(position, halfway_point, speed)
        target_halfway_eta = calculate_time_to_dest(target_start_point,
            halfway_point, targetSpeed)
        if abs(halfway_eta - target_halfway_eta) < 0.005:
            return halfway_point
        elif halfway_eta < target_halfway_eta:
            targetDest = halfway_point
        elif halfway_eta >= target_halfway_eta:
            targetPos = halfway_point
    return halfway_point


def plot_intercept_point_from(path, point, speed):
    path_position = (path.x(), path.y())
    intercept = plot_intercept_point(point, speed, path_position,
        path.path[-1][0], path.speed)
    return intercept


def match_path_from(path, point, speed):
    if not path.path:
        return []
    path = list(path.path)
    while path[1:]:
        (start, starttime), (end, endtime) = path[:2]
        if path.time_to_move(point, end, speed) < endtime:
            intercept = plot_intercept_point_from(path, point, speed)
            newpath = Path()
            newpath.path.append((intercept, path.time_to_move(point,
                intercept, speed)))
            newpath.path.extend([p for p in path[1:]])
            return newpath
        path.pop(0)

    return Path()


