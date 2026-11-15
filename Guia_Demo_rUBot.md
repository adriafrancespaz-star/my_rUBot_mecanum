# Guía de demo: rUBot real (VS Code + ROS 2 Humble)

> **Cobertura.** Todas las prácticas (01, 02, 03a, 03b1, 03b2, 04, 05a, 05b).
> **Revisión de waypoints:** ver **6.0** (navegación), **8.2** (señales) y **5.5** (brazo).
>
> Los valores de velocidad marcados con ⚠️ son recomendaciones mías para una demo real prudente (no vienen de los documentos). Ajústalos a tu robot.

---

## Si solo te piden UNA práctica: qué secciones necesitas

**Siempre (cualquier práctica):** sección **0** (preparación, `.bashrc`, compilar) + sección **1** (comprobar con `ros2 node list` que el PC ve el robot).

| Si te piden… | Además de 0 y 1, haz/lee |
|---|---|
| **02** Bringup | solo la sección 2 |
| **03a** Control | sección 3 (empieza por "Reglas generales" y el chequeo de QoS) |
| **03b1** Brazo | sección 4 (4.1 driver y puerto antes de mover nada) |
| **03b2** Pick & place | **4.1** (driver del brazo) + sección 5 (necesitas los ángulos de RoboDK preparados) |
| **04** SLAM / Nav2 | **6.0** (waypoints) + 6.A (mapa), 6.B (Nav2) y 6.C (waypoints) |
| **05a** YOLO | **7.1** (entorno Python) + 7.2–7.4 |
| **05b** Señales + Nav2 | **7.1** (entorno YOLO) + **6.0** (waypoints) + sección 8 completa (8.4 ya incluye lanzar Nav2 con `reset_odom`) |

Así, la última práctica (05b) **no** requiere repetir el mapeo de la 04, pero sí: entorno YOLO (7.1), mapa plantilla, revisión de waypoints (6.0), `colcon build` de los paquetes de IA (8.1) y las etapas de 8.4.

---

## 0. Preparación (antes de la demo, en casa/laboratorio)

### 0.1 Checklist

- [ ] Robot cargado y **encendido** (arranca solo bringup + control + Rosbridge).
- [ ] PC Ubuntu 22.04 conectado al wifi **`Robotics_UB`**.
- [ ] Repo actualizado y compilado.
- [ ] Mapa plantilla del profe localizado (se asume `my_lab_map.yaml`, **verifícalo**, ver 0.4).
- [ ] Zona despejada, robot sobre el suelo, cable/batería OK, **alguien con la mano cerca del robot para pararlo**.
- [ ] Brazo: bola ligera a 12–18 cm de la base, alimentación de servos OK.

### 0.2 Abrir el proyecto en VS Code

1. Abre VS Code → `File > Open Folder…` → `~/Desktop/my_rUBot_mecanum` (o la ruta donde clonaste).
2. Abre un terminal: `` Ctrl+Shift+` `` (Terminal > New Terminal).
3. Para abrir **más terminales**: botón **`+`** del panel de terminal, o **dividir** el actual con `Ctrl+Shift+5`.
4. Cada terminal nuevo lee `.bashrc` automáticamente.

### 0.3 Verificar `.bashrc` (una sola vez)

```bash
gedit ~/.bashrc   # o: code ~/.bashrc
```

Debe contener (ajusta usuario, grupo e IP del robot):

```bash
source /opt/ros/humble/setup.bash
source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash
source /home/<tu_usuario>/Desktop/my_rUBot_mecanum/install/setup.bash
cd ~/Desktop/my_rUBot_mecanum
export QT_QPA_PLATFORM=xcb
export ROS_DOMAIN_ID=1                       # nº de tu grupo
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_AUTOMATIC_DISCOVERY_RANGE=OFF
export ROS_STATIC_PEERS=192.168.1.14         # IP del robot (14, 24, 34 o 44)
```

### 0.4 Actualizar y compilar

```bash
cd ~/Desktop/my_rUBot_mecanum
git pull
colcon build
source install/setup.bash
```

Si da warnings de `PREFIX_PATH`:

```bash
unset COLCON_PREFIX_PATH
unset AMENT_PREFIX_PATH
unset CMAKE_PREFIX_PATH
rm -rf build/ install/ log/
source /opt/ros/humble/setup.bash
colcon build
```

Comprueba que existe el mapa plantilla y los archivos de waypoints:

```bash
ls src/Navigation_Projects/my_robot_navigation2/map/
ls src/Navigation_Projects/my_robot_nav_control/config/
```

---

## 1. Práctica 01: Setup del robot real

**Objetivo a demostrar:** el PC se comunica con el robot real por la red.

**Terminales: 1**

```bash
ros2 node list
```

- Debes ver los **5 nodos principales** del robot. Si es así, estás listo.
- Si no aparecen: revisa wifi `Robotics_UB`, `ROS_DOMAIN_ID`, `ROS_STATIC_PEERS` (IP correcta) y abre un terminal nuevo.

Opcional para enseñar que hay datos:

```bash
ros2 topic list
ros2 topic hz /scan
```

Para el apartado de git (si lo piden):

```bash
git add .
git commit -m "Demo"
git push        # pedirá usuario y PAT de GitHub
```

---

## 2. Práctica 02: Bringup del robot real

**Objetivo a demostrar:** el robot real está levantado (bringup ya hecho al encenderlo), se ve en RViz y se mueve con teleop.

**Terminales: 3**

**Terminal 1: modelo y topics en RViz:**

```bash
ros2 launch my_robot_description display.launch.py use_sim_time:=false
```

En RViz añade `RobotModel`, `TF`, `LaserScan` (`/scan`), `Odometry` (`/odom`) y, si quieres, `Image` (en el robot real la cámara sale en `/image_raw`).

**Terminal 2: teleop (⚠️ despacio):**

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p speed:=0.15 -p turn:=0.5
```

**Terminal 3: odometría y grafo:**

```bash
ros2 topic echo /odom
```

(Para el grafo de nodos, en otra pestaña: `rqt_graph`.)

Comprobaciones rápidas:

```bash
ros2 topic hz /scan
ros2 topic list
```

> `use_sim_time:=false` siempre en real. Las partes de Gazebo y el mundo personalizado (`groupN_custom.world`) son de simulación: no se usan en la demo real (solo si te piden enseñar el entregable).

**Brazo montado en el robot (bringup):** al encender ya se hace como servicio. Solo si hubiera que lanzarlo a mano:

```bash
ros2 launch my_robot_bringup my_robot_arm_bringup_hw.launch.py
```

---

## 3. Práctica 03a: Control del rUBot

**Objetivos:** control por Twist, LiDAR con parada ante obstáculo, selfcontrol, wall follower y go-to-pose.

### Reglas generales (robot real)

- **No ejecutes** `my_robot_set_pose_gazebo_exec`: es solo de simulación.
- Para ver qué argumentos admite un launch antes de lanzarlo:

  ```bash
  ros2 launch my_robot_control my_robot_selfcontrol.launch.xml --show-args
  ```

- Parada: `Ctrl+C` en el terminal del nodo. Si el nodo ya está cerrado y el robot sigue moviéndose:

  ```bash
  ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"
  ```

- **Seguridad LiDAR / QoS (importante):** los documentos avisan de que el LiDAR real suele ser `BEST_EFFORT` y de que los nodos `lidar_test` y `selfcontrol` **aún pueden no tener el QoS corregido**. Si un nodo con suscriptor `RELIABLE` no recibe `/scan`, **no verá obstáculos y no frenará**. Antes de la demo:

  ```bash
  ros2 topic info /scan --verbose
  ```

  y haz una prueba con la mano/caja delante del robot a baja velocidad.

### 3.1 Movimiento con Twist

**Terminales: 1**

```bash
ros2 launch my_robot_control my_robot_control.launch.xml vx:=0.0 vy:=0.2 w:=0.0 td:=5.0
```

- `vy:=0.2` durante `td:=5.0` s ≈ 1 m lateral (holonómico). Deja 1.5 m libres.
- ⚠️ Para la demo, p. ej. `vx:=0.1 vy:=0.0 w:=0.0 td:=3.0` (≈30 cm adelante) y luego `vy:=0.1 td:=3.0` (lateral).

### 3.2 Test de LiDAR (parada ante obstáculo)

```bash
ros2 launch my_robot_control my_robot_lidar_test.launch.xml
```

Si en tu versión ya añadiste los argumentos (`vx`, `vy`, `w`, `stop_distance`, `fov_min_deg`, `fov_max_deg`), úsalos con valores bajos:

```bash
ros2 launch my_robot_control my_robot_lidar_test.launch.xml vx:=0.1 vy:=0.0 w:=0.0 stop_distance:=0.4
```

(⚠️ `stop_distance` mayor de lo que usarías en simulación, por margen en real.) Acércale la mano/caja: debe pararse.

### 3.3 Selfcontrol con obstáculos

```bash
ros2 launch my_robot_control my_robot_selfcontrol.launch.xml
```

- Valores por defecto: `forward_speed=0.3 m/s`, `rotation_speed=0.5 rad/s` (rápido para una demo). Mira con `--show-args` si se pueden bajar; si no, edita el valor por defecto en el launch/nodo y recompila (`colcon build --symlink-install --packages-select my_robot_control`). ⚠️ Prueba con ~0.15 m/s.
- Haz la demo en un recinto con paredes/cajas; tú siempre cerca. Parar: `Ctrl+C` (publica velocidad cero).
- Si presentas la versión holonómica del entregable: `my_robot_selfcontrol_holonomic.py` (comprueba cómo se lanza en tu paquete).

### 3.4 Wall follower

Coloca el robot **paralelo a una pared a su derecha**, con la pared dentro de la región `RIGHT` del LiDAR (-110° a -70°). No hay maniobra inicial de acercamiento.

```bash
# Versión diferencial
ros2 launch my_robot_control my_robot_wallfollower_differential.launch.xml

# Versión holonómica
ros2 launch my_robot_control my_robot_wallfollower_holonomic.launch.py
```

- Por defecto `forward_speed=0.3 m/s`, `turn_speed=0.5 rad/s` (holonómico: `max_lateral_speed=0.4`, `max_angular_speed=1.0`). ⚠️ Reduce si se pueden pasar por parámetro.
- Parar con `Ctrl+C` antes de cambiar de controlador.

### 3.5 Go to pose

```bash
ros2 launch my_robot_control my_robot_go2pose.launch.xml x:=1.0 y:=1.0 f:=90.0
```

- `x`, `y` en **metros** en el frame **`odom`** (no `map`); `f` en **grados** (a diferencia de los waypoints de Nav2, que usan radianes).
- El origen `odom` es donde estaba el robot al arrancar/resetear la odometría. Para tener un origen conocido: robot quieto y
  `ros2 topic pub --once /reset_odom std_msgs/msg/Bool "{data: true}"` (comando de la práctica 04).
- ⚠️ Para la demo, un objetivo corto: `x:=0.5 y:=0.5 f:=90.0`. En RViz, Fixed Frame = `odom`.

---

## 4. Práctica 03b1: Control del brazo (hardware real)

> Pipeline: `send_*_node` → `/arm_controller/joint_trajectory` → `serial_trajectory_bridge_node` → Arduino Nano ESP32 → servos SG90.

### 4.1 Antes de nada

```bash
ros2 node list
```

- Si ya aparece `/serial_trajectory_bridge_node` (el bringup del brazo en el arranque lo incluye), **no lances otro driver**.
- Si no aparece, identifica el puerto y lanza el driver:

  ```bash
  ls /dev/ttyUSB* /dev/ttyACM*
  ros2 run my_arm_driver serial_trajectory_bridge_node --ros-args -p serial_port:=/dev/ttyUSB1
  ```

  (`/dev/ttyUSB1` es lo habitual para el brazo mecanum.) Si da *permission denied*: `sudo usermod -a -G dialout $USER` y reinicia sesión.

> Los documentos no dicen en qué máquina corre el driver (PC o Raspberry del robot). Confírmalo con el profe/compañeros antes de la demo.

Verifica topics: `ros2 topic list | grep joint` → `/arm_controller/joint_trajectory` y `/joint_states`.

### 4.2 Movimiento suave (nodo recomendado)

**Regla clave:** `start_joints_deg` **no se lee del robot**: tú indicas la postura de partida. Debe coincidir con la postura real del brazo; si no, el primer punto provoca un salto brusco.

**Terminales: 2** (T1 driver si hace falta, T2 comandos)

Primero, movimientos pequeños (10–20°) y mirando que cada servo gire en el sentido correcto:

```bash
ros2 run my_arm_driver send_smooth_joint_target_node --ros-args \
  -p start_joints_deg:="[0.0,0.0,0.0,0.0,0.0,0.0]" \
  -p target_joints_deg:="[15.0,0.0,0.0,0.0,0.0,0.0]" \
  -p duration:=4.0 \
  -p steps:=40
```

Dos articulaciones y vuelta a casa:

```bash
ros2 run my_arm_driver send_smooth_joint_target_node --ros-args \
  -p start_joints_deg:="[15.0,0.0,0.0,0.0,0.0,0.0]" \
  -p target_joints_deg:="[15.0,25.0,-20.0,0.0,0.0,0.0]" \
  -p duration:=5.0 \
  -p steps:=50

ros2 run my_arm_driver send_smooth_joint_target_node --ros-args \
  -p start_joints_deg:="[15.0,25.0,-20.0,0.0,0.0,0.0]" \
  -p target_joints_deg:="[0.0,0.0,0.0,0.0,0.0,0.0]" \
  -p duration:=5.0 \
  -p steps:=50
```

Comparación lento/suave (para enseñar `duration` y `steps`): `duration:=10.0 steps:=100`.

### 4.3 Otras formas de comandar (si las piden)

- Un solo objetivo (brusco si el salto es grande):

  ```bash
  ros2 run my_arm_driver send_joint_target_node --ros-args \
    -p joint_names:="[arm_joint1,arm_joint2,arm_joint3,arm_joint4,arm_joint5,arm_joint6]" \
    -p target_joints_deg:="[0.0,30.0,-30.0,0.0,0.0,0.0]" \
    -p duration:=2.0
  ```

- Con `ros2 topic pub` (**radianes**, 0.5 rad ≈ 28.6°):

  ```bash
  ros2 topic pub /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
  joint_names:
  - arm_joint1
  - arm_joint2
  - arm_joint3
  - arm_joint4
  - arm_joint5
  - arm_joint6
  points:
  - positions: [0.0, 0.5, -0.5, 0.0, 0.0, 0.0]
    time_from_start:
      sec: 2
      nanosec: 0
  " --once
  ```

  ⚠️ No copies los ejemplos del documento 02 (p. ej. `[0.0, -1.0, 2.0, …]` rad ≈ −57°/115°): son de simulación y grandes para el hardware.

### 4.4 Visualizar en RViz y monitorizar

```bash
ros2 topic echo /joint_states --once
ros2 topic hz /joint_states      # ~20 Hz
rviz2
```

### 4.5 Si algo falla

| Síntoma | Solución |
|---|---|
| Servo gira al revés | Relanza el driver con `-p servo_sign:="[1,-1,1,1,1,1]"` (ajusta la posición) |
| Servo topa mecánicamente | `-p servo_min_deg:="[20,20,20,20,20,20]" -p servo_max_deg:="[160,160,160,160,160,160]"` |
| No se mueve | `ros2 topic echo /arm_controller/joint_trajectory` y `ros2 node list` |
| No se ve en RViz | Los nombres de joints deben ser `arm_joint1…6` |
| Puerto no detectado | `ls /dev/ttyUSB*`, `dmesg | tail`, reconectar USB |

---

## 5. Práctica 03b2: Pick and Place con cinemática inversa

**Objetivo a demostrar:** definir targets cartesianos en RoboDK → IK → ángulos → ejecutar con ROS 2 → coger y soltar una bola.

### 5.1 Antes de la demo (preparar los datos)

1. En **RoboDK** crea los targets: `Home`, `PrePick`, `Pick`, `PrePlace`, `Place` (PrePick/PrePlace ≈ **5 cm por encima** de la bola).
2. Apunta los ángulos J1–J6 de cada target:

| Target | J1 | J2 | J3 | J4 | J5 | J6 |
|---|---:|---:|---:|---:|---:|---:|
| Home | | | | | | |
| PrePick | | | | | | |
| Pick | | | | | | |
| PrePlace | | | | | | |
| Place | | | | | | |

3. Haz una **captura de la estación RoboDK** con todos los targets (entregable).

### 5.2 Ejecución

**Terminales: 2.** T1 = driver (solo si no está ya en `ros2 node list`, ver 4.1). T2 = movimientos.

Cada movimiento usa `send_smooth_joint_target_node`; **`start_joints_deg` = el objetivo del movimiento anterior** (el nodo no lee la postura real). Valores típicos: `duration:=5.0`, `steps:=50` (≈51 puntos).

Rellena `HOME`, `PREPICK`, `PICK`, `PREPLACE`, `PLACE` con los ángulos de RoboDK. Guárdalo como `pick_place_demo.sh` y ejecútalo con `bash pick_place_demo.sh`:

```bash
#!/usr/bin/env bash
# Ángulos en grados [J1,J2,J3,J4,J5,J6] obtenidos de RoboDK
HOME_J="[0.0,0.0,0.0,0.0,0.0,0.0]"
PREPICK="[...]"
PICK="[...]"
PICK_CLOSED="[...]"   # mismo que PICK pero con la pinza cerrada
PREPLACE="[...]"
PLACE="[...]"
PLACE_OPEN="[...]"    # mismo que PLACE pero con la pinza abierta
DUR=5.0
STEPS=50

move() {   # $1 = postura de partida, $2 = objetivo
  timeout 5 ros2 run my_arm_driver send_smooth_joint_target_node --ros-args \
    -p start_joints_deg:="$1" \
    -p target_joints_deg:="$2" \
    -p duration:=$DUR \
    -p steps:=$STEPS
  sleep "$(awk "BEGIN{print $DUR+1.5}")"   # esperar a que termine el movimiento
}

move "$HOME_J"      "$PREPICK"
move "$PREPICK"     "$PICK"
move "$PICK"        "$PICK_CLOSED"
move "$PICK_CLOSED" "$PREPICK"
move "$PREPICK"     "$PREPLACE"
move "$PREPLACE"    "$PLACE"
move "$PLACE"       "$PLACE_OPEN"
move "$PLACE_OPEN"  "$HOME_J"
```

> ⚠️ Los documentos no indican **qué servo es la pinza**, así que `PICK_CLOSED`/`PLACE_OPEN` quedan como postura con ese servo cambiado. Confírmalo. Prueba el script antes con movimientos pequeños (10–20°) y la bola lejos.
> Si el nodo no termina solo, el `timeout 5` lo cierra tras publicar; si prefieres, ejecútalo a mano comando a comando.

### 5.3 Secuencia

```
Home → PrePick → Pick → Cerrar pinza → PrePick (subir) → PrePlace → Place → Abrir pinza → Home
```

⚠️ Para una demo segura no bajes de `duration = 5 s` y `steps = 50`. Para el Task 4 (optimización) repite un tramo con otros valores (p. ej. `duration:=2.0 steps:=10` brusco vs `duration:=10.0 steps:=100` lento).

**Parar:** `Ctrl+C` en el terminal activo y, si hace falta, desconectar el USB del Arduino.

**Errores típicos:** orden de articulaciones, sentido del servo (`servo_sign`), bola fuera de alcance, `duration` muy pequeño, `start_joints_deg` distinto de la postura real.

### 5.4 Preguntas del laboratorio (Q1–Q5): respuestas cortas

1. **FK vs IK:** FK calcula la pose del efector a partir de los ángulos; IK calcula los ángulos necesarios para una pose dada.
2. **Por qué IK:** la tarea se define en espacio cartesiano (posición de la bola) y el robot necesita ángulos de articulación.
3. **PrePick/PrePlace:** aproximación vertical segura (~5 cm), evita colisiones con la mesa/bola y da movimientos más suaves.
4. **Trayectorias suaves con SG90:** solo aceptan ángulo objetivo (sin control de velocidad); dividir el movimiento en pasos evita saltos bruscos y esfuerzos.
5. **Parámetros:** `duration` (velocidad) y `steps` (suavidad).

### 5.5 Waypoints de brazo: `send_joint_trajectory_node` (alternativa)

```bash
ros2 run my_arm_driver send_joint_trajectory_node --ros-args \
  -p joint_names:="[arm_joint1,arm_joint2,arm_joint3,arm_joint4,arm_joint5,arm_joint6]" \
  -p trajectory_points_deg:="[
    [0.0,0.0,0.0,0.0,0.0,0.0],
    [0.0,20.0,0.0,0.0,0.0,0.0],
    [0.0,20.0,-20.0,0.0,0.0,0.0],
    [0.0,0.0,0.0,0.0,0.0,0.0]
  ]" \
  -p point_times_sec:="[0.0,2.0,4.0,6.0]"
```

Revisión:
- `joint_names` **hay que sobrescribirlo** (por defecto `joint1…6`; el robot usa `arm_joint1…6`).
- Un waypoint por tiempo: las dos listas deben tener **la misma longitud**; los tiempos son **absolutos** y crecientes desde el inicio.
- El **primer punto (t = 0)** es una orden inmediata: si no coincide con la postura real del brazo, habrá un salto. Pon el brazo en esa postura antes o usa el nodo suave.
- Con pocos puntos el movimiento es menos suave que con `send_smooth_joint_target_node`; ⚠️ en la demo prefiere el suave.

---

## 6. Práctica 04: SLAM y navegación (robot real)

### 6.0 Waypoints: revisión y checklist (leer antes de 6.B, 6.C y del apartado 8)

Se usan en `waypoints_hw.yaml` (04) y `traffic_sign_navigation_real.yaml` (05b). Formato **`[x, y, yaw]` en el frame `map`**: `x`, `y` en metros; `yaw` en **radianes** (0 = eje +X, 1.57 ≈ 90° a la izquierda, 3.14 ≈ 180°, −1.57 ≈ 90° a la derecha).

**Problemas detectados en los documentos**

1. **Valores de ejemplo de simulación.** `[1.0,-1.0]`, `[2.0,0.0]`, `[2.0,1.0]`, `[0.5,±1.0]`… son del mundo `square_sign_left_ign`. En el mapa real pueden caer dentro de una pared o de una zona inflada. No los copies sin comprobarlos.
2. **Nombre de archivo incoherente en 04.** El texto dice `waypoints_sw_ign.yaml` pero el comando usa `waypoints_hw.yaml`. Para el robot real: **`waypoints_hw.yaml`**.
3. **El ejemplo de 05b es el de simulación:** trae `use_sim_time: true`. En `traffic_sign_navigation_real.yaml` debe ser **`false`** (si queda en `true`, la navegación espera `/clock` indefinidamente).
4. **Unidades distintas entre prácticas:** Nav2/waypoints usan **radianes y frame `map`**; `go2pose` usa **grados y frame `odom`**.
5. **Formato:** el nodo actual solo admite la estructura **plana** (`initial_pose`, `waypoints`, `final_pose`), no la de `ros__parameters`. En 05b, en cambio, **sí** se usa `ros__parameters`.
6. **`initial_pose` debe coincidir con la realidad.** Se envía a Nav2 como pose inicial: si el robot no está físicamente ahí, la localización será errónea y navegará mal o chocará.

**Paso 1: conocer el mapa plantilla**

```bash
cat ~/Desktop/my_rUBot_mecanum/src/Navigation_Projects/my_robot_navigation2/map/my_lab_map.yaml
```

Anota `resolution` y `origin`. El (0,0) del mapa es el punto donde el profe puso el robot al mapear: **pregunta/identifica dónde está físicamente en tu laboratorio y márcalo en el suelo**.

**Paso 2: obtener coordenadas válidas**

Con Nav2 en marcha (6.B) y `Fixed Frame = map` en RViz:
1. Herramienta **Publish Point** (barra superior) → clic sobre una zona **blanca/libre** del mapa.
2. En otro terminal:

   ```bash
   ros2 topic echo /clicked_point
   ```

   `x` e `y` son las coordenadas para el YAML. Para el yaw, usa la dirección en que quieres que mire (`atan2(Δy, Δx)`).

**Paso 3: márgenes**

```bash
grep -rn "inflation_radius\|robot_radius\|footprint" ~/Desktop/my_rUBot_mecanum/src/Navigation_Projects/my_robot_navigation2/ --include=rubot_real_lidar_nav.yaml
```

Cada waypoint debe quedar fuera de las celdas inflated (a más distancia de la pared que `inflation_radius`, ⚠️ con margen extra). Evita pasillos estrechos para la demo.

**Paso 4: probar antes**

- Primero con **distancias cortas** (≤ 1–1.5 m) y zonas amplias.
- Comprueba cada punto en RViz con **Nav2 Goal** (¿lo acepta y planifica?) antes de ponerlo en el YAML.
- El camino entre waypoints consecutivos no debe cruzar paredes ni obstáculos.

**Paso 5: recompilar tras editar el YAML**

```bash
cd ~/Desktop/my_rUBot_mecanum
colcon build --symlink-install --packages-select my_robot_nav_control my_robot_ai_navigation
source install/setup.bash
```

(Si no se compiló antes con `--symlink-install`, el robot usaría el YAML antiguo.)


### 6.A Generar un mapa con SLAM

**Terminales: 3**

⚠️ Guarda el mapa con un **nombre nuevo** (`my_demo_map`) para **no sobrescribir** el mapa plantilla.

1. Coloca el robot **físicamente en el punto que será el origen del mapa** y no lo muevas.

**Terminal 1: reset de odometría + Cartographer:**

```bash
ros2 topic pub --once /reset_odom std_msgs/msg/Bool "{data: true}"
ros2 launch my_robot_cartographer cartographer.launch.py use_sim_time:=false
```

Se abre RViz con el mapa creciendo.

**Terminal 2: teleop (despacio):**

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p speed:=0.1 -p turn:=0.4
```

⚠️ Velocidades bajas (~0.1 m/s) y giros suaves dan mejor mapa y menos riesgo. Recorre el entorno y vuelve cerca del inicio.

**Terminal 3: guardar el mapa:**

```bash
cd ~/Desktop/my_rUBot_mecanum/src/Navigation_Projects/my_robot_navigation2/map/
ros2 run nav2_map_server map_saver_cli -f my_demo_map
display my_demo_map.pgm
```

(`display` requiere `sudo apt install imagemagick`, hazlo antes.)

**Para todo:** `k` en el teleop, `Ctrl+C` en Cartographer. Vuelve a la raíz: `cd ~/Desktop/my_rUBot_mecanum`.

### 6.B Navegar con Nav2 sobre el mapa plantilla

**Terminales: 2**

1. Coloca el robot **exactamente en el pose `[0, 0, 0]` con el que se creó el mapa**, quieto.

**Terminal 1: reset de odometría y Nav2 (antes de lanzar Nav2):**

```bash
ros2 topic pub --once /reset_odom std_msgs/msg/Bool "{data: true}"
ros2 launch my_robot_navigation2 navigation2_robot.launch.py use_sim_time:=false map_file:=my_lab_map.yaml params_file:=rubot_real_lidar_nav.yaml
```

> `use_sim_time:=false` es obligatorio en real (por defecto es `true`).

2. En **RViz**, si el robot no está bien localizado: botón **2D Pose Estimate** y marca su pose real.
3. Demo manual: **Nav2 Goal** → clic y arrastre en el mapa (en zona libre). Muestra también:
   - **Waypoint/Nav Through Poses Mode** → varios goals → **Start Waypoint Following** (visita cada uno) o **Start Nav Through Poses** (una trayectoria optimizada).

### 6.C Navegación programática con waypoints (Simple Commander)

Con Nav2 de 6.B aún en marcha y tras revisar **6.0**:

**Terminal 2:**

```bash
code src/Navigation_Projects/my_robot_nav_control/config/waypoints_hw.yaml
```

Edita con **tus** coordenadas del mapa real (plantilla):

```yaml
initial_pose: [X0, Y0, YAW0]      # donde está físicamente el robot AHORA (mapa)
waypoints:
  - [X1, Y1, YAW1]
  - [X2, Y2, YAW2]
final_pose: [XF, YF, YAWF]
```

Recompila (paso 5 de 6.0) y lanza:

```bash
ros2 launch my_robot_nav_control nav_waypoints.launch.py wp_file:=waypoints_hw.yaml
```

- Orden: coloca el robot en `initial_pose` → `reset_odom` (quieto) → Nav2 activo en RViz → lanzar el nodo.
- Con `waypoints: []`, va directo de `initial_pose` a `final_pose`.
- ⚠️ Primero prueba con un solo waypoint cercano; luego con la ruta completa.
- Estructura **plana** (no `ros__parameters`).

**Parar:** `Ctrl+C` en ambos terminales; si el robot se descontrola, para el robot físicamente.

---

## 7. Práctica 05a: Modelos YOLO

**Objetivo a demostrar:** clasificación de señales, detección y pose con YOLO.

### 7.1 Entorno (una vez, en Ubuntu)

```bash
cd ~/Desktop/my_rUBot_mecanum
python3 -m venv --system-site-packages .venv-yolo
source .venv-yolo/bin/activate
python -m pip install --upgrade pip
python -m pip install ultralytics "numpy<2.0"
```

No uses `sudo pip`, no lo crees como root y no reinstales NumPy/OpenCV del sistema (rompe `cv_bridge`).

### 7.2 Clasificación con la cámara del robot (ROS 2)

**Terminales: 2**

**Terminal 1: comprobar la cámara:**

```bash
source /opt/ros/humble/setup.bash
source .venv-yolo/bin/activate
ros2 topic hz /image_raw
```

**Terminal 2 (con el venv activo):**

```bash
source .venv-yolo/bin/activate
python tools/yolo_model_generation/classification/5_infer_ros.py
```

Usa `yolo11n_cls_g1.pt` y `/image_raw` por defecto. Enseña cada señal (Stop, Give Way, No Entry, y las de giro) a la cámara. Salir: `q` en la ventana.

Si tu cámara publica en otro topic:

```bash
python tools/yolo_model_generation/classification/5_infer_ros.py --image-topic /<tu_topic>
```

Alternativa con **webcam del PC** (sin robot):

```bash
python tools/yolo_model_generation/classification/5_infer_webcam.py
```

> Recuerda: señal **No left turn → clase `Right`** (ruta derecha); **No right turn → clase `Left`**.

### 7.3 Detección (si tienes el modelo entrenado)

```bash
python tools/yolo_model_generation/detection/5_infer_webcam.py
# o con cámara ROS 2:
python tools/yolo_model_generation/detection/5_infer_ros.py
```

Necesita `detection/workspace/runs/detect/train/weights/best.pt`. Si no existe, omite este apartado. Salir: `q` (webcam) o `Ctrl+C` (ROS).

### 7.4 Pose estimation

```bash
python tools/yolo_model_generation/pose/pose_gesture_webcam.py
```

---

## 8. Práctica 05b: Navegación con señales de tráfico (YOLO + Nav2)

**Objetivo a demostrar:** el robot va al punto de inspección, lee la señal y elige ruta (`left`/`right`/`stop`).

### 8.1 Compilar (si no lo has hecho)

```bash
cd ~/Desktop/my_rUBot_mecanum
source /opt/ros/humble/setup.bash
source .venv-yolo/bin/activate
colcon build --symlink-install --packages-select my_robot_ai_perception my_robot_ai_navigation
source install/setup.bash
```

### 8.2 Configurar las rutas (waypoints de señales): revisar con 6.0

Abre `src/AI_Projects/my_robot_ai_navigation/config/traffic_sign_navigation_real.yaml` (`code …`) y adapta **todas** las poses a tu mapa plantilla:

```yaml
traffic_sign_navigation:
  ros__parameters:
    use_sim_time: false            # ← OBLIGATORIO en real
    initial_pose: [X0, Y0, YAW0]   # donde colocas el robot (coordenadas del mapa)
    inspection_pose: [XI, YI, YAWI]  # mirando a la señal
    left_waypoint: [XL, YL, YAWL]
    right_waypoint: [XR, YR, YAWR]
    final_pose: [XF, YF, YAWF]
    stop_duration: 3.0
```

(En el documento, el ejemplo con `[-0.5, 0.0]`, `[0.0, 0.0]`, `[0.5, ±1.0]`, `[2.0, 1.0, 1.57]` y `use_sim_time: true` es el de **simulación**; no es válido tal cual.)

Comprobaciones específicas:
- **`inspection_pose` orientada a la señal:** yaw = `atan2(y_señal − y_insp, x_señal − x_insp)`. Con el robot ahí, la señal debe verse completa en `/traffic_sign/image`.
- **`left_waypoint` y `right_waypoint`** en zonas libres, uno por cada ruta física, y `final_pose` alcanzable desde ambos.
- Valores aceptados: `left`, `right`, `stop` (minúsculas); `stop` espera `stop_duration` s y continúa; cualquier otro valor = se queda en la inspección.
- **Clases:** señal *No left turn* → `Right`, *No right turn* → `Left` (indican la ruta a seguir, no la barra roja).
- Muestra la señal **cuando el robot ya esté en la inspección** y aparezca `Waiting for a traffic sign on /traffic_sign ...`.
- Recompila tras editar (paso 5 de 6.0).

### 8.3 Verificar el hardware

**Terminal 1:**

```bash
ros2 topic hz /scan
ros2 topic hz /odom
ros2 topic list | grep image_raw
```

### 8.4 Demo en etapas

**Terminales: 4**

Etapa 1 — **Nav2.** Coloca el robot en la `initial_pose` y, **quieto**:

**Terminal 1:**

```bash
ros2 topic pub --once /reset_odom std_msgs/msg/Bool "{data: true}"
ros2 launch my_robot_navigation2 navigation2_robot.launch.py use_sim_time:=false map_file:=my_lab_map.yaml params_file:=rubot_real_lidar_nav.yaml
```

Comprueba en RViz pose y costmaps (usa **2D Pose Estimate** si hace falta).

Etapa 2 — **Prueba de navegación con mensaje manual** (recomendada antes de la demo; no hace falta YOLO):

**Terminal 2:**

```bash
ros2 launch my_robot_ai_navigation traffic_sign_navigation.launch.py config_file:=traffic_sign_navigation_real.yaml
```

Espera a ver `Waiting for a traffic sign on /traffic_sign ...` (robot en inspection pose). Entonces, **Terminal 3:**

```bash
ros2 topic pub --once /traffic_sign std_msgs/msg/String "{data: left}"
```

Repite (reiniciando `traffic_sign_navigation`: `Ctrl+C` y relanzar) con `right`, `stop` y `unknown`. No pases a la etapa 3 hasta que los 4 casos sean seguros.

Etapa 3 — **Con YOLO real.** Para el terminal 2 (`Ctrl+C`). En el **Terminal 3** (con venv):

```bash
source /opt/ros/humble/setup.bash
source .venv-yolo/bin/activate
ros2 launch my_robot_ai_perception traffic_sign_classifier.launch.py config_file:=traffic_sign_classifier_real.yaml
```

Se abre `rqt_image_view` con `/traffic_sign/image` (imagen anotada). Para ver la cámara cruda añade `view_topic:=/image_raw`. Sin visor: `show_image:=false`.

**Terminal 4: verificar que clasifica antes de mover el robot:**

```bash
ros2 topic echo /traffic_sign
```

Enseña cada señal a la cámara y comprueba la salida.

Etapa 4 — **Demo completa.** Reinicia el robot en la `initial_pose` si se movió y, en el **Terminal 2**:

```bash
ros2 launch my_robot_ai_navigation traffic_sign_navigation.launch.py config_file:=traffic_sign_navigation_real.yaml
```

El robot va a la inspección, lee la señal y toma la ruta.

### 8.5 Si algo falla

| Síntoma | Qué hacer |
|---|---|
| No llega `/traffic_sign` manual | `source install/setup.bash`, revisa nombre y tipo |
| No sale del punto de inspección | Publica solo después del mensaje "Waiting…" |
| Rechaza el goal | Revisa la pose en el costmap global / inflation |
| Ruta equivocada | Valores en minúscula: `left`, `right`, `stop` |
| Sin imágenes | Comprueba el topic real y el dispositivo de cámara |
| YOLO no da clase | Baja temporalmente la confianza e inspecciona la imagen anotada |
| Clase oscila | Sube `stable_frames` |

---

## 9. Orden sugerido para la demo

1. **01** `ros2 node list` (conexión OK)
2. **02 / 03a** bringup, teleop y control (3.1–3.5)
3. **03b1 / 03b2** brazo (4 y 5)
4. **04** mapa con SLAM → **revisar waypoints (6.0)** → Nav2 con mapa plantilla → waypoints programáticos
5. **05a** YOLO (clasificación + pose)
6. **05b** integración completa con señales

## 10. Reglas de seguridad para la demo en real

- Alguien siempre cerca del robot/botón de apagado.
- Reset de odometría **solo con el robot quieto** y **antes** de lanzar Nav2.
- Todas las velocidades de teleop bajas (⚠️ 0.1–0.15 m/s) y goals en zonas amplias y libres.
- Un `Ctrl+C` en cada terminal para cerrar; no relances Nav2 con el robot moviéndose.
- Ten una grabación/vídeo de respaldo por si falla el wifi.
