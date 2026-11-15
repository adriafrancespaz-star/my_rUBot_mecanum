# Demo rUBot en 3 partes (versión corta)

1. Movimiento holonómico + teclado
2. Mapeo (SLAM) y navegación a waypoints con obstáculos
3. Reconocer señales y obedecerlas

> ⚠️ = recomendación mía para demo real (no viene de los documentos). Ajusta a tu robot.

---

## 0. Antes de empezar (una vez)

- Robot encendido, PC en wifi `Robotics_UB`.
- VS Code: `File > Open Folder…` → `~/Desktop/my_rUBot_mecanum`. Terminal nuevo: `` Ctrl+Shift+` ``; dividir: `Ctrl+Shift+5`.
- Actualizar y compilar:

```bash
git pull
colcon build --symlink-install
source install/setup.bash
```

- `.bashrc` con `ROS_DOMAIN_ID` (tu grupo) y `ROS_STATIC_PEERS` (IP del robot: 14, 24, 34 o 44). Comprueba conexión:

```bash
ros2 node list      # deben salir los 5 nodos del robot
```

- Zona despejada y alguien con la mano cerca del robot.

---

## PARTE 1: Movimiento holonómico y teclado

**Terminales: 1**

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p speed:=0.15 -p turn:=0.5
```

| Tecla | Movimiento |
|---|---|
| `i` / `,` | adelante / atrás |
| `j` / `l` | girar izquierda / derecha |
| **`J` / `L`** (Shift) | **desplazamiento lateral** (holonómico) |
| **`U` `O` `M` `>`** (Shift) | **diagonales** |
| `k` | **parar** |
| `q` / `z` | subir / bajar velocidades |

Opcional, movimiento lateral programado (≈30 cm a la izquierda):

```bash
ros2 launch my_robot_control my_robot_control.launch.xml vx:=0.0 vy:=0.1 w:=0.0 td:=3.0
```

Parar: `k` (teleop) o `Ctrl+C`.

---

## PARTE 2: Mapa con SLAM y navegación con obstáculos

### 2.A Crear el mapa

Coloca el robot en el punto que será el origen y no lo muevas.

**Terminal 1:**

```bash
ros2 topic pub --once /reset_odom std_msgs/msg/Bool "{data: true}"
ros2 launch my_robot_cartographer cartographer.launch.py use_sim_time:=false
```

**Terminal 2** (despacio, ⚠️):

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p speed:=0.1 -p turn:=0.4
```

Recorre el entorno y vuelve cerca del inicio. **Terminal 3:** guardar (nombre nuevo, para no pisar la plantilla):

```bash
cd ~/Desktop/my_rUBot_mecanum/src/Navigation_Projects/my_robot_navigation2/map/
ros2 run nav2_map_server map_saver_cli -f my_demo_map
cd ~/Desktop/my_rUBot_mecanum
```

Luego **para Cartographer (`Ctrl+C`) y cierra el teleop** antes de pasar a Nav2. Recompila para que se instale el mapa nuevo:

```bash
colcon build --symlink-install --packages-select my_robot_navigation2
source install/setup.bash
```

> Si prefieres usar el mapa plantilla del profe, salta a 2.B con `map_file:=my_lab_map.yaml`.

### 2.B Navegar con Nav2

Coloca el robot en el **mismo punto de origen del mapa**, quieto.

**Terminal 1:**

```bash
ros2 topic pub --once /reset_odom std_msgs/msg/Bool "{data: true}"
ros2 launch my_robot_navigation2 navigation2_robot.launch.py use_sim_time:=false map_file:=my_demo_map.yaml params_file:=rubot_real_lidar_nav.yaml
```

En RViz, si no está bien localizado: **2D Pose Estimate**. Luego **Nav2 Goal** (clic y arrastre) en una zona libre.

**Obstáculos:** Nav2 usa el LiDAR para esquivarlos. Mientras avanza, pon una caja delante: debe replanificar.

### 2.C Waypoints programados

Edita `src/Navigation_Projects/my_robot_nav_control/config/waypoints_hw.yaml` con **tus** coordenadas:

```yaml
initial_pose: [0.0, 0.0, 0.0]     # donde está el robot (mapa)
waypoints:
  - [X1, Y1, YAW1]
final_pose: [XF, YF, YAWF]
```

Reglas:
- `[x, y, yaw]` en frame `map`; metros y **radianes** (1.57 ≈ 90°).
- Los valores de ejemplo de los documentos son de simulación: **no los copies**. Saca coordenadas con la herramienta **Publish Point** de RViz + `ros2 topic echo /clicked_point` sobre zonas libres (blancas), lejos de paredes.
- ⚠️ Primero 1 waypoint cercano (≤1 m), luego la ruta completa.
- Recompila tras editar:

```bash
colcon build --symlink-install --packages-select my_robot_nav_control
source install/setup.bash
```

**Terminal 2** (con Nav2 activo):

```bash
ros2 launch my_robot_nav_control nav_waypoints.launch.py wp_file:=waypoints_hw.yaml
```

Parar: `Ctrl+C` en ambos terminales.

---

## PARTE 3: Reconocer señales y hacerles caso

### 3.0 Preparación (una vez)

```bash
python3 -m venv --system-site-packages .venv-yolo
source .venv-yolo/bin/activate
python -m pip install --upgrade pip
python -m pip install ultralytics "numpy<2.0"

source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select my_robot_ai_perception my_robot_ai_navigation
source install/setup.bash
```

### 3.1 Configurar rutas

Edita `src/AI_Projects/my_robot_ai_navigation/config/traffic_sign_navigation_real.yaml` con tus coordenadas (mismo mapa que la parte 2):

```yaml
traffic_sign_navigation:
  ros__parameters:
    use_sim_time: false            # obligatorio en real
    initial_pose: [X0, Y0, YAW0]   # donde colocas el robot
    inspection_pose: [XI, YI, YAWI]  # mirando a la señal
    left_waypoint: [XL, YL, YAWL]
    right_waypoint: [XR, YR, YAWR]
    final_pose: [XF, YF, YAWF]
    stop_duration: 3.0
```

La `inspection_pose` debe **mirar a la señal** y los waypoints deben estar en zonas libres. Recompila tras editar (`colcon build --symlink-install --packages-select my_robot_ai_navigation` + `source install/setup.bash`).

### 3.2 Ejecución

Robot en `initial_pose`, quieto. **4 terminales** (en el 2, con el venv activado):

**Terminal 1: Nav2**

```bash
ros2 topic pub --once /reset_odom std_msgs/msg/Bool "{data: true}"
ros2 launch my_robot_navigation2 navigation2_robot.launch.py use_sim_time:=false map_file:=my_demo_map.yaml params_file:=rubot_real_lidar_nav.yaml
```

**Terminal 2: clasificador YOLO**

```bash
source /opt/ros/humble/setup.bash
source .venv-yolo/bin/activate
ros2 launch my_robot_ai_perception traffic_sign_classifier.launch.py config_file:=traffic_sign_classifier_real.yaml
```

**Terminal 3: comprobar lo que ve** (enseña cada señal a la cámara antes de mover el robot)

```bash
ros2 topic echo /traffic_sign
```

**Terminal 4: navegación por señales**

```bash
ros2 launch my_robot_ai_navigation traffic_sign_navigation.launch.py config_file:=traffic_sign_navigation_real.yaml
```

El robot va a la inspección. Cuando salga `Waiting for a traffic sign on /traffic_sign ...`, **muestra la señal**:

| Señal | Resultado |
|---|---|
| Stop | espera 3 s y continúa |
| No left turn | ruta derecha (`right`) |
| No right turn | ruta izquierda (`left`) |
| Otra / ninguna | se queda quieto |

Si falla la cámara: `ros2 topic list | grep image_raw`. Si no hay clase estable, sube `stable_frames` o mejora la luz.

Prueba de seguridad sin YOLO (opcional): `ros2 topic pub --once /traffic_sign std_msgs/msg/String "{data: left}"`.

Parar todo: `Ctrl+C` en cada terminal.
