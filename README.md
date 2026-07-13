## Jetson Orin Nano Setup

Install ROS 2 and CAN tools first. Then install project dependencies:

```bash
sudo apt update
sudo apt install -y can-utils python3-aenum python3-can python3-colcon-common-extensions
sudo apt install -y ros-$ROS_DISTRO-geometry-msgs ros-$ROS_DISTRO-std-msgs
```

Build the ROS 2 package:

```bash
cd ~/GolfCart/golfcart-low-level-control/ros2_ws
source /opt/ros/$ROS_DISTRO/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Optional shell setup:

```bash
echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> ~/.bashrc
echo "source ~/GolfCart/golfcart-low-level-control/ros2_ws/install/setup.bash" >> ~/.bashrc
```

## CAN Bring-Up

Connect the InnoMaker USB2CAN adapter and verify that `can0` exists:

```bash
ip link
```

Bring up the CAN interface at 250 kbit/s:

```bash
cd ~/GolfCart/golfcart-low-level-control/ros2_ws
bash src/golfcart_low_level/scripts/setup_can0.sh can0 250000
```

Or manually:

```bash
sudo ip link set can0 down
sudo ip link set can0 up type can bitrate 250000 restart-ms 100
ip -details -statistics link show can0
```

## Run ROS 2 Low-Level Control 
Terminal 1 รัน low-level stack:
```
  cd ~/GolfCart/golfcart-low-level-control/ros2_ws
  source install/setup.bash
  ros2 launch golfcart_low_level low_level.launch.py
```

Terminal 2 เลือก command source แค่ตัวเดียว

  Fake:
```
  source install/setup.bash
  ros2 run golfcart_low_level fake_cmd_vel
```

  Joystick: 
  	กดปุ่ม ZR สำหรับเริ่มใช้ joy 
  	อนาล็อกซ้ายใช้ควบคุมความเร็ว (max 3.0 m/s)
  	อนาล็อกขวาใช้ควบคุมพวงมาลัย (max 0.7 rad)
  	กดค้างปุ่ม B เพื่อสั่ง emergency stop 
```
  source install/setup.bash
  ros2 launch golfcart_low_level joy_cmd_vel.launch.py
```

# Useful status topics:

```bash
ros2 topic echo /lowlevel_fault
ros2 topic echo /e_stop_status
ros2 topic echo /speed_status
ros2 topic echo /speed_target
ros2 topic echo /speed_diagnostics
ros2 topic echo /brake_status
ros2 topic echo /brake_angle
ros2 topic echo /steering_angle
ros2 topic echo /steering_fault
ros2 topic echo /cmd_vel
```



## --------------------เงื่อนไขการทำงานของระบบ------------------------


# กรณี 1: ยังไม่มี /cmd_vel เข้ามาเลย

  ระบบจะรอคำสั่งจาก navigation:

  speed enable = 0
  speed command = 0
  brake = 0
  /lowlevel_fault = false
  /lowlevel_fault_reason = waiting_for_cmd
  เบรกไม่ทำงาน

# กรณี 2: เคยมี /cmd_vel แล้ว แต่ /cmd_vel หายหรือ timeout

  ระบบจะกลับไปรอคำสั่งเหมือนกรณีแรก:

  speed enable = 0
  speed command = 0
  brake = 0
  /lowlevel_fault = false
  /lowlevel_fault_reason = cmd_vel_timeout_waiting
  เบรกไม่ทำงาน

# กรณี 3: /cmd_vel.linear.x > 0

  ระบบมองว่าเป็นคำสั่งให้รถวิ่ง:
  brake = 0
  speed enable = 1
  speed command = linear.x

  และคำนวณพวงมาลัยจาก:
  steering = atan(wheelbase * angular.z / linear.x)

  จากนั้น publish:

  /steering_cmd

  ให้ steering_node สั่ง KEYA steering motor

# กรณี 4: /cmd_vel.linear.x = 0

  ระบบมองว่าเป็นคำสั่งให้หยุด แต่จะดูความเร็วจริงจาก STM32 speed status ก่อน:

  speed enable = 0
  speed command = 0

  ถ้า:

  abs(/speed_status) > 0.03 m/s

  ระบบจะสั่ง:

  brake = 1

  ถ้า:

  abs(/speed_status) <= 0.03 m/s

  ระบบจะสั่ง:

  brake = 0

  ค่า 0.03 มาจาก config:

  zero_cmd_brake_release_speed_mps: 0.03

# กรณี 5: กด emergency stop

  e-stop override ทุกอย่าง:

  speed enable = 0
  speed command = 0
  brake = 1
  /lowlevel_fault = true
  /lowlevel_fault_reason = e_stop_active

  steering_node จะเข้า safe state และไม่ทำงานตามคำสั่งปกติ

# กรณี 6: speed board fault

  ถ้า STM32 speed board รายงาน fault:

  /lowlevel_fault_reason = speed_fault
  /lowlevel_fault = true

  ระบบจะสั่ง:

  speed enable = 0
  speed command = 0
  brake = 1

# กรณี 7: brake board 0x131 timeout

  ถ้า ros_can_bridge ไม่เห็น CAN status จาก brake board:

  CAN ID 0x131

  เกิน board_timeout_s = 0.5 วินาที จะได้:

  /lowlevel_fault_reason = brake_board_0x131_timeout
  /lowlevel_fault = true

  ระบบจะสั่ง:

  speed enable = 0
  speed command = 0
  brake = 1

# กรณี 8: manual brake override

  สั่งเบรกด้วย topic:

  ros2 topic pub --once /brake_cmd std_msgs/msg/Bool "{data: true}"

  ผลคือ:

  speed enable = 0
  speed command = 0
  brake = 1

  ปล่อย override:

  ros2 topic pub --once /brake_cmd std_msgs/msg/Bool "{data: false}"

  จากนั้นระบบกลับไปทำงานตาม /cmd_vel และ safety logic ปกติ

# กรณี 9: shutdown / Ctrl-C

  เมื่อกด Ctrl-C ปิด ros2 launch ตอนนี้ ros_can_bridge.destroy_node() ยังสั่ง fail-safe:

  speed enable = 0
  speed command = 0
  brake = 1

  ดังนั้นตอน cancel ระบบ เบรกจะทำงาน

  Steering Behavior

  steering_node ใน full system รับ:

  /steering_cmd std_msgs/msg/Float64


  ไม่ได้รับ /cmd_vel โดยตรง

  ถ้า /lowlevel_fault=true หรือ /e_stop_status=true:

  steering_node เข้า safe state

  ถ้า safety clear และ /steering_cmd สดใหม่:

  ส่ง CAN extended ID 0x06000001 ไป KEYA steering motor






