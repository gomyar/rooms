
from rooms.waypoint import Path
from rooms.waypoint import distance
from rooms.waypoint import path_from_waypoints
from rooms.waypoint import get_now
import math

import logging
log = logging.getLogger("rooms.intercept")


def plot_intercept_point(position, speed, targetPos, targetDest,
        targetSpeed):
    log.info("plot_intercept_point(%s, %s, %s, %s, %s)", position, speed,
        targetPos, targetDest, targetSpeed)
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


def calculate_time_to_dest(startposition, destination, speed):
    if speed == 0.0:
        return 0.0
    distance = math.hypot(destination[0] - startposition[0],
        destination[1] - startposition[1])
    return distance / speed


def plot_intercept_point_from(path, point, speed):
    path_position = (path.x(), path.y())
    intercept = plot_intercept_point(point, speed, path_position,
        (path.path[-1][0], path.path[-1][1]), path.speed())
    return intercept


def time_to_move(x1, y1, x2, y2, speed):
    return distance(x1, y1, x2, y2) / speed


def match_path_from(target_path, point, speed):
    if not target_path.path:
        return []
    path = list(target_path.path)
    log.debug("Intercept: matching path %s from %s at speed %s", path,
        point, speed)
    while path[1:]:
        (start_x, start_y, starttime), (end_x, end_y, endtime) = path[:2]
        if get_now() + time_to_move(point[0], point[1], end_x, end_y, speed) < endtime:
            i_x, i_y= plot_intercept_point_from(target_path, point, speed)
            newpath = Path()
            newpath.path.append((point[0], point[1], get_now()))
            newpath.path.append((i_x, i_y, get_now() + time_to_move(point[0], point[1],
                i_x, i_y, speed)))
            newpath.path.extend([p for p in path[1:]])
            return newpath
        path.pop(0)

    return path_from_waypoints([point, target_path.path[-1][:2]], speed)


