## 0. Preparación rápida (antes de empezar)

**Verificar conexión y entorno (Terminal 1):**

**1. Actualizar repositorio:**

```bash
cd ~/Desktop/my_rUBot_mecanum
git pull
```

**2. Compilar el proyecto:**

```bash
colcon build
```

**3. Cargar el entorno ROS 2:**

```bash
source install/setup.bash
```

**4. Comprobar los nodos del robot:**

```bash
ros2 node list
```

Deben aparecer los 5 nodos del robot.

---

## 1. Práctica A4 / 03a: Wall Follower (Diferencial, Holonómico y Mejorado)

Parar siempre el controlador actual con `Ctrl+C` antes de lanzar el siguiente.

### 1. Wall Follower Diferencial

```bash
ros2 launch my_robot_control my_robot_wallfollower_differential.launch.xml
```

### 2. Wall Follower Holonómico (simple)

```bash
ros2 launch my_robot_control my_robot_wallfollower_holonomic.launch.py
```

### 3. Wall Follower Holonómico Mejorado (con evasión de obstáculos)

```bash
ros2 launch my_robot_control my_robot_wallfollower_holonomic_obstacle.launch.py
```

---

## 2. Práctica 04-A: Mapeo del entorno (SLAM Cartographer)

### T1 — Reset odom + SLAM

```bash
ros2 topic pub --once /reset_odom std_msgs/msg/Bool "{data: true}"
```

A continuación, lanzar Cartographer:

```bash
ros2 launch my_robot_cartographer cartographer.launch.py use_sim_time:=false
```

### T2 — Teleop despacio (recorrer zona y volver al origen)

En una segunda terminal:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### T3 — Guardar mapa (sin pisar `my_lab_map`)

En una tercera terminal:

```bash
cd ~/Desktop/my_rUBot_mecanum/src/Navigation_Projects/my_robot_navigation2/map/
```

Guardar el mapa con un nombre diferente:

```bash
ros2 run nav2_map_server map_saver_cli -f my_demo_map
```

**Finalizar la práctica:** Cerrar los procesos de SLAM (T1) y teleoperación (T2) con `Ctrl+C`.


## 3. Práctica 04-B: Navegación Autónoma (Nav2)

### Navegación manual (RViz)

**T1 — Colocar el robot en `[0, 0, 0]` del mapa, resetear y lanzar Nav2:**

```bash
ros2 topic pub --once /reset_odom std_msgs/msg/Bool "{data: true}"
```

Lanzar Nav2:

```bash
ros2 launch my_robot_navigation2 navigation2_robot.launch.py use_sim_time:=false map_file:=mapB3_lab.yaml params_file:=rubot_real_lidar_nav.yaml
```

**En RViz: (OPCIONAL)**

- Ajustar la posición inicial con **2D Pose Estimate**, si hace falta.
- Enviar destinos con **Nav2 Goal**.
- También se pueden utilizar **Waypoint** o **Nav Through Poses**.

### Navegación por Waypoints (Simple Commander)

**T2&#x20;**

Lanzar la navegación por waypoints:

```bash
ros2 launch my_robot_nav_control nav_waypoints.launch.py wp_file:=waypoints_hw.yaml
```


## 5. Práctica 05b: Integración Total (YOLO + Nav2)

### Terminal 1 — Start localization and Nav2

```bash
ros2 topic pub --once /reset_odom std_msgs/msg/Bool "{data: true}"
```

```bash
ros2 launch my_robot_navigation2 navigation2_robot.launch.py \
  use_sim_time:=false \
  map_file:=mapB3_lab.yaml \
  params_file:=rubot_real_lidar_nav.yaml
```

Place the physical robot at the configured initial pose. Verify its pose and costmaps in RViz. Use **2D Pose Estimate** when necessary.

### Terminal 2 — Validate navigation with manual messages

Start the real route configuration:

```bash
ros2 launch my_robot_ai_navigation traffic_sign_navigation.launch.py \
  config_file:=traffic_sign_navigation_real.yaml
```

When the robot reaches the inspection pose, publish a traffic sign manually:

**Publish `left`:**

```bash
ros2 topic pub --once /traffic_sign std_msgs/msg/String "{data: left}"
```

**Publish `right`:**

```bash
ros2 topic pub --once /traffic_sign std_msgs/msg/String "{data: right}"
```

**Publish `stop`:**

```bash
ros2 topic pub --once /traffic_sign std_msgs/msg/String "{data: stop}"
```

**Publish `unknown`:**

```bash
ros2 topic pub --once /traffic_sign std_msgs/msg/String "{data: unknown}"
```

Do not continue until the inspection, left, right, stop and unknown cases are safe with manual messages.

### Terminal 3 — Add the real YOLO classifier

Activate the YOLO environment:

```bash
cd ~/my_rUBot_mecanum
source /opt/ros/humble/setup.bash
source .venv-yolo/bin/activate
source install/setup.bash
```

Start the detector with the real camera topic:

```bash
ros2 launch my_robot_ai_perception traffic_sign_classifier.launch.py \
  config_file:=traffic_sign_classifier_real.yaml
```

### Terminal 4 — Monitor traffic sign topic (optional)

```bash
ros2 topic echo /traffic_sign
```
