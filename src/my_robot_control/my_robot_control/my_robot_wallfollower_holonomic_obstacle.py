#!/usr/bin/env python3
"""Holonomic obstacle wall follower with terminal logging per LiDAR region."""

# We import the needed packages.
import math

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import LaserScan
from tf_transformations import euler_from_quaternion


def clamp(value, low, high):
    return max(low, min(high, value))


class HolonomicObstacleWallFollower(Node):
    """LiDAR processing, state machine and control laws."""

    def __init__(self):
        super().__init__('holonomic_obstacle_wall_follower')

        # Desired distance between the robot and the right wall (m).
        self.follow_distance = float(
            self.declare_parameter('follow_distance', 0.35).value
        )
        # Maximum lateral distance used to classify a short obstacle (m).
        self.max_front_length = float(
            self.declare_parameter('max_front_length', 0.50).value
        )
        # Forward velocity (m/s).
        self.forward_speed = float(
            self.declare_parameter('forward_speed', 0.20).value
        )
        # Maximum lateral velocity (m/s).
        self.lateral_speed = float(
            self.declare_parameter('lateral_speed', 0.20).value
        )
        # Turn speed and maximum angular correction (rad/s).
        self.turn_speed = float(
            self.declare_parameter('turn_speed', 1.00).value
        )
        # Maximum LiDAR distance considered (m).
        self.detection_limit = float(
            self.declare_parameter('detection_limit', 1.20).value
        )
        # Proportional gain for lateral-distance correction.
        self.lateral_gain = float(
            self.declare_parameter('lateral_gain', 2.0).value
        )
        # Proportional gain for angular alignment.
        self.alignment_gain = float(
            self.declare_parameter('alignment_gain', 2.0).value
        )

        self.RIGHT = 'RIGHT'
        self.FRONT = 'FRONT'
        self.FRONT_RIGHT = 'FRONT_RIGHT'
        self.BACK_RIGHT = 'BACK_RIGHT'

        self.diagonal_factor = 0.5
        self.region_confirmations = 3
        self.robust_rays = 3

        self.state = self.RIGHT
        self.obstacle_is_long = False
        self.passing_short_obstacle = False
        self.command = Twist()
        self.odom_pose = None
        self.front_start_pose = None
        self.right_angle = None

        self.region_candidate = None
        self.region_candidate_count = 0
        self.stable_region = None

        # Logging state.
        self._action = 'Idle'
        self._last_logged = None
        self._shutting_down = False

        self.create_subscription(
            LaserScan, '/scan', self.scan_callback, qos_profile_sensor_data
        )
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.timer = self.create_timer(0.05, self.publish_command)
        self.info_timer = self.create_timer(1.0, self.log_info)

        self.get_logger().info(
            'Holonomic obstacle wall follower started.'
        )

    def publish_command(self):
        if not self._shutting_down:
            self.publisher.publish(self.command)

    def describe_action(self, measurements, closest, cmd):
        """Build a log line for the current state and its velocities."""
        def fmt(region):
            d, _ = measurements[region]
            return 'inf' if math.isinf(d) else f'{d:.2f}'

        regions = (
            f'F={fmt(self.FRONT)} FR={fmt(self.FRONT_RIGHT)} '
            f'R={fmt(self.RIGHT)} BR={fmt(self.BACK_RIGHT)} m'
        )
        cmd_txt = (
            f'vx={cmd.linear.x:.2f}, vy={cmd.linear.y:.2f}, '
            f'w={cmd.angular.z:.2f}'
        )

        if self.state == self.RIGHT:
            angle = measurements[self.RIGHT][1]
            angle_txt = f', angle={angle:.1f} deg' if angle is not None else ''
            mode = (
                'temporary RIGHT (short obstacle, w=0)'
                if self.passing_short_obstacle else 'RIGHT wall'
            )
            label = f'{mode} {fmt(self.RIGHT)} m{angle_txt}'
        elif self.state == self.FRONT:
            label = (
                f'FRONT {fmt(self.FRONT)} m -> moving LEFT, '
                f'progress={self.lateral_progress():.2f} m'
            )
        elif self.state == self.FRONT_RIGHT:
            if self.obstacle_is_long:
                label = (
                    f'FRONT-RIGHT {fmt(self.FRONT_RIGHT)} m '
                    f'-> long wall, turn LEFT'
                )
            else:
                label = (
                    f'FRONT-RIGHT {fmt(self.FRONT_RIGHT)} m '
                    f'-> short obstacle, diagonal'
                )
        else:  # BACK_RIGHT
            label = f'BACK-RIGHT {fmt(self.BACK_RIGHT)} m -> recovering wall'

        return f'{label} | {cmd_txt} | {regions} | closest={closest}'

    def log_info(self):
        if not self._shutting_down:
            self.get_logger().info(self._action)

    def odom_callback(self, msg):
        """Store planar pose (x, y, yaw) from odometry."""
        position = msg.pose.pose.position
        orientation = msg.pose.pose.orientation
        quaternion = [
            orientation.x,
            orientation.y,
            orientation.z,
            orientation.w,
        ]
        _, _, yaw = euler_from_quaternion(quaternion)
        self.odom_pose = (position.x, position.y, yaw)

    def region_measurements(self, scan):
        """Return robust distances and angles for the four LiDAR regions."""
        # Each valid ray is stored as (distance, angle_deg).
        rays = {
            self.FRONT: [],
            self.FRONT_RIGHT: [],
            self.RIGHT: [],
            self.BACK_RIGHT: [],
        }

        for i, distance in enumerate(scan.ranges):
            # Ignore invalid (nan/inf) and out-of-range measurements.
            if not math.isfinite(distance):
                continue
            if distance < scan.range_min or distance > scan.range_max:
                continue

            # Ray angle in degrees, normalised to [-180, 180).
            angle = math.degrees(scan.angle_min + i * scan.angle_increment)
            angle = (angle + 180.0) % 360.0 - 180.0

            if -20.0 <= angle <= 20.0:
                rays[self.FRONT].append((distance, angle))
            elif -70.0 <= angle < -20.0:
                rays[self.FRONT_RIGHT].append((distance, angle))
            elif -110.0 <= angle < -70.0:
                rays[self.RIGHT].append((distance, angle))
            elif -160.0 <= angle < -110.0:
                rays[self.BACK_RIGHT].append((distance, angle))

        # Mean distance and mean angle of the nearest valid rays per region.
        measurements = {}
        for region, region_rays in rays.items():
            if not region_rays:
                measurements[region] = (math.inf, None)
                continue
            nearest = sorted(region_rays)[:self.robust_rays]
            mean_distance = sum(r[0] for r in nearest) / len(nearest)
            mean_angle = sum(r[1] for r in nearest) / len(nearest)
            measurements[region] = (mean_distance, mean_angle)
        return measurements

    def closest_region(self, measurements):
        """Return the closest region inside detection_limit."""
        closest = None
        closest_distance = math.inf
        for region, (distance, _) in measurements.items():
            # Ignore regions whose distance is not below detection_limit.
            if distance >= self.detection_limit:
                continue
            if distance < closest_distance:
                closest_distance = distance
                closest = region
        return closest

    def confirmed_region(self, measurements):
        """Confirm a region change over several consecutive scans."""
        closest = self.closest_region(measurements)

        if closest == self.region_candidate:
            self.region_candidate_count += 1
        else:
            self.region_candidate = closest
            self.region_candidate_count = 1

        if self.region_candidate_count >= self.region_confirmations:
            self.stable_region = self.region_candidate

        return self.stable_region

    def lateral_progress(self):
        """Return travel along the robot's initial lateral axis."""
        if self.front_start_pose is None or self.odom_pose is None:
            return 0.0
        x0, y0, yaw0 = self.front_start_pose
        x, y, _ = self.odom_pose
        dx = x - x0
        dy = y - y0
        return abs(-math.sin(yaw0) * dx + math.cos(yaw0) * dy)

    def follow_right(self, measurements, closest, cmd):
        """Follow the wall using lateral and angular correction."""
        # A frontal obstacle starts the lateral bypass.
        if closest == self.FRONT:
            self.state = self.FRONT
            self.obstacle_is_long = False
            self.passing_short_obstacle = False
            self.front_start_pose = self.odom_pose
            self.follow_front(measurements, closest, cmd)
            return

        # Short obstacle: the corner is behind the robot, finish the bypass.
        if self.passing_short_obstacle and closest == self.BACK_RIGHT:
            self.state = self.BACK_RIGHT
            self.follow_back_right(measurements, closest, cmd)
            return

        distance, angle = measurements[self.RIGHT]
        self.right_angle = angle

        cmd.linear.x = self.forward_speed

        if distance < self.detection_limit:
            # Lateral distance correction (right wall -> negative vy).
            error = distance - self.follow_distance
            cmd.linear.y = -clamp(
                self.lateral_gain * error,
                -self.lateral_speed,
                self.lateral_speed,
            )

            # Angular alignment: move the closest right angle towards -90 deg.
            # It is disabled while passing a short obstacle (w = 0), because
            # the closest point belongs to the obstacle corner.
            if not self.passing_short_obstacle:
                angle_error = math.radians(angle + 90.0)
                cmd.angular.z = clamp(
                    self.alignment_gain * angle_error,
                    -self.turn_speed,
                    self.turn_speed,
                )

    def follow_front(self, measurements, closest, cmd):
        """Move laterally and classify the obstacle as short or long."""
        if self.front_start_pose is None:
            self.front_start_pose = self.odom_pose

        # Stop forward motion and move left.
        cmd.linear.x = 0.0
        cmd.linear.y = self.lateral_speed

        progress = self.lateral_progress()

        if closest != self.FRONT and progress < self.max_front_length:
            # FRONT cleared before max_front_length: short obstacle.
            self.passing_short_obstacle = True
            self.obstacle_is_long = False
            self.state = self.FRONT_RIGHT
            self.follow_front_right(measurements, closest, cmd)
        elif progress >= self.max_front_length:
            # Lateral progress reached max_front_length: long wall.
            self.passing_short_obstacle = False
            self.obstacle_is_long = True
            self.state = self.FRONT_RIGHT
            self.follow_front_right(measurements, closest, cmd)

    def follow_front_right(self, measurements, closest, cmd):
        """Move diagonally around the front-right side."""
        if self.obstacle_is_long:
            # Long wall: turn left until it becomes the new right wall.
            cmd.linear.x = 0.0
            cmd.linear.y = 0.0
            if closest == self.RIGHT:
                self.obstacle_is_long = False
                self.passing_short_obstacle = False
                self.state = self.RIGHT
                self.follow_right(measurements, closest, cmd)
            else:
                cmd.angular.z = self.turn_speed
            return

        # Short obstacle transitions.
        if closest == self.FRONT:
            self.state = self.FRONT
            self.passing_short_obstacle = False
            self.front_start_pose = self.odom_pose
            self.follow_front(measurements, closest, cmd)
            return
        if closest == self.RIGHT:
            # Temporary RIGHT phase (passing_short_obstacle stays True).
            self.state = self.RIGHT
            self.follow_right(measurements, closest, cmd)
            return
        if closest == self.BACK_RIGHT:
            self.state = self.BACK_RIGHT
            self.follow_back_right(measurements, closest, cmd)
            return

        # Move forward with a limited proportional lateral correction
        # using the FRONT_RIGHT distance.
        cmd.linear.x = self.forward_speed
        distance = measurements[self.FRONT_RIGHT][0]
        if distance < self.detection_limit:
            limit = self.diagonal_factor * self.lateral_speed
            error = distance - self.follow_distance
            cmd.linear.y = -clamp(self.lateral_gain * error, -limit, limit)

    def follow_back_right(self, measurements, closest, cmd):
        """Complete the bypass and recover the right wall."""
        if closest == self.RIGHT:
            # RIGHT recovered: enable angular alignment again.
            self.passing_short_obstacle = False
            self.state = self.RIGHT
            self.follow_right(measurements, closest, cmd)
            return
        if closest == self.FRONT:
            self.state = self.FRONT
            self.passing_short_obstacle = False
            self.front_start_pose = self.odom_pose
            self.follow_front(measurements, closest, cmd)
            return

        # Diagonal motion: forward and towards the right wall.
        cmd.linear.x = self.forward_speed
        cmd.linear.y = -self.diagonal_factor * self.lateral_speed

    def scan_callback(self, scan):
        """Read the LiDAR and calculate the next velocity command."""
        if self._shutting_down:
            return

        measurements = self.region_measurements(scan)
        closest = self.confirmed_region(measurements)

        cmd = Twist()

        if self.state == self.RIGHT:
            self.follow_right(measurements, closest, cmd)
        elif self.state == self.FRONT:
            self.follow_front(measurements, closest, cmd)
        elif self.state == self.FRONT_RIGHT:
            self.follow_front_right(measurements, closest, cmd)
        elif self.state == self.BACK_RIGHT:
            self.follow_back_right(measurements, closest, cmd)

        self.command = cmd

        self._action = self.describe_action(measurements, closest, cmd)

        # Log immediately on every state / sub-state change.
        key = (self.state, self.passing_short_obstacle, self.obstacle_is_long)
        if key != self._last_logged:
            self.get_logger().info(self._action)
            self._last_logged = key

    def stop(self):
        """Publish a final zero command."""
        self._shutting_down = True
        self.command = Twist()
        for timer in (self.timer, self.info_timer):
            try:
                timer.cancel()
            except Exception:
                pass
        try:
            self.publisher.publish(self.command)
        except Exception:
            pass


def main(args=None):
    rclpy.init(
        args=args,
        signal_handler_options=SignalHandlerOptions.NO,
    )
    node = HolonomicObstacleWallFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
