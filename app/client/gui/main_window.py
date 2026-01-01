# -*- coding: utf-8 -*-
"""
Main Window UI for K.O.C Robot GUI Client.

This module was originally auto-generated from main_window.ui but has been
manually refactored for:
- Responsive layout (scales with window size)
- QTabWidget for video streams and point cloud
- Consolidated telemetry section
- Cleaner, maintainable code structure

The .ui file is now deprecated - all changes should be made here directly.
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QSizePolicy


class Ui_MainWindow(object):
    """Main window UI setup class."""

    def setupUi(self, MainWindow):
        """Set up the main window UI with responsive layout."""
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1400, 900)
        MainWindow.setMinimumSize(QtCore.QSize(1000, 700))
        MainWindow.setAutoFillBackground(True)
        MainWindow.setStyleSheet("""
            QLCDNumber {
                color: red;
                background-color: rgb(204, 219, 162);
            }
            QLCDNumber[readoutType="system"] {
                color: #333;
                background-color: rgb(180, 200, 220);
            }
        """)

        # Central widget with main vertical layout
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.main_layout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        self.main_layout.setObjectName("main_layout")

        # === VIDEO AREA (QTabWidget) ===
        self._setup_video_tabs()

        # === CONTROLS AREA ===
        self._setup_controls_area()

        # Set central widget
        MainWindow.setCentralWidget(self.centralwidget)

        # Menu bar (minimal)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)

        # Signal connections
        self._setup_connections()

        # Set text/translations
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def _setup_video_tabs(self):
        """Set up the tabbed video area with Streams and Point Cloud tabs."""
        self.video_tab_widget = QtWidgets.QTabWidget(self.centralwidget)
        self.video_tab_widget.setObjectName("video_tab_widget")
        self.video_tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # --- Tab 1: Streams (Video + Depth) ---
        self.streams_tab = QtWidgets.QWidget()
        self.streams_tab.setObjectName("streams_tab")
        streams_layout = QtWidgets.QHBoxLayout(self.streams_tab)
        streams_layout.setContentsMargins(5, 5, 5, 5)
        streams_layout.setSpacing(10)

        # Video stream label
        self.kinect_video = QtWidgets.QLabel(self.streams_tab)
        self.kinect_video.setObjectName("kinect_video")
        self.kinect_video.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.kinect_video.setMinimumSize(QtCore.QSize(320, 240))
        self.kinect_video.setAlignment(QtCore.Qt.AlignCenter)
        self.kinect_video.setScaledContents(True)
        self.kinect_video.setStyleSheet("background-color: #1a1a1a; color: #666;")
        streams_layout.addWidget(self.kinect_video, stretch=1)

        # Depth stream label
        self.kinect_depth = QtWidgets.QLabel(self.streams_tab)
        self.kinect_depth.setObjectName("kinect_depth")
        self.kinect_depth.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.kinect_depth.setMinimumSize(QtCore.QSize(320, 240))
        self.kinect_depth.setAlignment(QtCore.Qt.AlignCenter)
        self.kinect_depth.setScaledContents(True)
        self.kinect_depth.setStyleSheet("background-color: #1a1a1a; color: #666;")
        streams_layout.addWidget(self.kinect_depth, stretch=1)

        self.video_tab_widget.addTab(self.streams_tab, "")

        # --- Tab 2: Point Cloud (placeholder - actual widget added in MainWindowWrapper) ---
        self.pointcloud_tab = QtWidgets.QWidget()
        self.pointcloud_tab.setObjectName("pointcloud_tab")
        self.pointcloud_layout = QtWidgets.QVBoxLayout(self.pointcloud_tab)
        self.pointcloud_layout.setContentsMargins(0, 0, 0, 0)
        self.video_tab_widget.addTab(self.pointcloud_tab, "")

        # Add tab widget to main layout with stretch factor 3 (takes 75% of space)
        self.main_layout.addWidget(self.video_tab_widget, stretch=3)

    def _setup_controls_area(self):
        """Set up the controls area with 4 evenly distributed sections."""
        self.controls_widget = QtWidgets.QWidget(self.centralwidget)
        self.controls_widget.setObjectName("controls_widget")
        self.controls_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.controls_layout = QtWidgets.QHBoxLayout(self.controls_widget)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_layout.setSpacing(10)
        self.controls_layout.setObjectName("controls_layout")

        # --- Section 1: Locomotion ---
        self._setup_locomotion_section()

        # --- Section 2: Turret ---
        self._setup_turret_section()

        # --- Section 3: Connection ---
        self._setup_connection_section()

        # --- Section 4: Telemetry ---
        self._setup_telemetry_section()

        # Add controls to main layout with stretch factor 1 (takes 25% of space)
        self.main_layout.addWidget(self.controls_widget, stretch=1)

    def _setup_locomotion_section(self):
        """Set up the locomotion control section."""
        self.locomotion = QtWidgets.QGroupBox(self.controls_widget)
        self.locomotion.setObjectName("locomotion")
        self.locomotion.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.locomotion.setMinimumWidth(280)

        locomotion_layout = QtWidgets.QVBoxLayout(self.locomotion)
        locomotion_layout.setContentsMargins(10, 25, 10, 10)
        locomotion_layout.setSpacing(8)

        # Encoder displays row
        encoder_layout = QtWidgets.QHBoxLayout()

        # Left encoder
        left_encoder_layout = QtWidgets.QVBoxLayout()
        self.left_encoder_lcd = QtWidgets.QLCDNumber(self.locomotion)
        self.left_encoder_lcd.setObjectName("left_encoder_lcd")
        self.left_encoder_lcd.setMinimumHeight(30)
        left_encoder_layout.addWidget(self.left_encoder_lcd)
        self.label_left_encoder = QtWidgets.QLabel(self.locomotion)
        self.label_left_encoder.setObjectName("label_left_encoder")
        left_encoder_layout.addWidget(self.label_left_encoder)
        encoder_layout.addLayout(left_encoder_layout)

        encoder_layout.addSpacing(20)

        # Right encoder
        right_encoder_layout = QtWidgets.QVBoxLayout()
        self.right_encoder_lcd = QtWidgets.QLCDNumber(self.locomotion)
        self.right_encoder_lcd.setObjectName("right_encoder_lcd")
        self.right_encoder_lcd.setMinimumHeight(30)
        right_encoder_layout.addWidget(self.right_encoder_lcd)
        self.label_right_encoder = QtWidgets.QLabel(self.locomotion)
        self.label_right_encoder.setObjectName("label_right_encoder")
        right_encoder_layout.addWidget(self.label_right_encoder)
        encoder_layout.addLayout(right_encoder_layout)

        locomotion_layout.addLayout(encoder_layout)

        # Separator line
        line = QtWidgets.QFrame(self.locomotion)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        locomotion_layout.addWidget(line)

        # Movement controls row
        movement_layout = QtWidgets.QHBoxLayout()

        # Direction buttons grid
        self._setup_direction_buttons(movement_layout)

        movement_layout.addSpacing(10)

        # Motor speed control
        speed_layout = QtWidgets.QVBoxLayout()
        self.motor_speed_lcd = QtWidgets.QLCDNumber(self.locomotion)
        self.motor_speed_lcd.setObjectName("motor_speed_lcd")
        self.motor_speed_lcd.setStyleSheet("background-color: rgb(114, 159, 207);")
        self.motor_speed_lcd.setProperty("intValue", 100)
        self.motor_speed_lcd.setMinimumHeight(30)
        speed_layout.addWidget(self.motor_speed_lcd)

        self.motor_speed = QtWidgets.QDial(self.locomotion)
        self.motor_speed.setObjectName("motor_speed")
        self.motor_speed.setMaximum(255)
        self.motor_speed.setProperty("value", 100)
        self.motor_speed.setMinimumSize(60, 60)
        self.motor_speed.setMaximumSize(80, 80)
        speed_layout.addWidget(self.motor_speed)

        movement_layout.addLayout(speed_layout)
        locomotion_layout.addLayout(movement_layout)

        locomotion_layout.addStretch()
        self.controls_layout.addWidget(self.locomotion, stretch=1)

    def _setup_direction_buttons(self, parent_layout):
        """Set up the direction control buttons in a grid."""
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(2)

        # Load icons
        icon_left = QtGui.QIcon()
        icon_left.addPixmap(QtGui.QPixmap("app/client/gui/images/left.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon_up = QtGui.QIcon()
        icon_up.addPixmap(QtGui.QPixmap("app/client/gui/images/up.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon_down = QtGui.QIcon()
        icon_down.addPixmap(QtGui.QPixmap("app/client/gui/images/down.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon_right = QtGui.QIcon()
        icon_right.addPixmap(QtGui.QPixmap("app/client/gui/images/right.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon_round_left = QtGui.QIcon()
        icon_round_left.addPixmap(QtGui.QPixmap("app/client/gui/images/round_left.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon_round_right = QtGui.QIcon()
        icon_round_right.addPixmap(QtGui.QPixmap("app/client/gui/images/round_right.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        btn_size = QtCore.QSize(50, 50)
        icon_size = QtCore.QSize(45, 45)

        # Row 0: left_full, forward, right_full
        self.left_full = QtWidgets.QPushButton(self.locomotion)
        self.left_full.setObjectName("left_full")
        self.left_full.setMinimumSize(btn_size)
        self.left_full.setIcon(icon_left)
        self.left_full.setIconSize(icon_size)
        grid.addWidget(self.left_full, 0, 0)

        self.forward = QtWidgets.QPushButton(self.locomotion)
        self.forward.setObjectName("forward")
        self.forward.setMinimumSize(btn_size)
        self.forward.setIcon(icon_up)
        self.forward.setIconSize(icon_size)
        grid.addWidget(self.forward, 0, 1)

        self.right_full = QtWidgets.QPushButton(self.locomotion)
        self.right_full.setObjectName("right_full")
        self.right_full.setMinimumSize(btn_size)
        self.right_full.setIcon(icon_right)
        self.right_full.setIconSize(icon_size)
        grid.addWidget(self.right_full, 0, 2)

        # Row 1: left (turn), backward, right (turn)
        self.left = QtWidgets.QPushButton(self.locomotion)
        self.left.setObjectName("left")
        self.left.setMinimumSize(btn_size)
        self.left.setIcon(icon_round_left)
        self.left.setIconSize(icon_size)
        grid.addWidget(self.left, 1, 0)

        self.backward = QtWidgets.QPushButton(self.locomotion)
        self.backward.setObjectName("backward")
        self.backward.setMinimumSize(btn_size)
        self.backward.setIcon(icon_down)
        self.backward.setIconSize(icon_size)
        grid.addWidget(self.backward, 1, 1)

        self.right = QtWidgets.QPushButton(self.locomotion)
        self.right.setObjectName("right")
        self.right.setMinimumSize(btn_size)
        self.right.setIcon(icon_round_right)
        self.right.setIconSize(icon_size)
        grid.addWidget(self.right, 1, 2)

        parent_layout.addLayout(grid)

    def _setup_turret_section(self):
        """Set up the turret control section."""
        self.turret_controls = QtWidgets.QGroupBox(self.controls_widget)
        self.turret_controls.setObjectName("turret_controls")
        self.turret_controls.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.turret_controls.setMinimumWidth(260)

        turret_layout = QtWidgets.QVBoxLayout(self.turret_controls)
        turret_layout.setContentsMargins(10, 25, 10, 10)
        turret_layout.setSpacing(8)

        # Encoder and color sensor row
        sensor_layout = QtWidgets.QHBoxLayout()

        # Turret encoder
        turret_enc_layout = QtWidgets.QVBoxLayout()
        self.turret_encoder_lcd = QtWidgets.QLCDNumber(self.turret_controls)
        self.turret_encoder_lcd.setObjectName("turret_encoder_lcd")
        self.turret_encoder_lcd.setMinimumHeight(30)
        turret_enc_layout.addWidget(self.turret_encoder_lcd)
        self.label_turret_encoder = QtWidgets.QLabel(self.turret_controls)
        self.label_turret_encoder.setObjectName("label_turret_encoder")
        turret_enc_layout.addWidget(self.label_turret_encoder)
        sensor_layout.addLayout(turret_enc_layout)

        sensor_layout.addSpacing(20)

        # Color sensor
        color_layout = QtWidgets.QVBoxLayout()
        self.color_sensor_lcd = QtWidgets.QLCDNumber(self.turret_controls)
        self.color_sensor_lcd.setObjectName("color_sensor_lcd")
        self.color_sensor_lcd.setMinimumHeight(30)
        color_layout.addWidget(self.color_sensor_lcd)
        self.label_color_sensor = QtWidgets.QLabel(self.turret_controls)
        self.label_color_sensor.setObjectName("label_color_sensor")
        color_layout.addWidget(self.label_color_sensor)
        sensor_layout.addLayout(color_layout)

        turret_layout.addLayout(sensor_layout)

        # Separator
        line = QtWidgets.QFrame(self.turret_controls)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        turret_layout.addWidget(line)

        # Turret controls row
        controls_row = QtWidgets.QHBoxLayout()

        # Turret direction buttons
        icon_round_left = QtGui.QIcon()
        icon_round_left.addPixmap(QtGui.QPixmap("app/client/gui/images/round_left.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon_round_right = QtGui.QIcon()
        icon_round_right.addPixmap(QtGui.QPixmap("app/client/gui/images/round_right.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        btn_size = QtCore.QSize(50, 50)
        icon_size = QtCore.QSize(45, 45)

        self.turret_left = QtWidgets.QPushButton(self.turret_controls)
        self.turret_left.setObjectName("turret_left")
        self.turret_left.setMinimumSize(btn_size)
        self.turret_left.setIcon(icon_round_left)
        self.turret_left.setIconSize(icon_size)
        controls_row.addWidget(self.turret_left)

        self.turret_right = QtWidgets.QPushButton(self.turret_controls)
        self.turret_right.setObjectName("turret_right")
        self.turret_right.setMinimumSize(btn_size)
        self.turret_right.setIcon(icon_round_right)
        self.turret_right.setIconSize(icon_size)
        controls_row.addWidget(self.turret_right)

        controls_row.addSpacing(10)

        # Turret speed
        speed_layout = QtWidgets.QVBoxLayout()
        self.turret_speed_lcd = QtWidgets.QLCDNumber(self.turret_controls)
        self.turret_speed_lcd.setObjectName("turret_speed_lcd")
        self.turret_speed_lcd.setStyleSheet("background-color: rgb(114, 159, 207);")
        self.turret_speed_lcd.setProperty("intValue", 100)
        self.turret_speed_lcd.setMinimumHeight(30)
        speed_layout.addWidget(self.turret_speed_lcd)

        self.turret_speed = QtWidgets.QDial(self.turret_controls)
        self.turret_speed.setObjectName("turret_speed")
        self.turret_speed.setMaximum(250)
        self.turret_speed.setProperty("value", 99)
        self.turret_speed.setMinimumSize(60, 60)
        self.turret_speed.setMaximumSize(80, 80)
        speed_layout.addWidget(self.turret_speed)

        controls_row.addLayout(speed_layout)
        turret_layout.addLayout(controls_row)

        # Separator
        line2 = QtWidgets.QFrame(self.turret_controls)
        line2.setFrameShape(QtWidgets.QFrame.HLine)
        line2.setFrameShadow(QtWidgets.QFrame.Sunken)
        turret_layout.addWidget(line2)

        # Turret angle row
        angle_layout = QtWidgets.QHBoxLayout()

        angle_display = QtWidgets.QVBoxLayout()
        self.turret_angle_lcd = QtWidgets.QLCDNumber(self.turret_controls)
        self.turret_angle_lcd.setObjectName("turret_angle_lcd")
        self.turret_angle_lcd.setStyleSheet("background-color: rgb(114, 159, 207);")
        self.turret_angle_lcd.setMinimumHeight(30)
        angle_display.addWidget(self.turret_angle_lcd)
        self.label_turret_angle = QtWidgets.QLabel(self.turret_controls)
        self.label_turret_angle.setObjectName("label_turret_angle")
        angle_display.addWidget(self.label_turret_angle)
        angle_layout.addLayout(angle_display)

        self.turret_angle = QtWidgets.QDial(self.turret_controls)
        self.turret_angle.setObjectName("turret_angle")
        self.turret_angle.setMaximum(360)
        self.turret_angle.setSliderPosition(180)
        self.turret_angle.setMinimumSize(60, 60)
        self.turret_angle.setMaximumSize(80, 80)
        angle_layout.addWidget(self.turret_angle)

        turret_layout.addLayout(angle_layout)

        # Reset button
        self.turret_reset = QtWidgets.QPushButton(self.turret_controls)
        self.turret_reset.setObjectName("turret_reset")
        turret_layout.addWidget(self.turret_reset)

        turret_layout.addStretch()
        self.controls_layout.addWidget(self.turret_controls, stretch=1)

    def _setup_connection_section(self):
        """Set up the connection control section."""
        self.connection_group = QtWidgets.QGroupBox(self.controls_widget)
        self.connection_group.setObjectName("connection_group")
        self.connection_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.connection_group.setMinimumWidth(180)

        conn_layout = QtWidgets.QVBoxLayout(self.connection_group)
        conn_layout.setContentsMargins(10, 25, 10, 10)
        conn_layout.setSpacing(10)

        # Robot IP label
        self.label_robot_ip = QtWidgets.QLabel(self.connection_group)
        self.label_robot_ip.setObjectName("label_robot_ip")
        conn_layout.addWidget(self.label_robot_ip)

        # IP address input
        self.robot_ip_address = QtWidgets.QLineEdit(self.connection_group)
        self.robot_ip_address.setObjectName("robot_ip_address")
        self.robot_ip_address.setMinimumHeight(28)
        conn_layout.addWidget(self.robot_ip_address)

        # Connect button
        self.connect_to_robot = QtWidgets.QPushButton(self.connection_group)
        self.connect_to_robot.setObjectName("connect_to_robot")
        self.connect_to_robot.setMinimumHeight(32)
        conn_layout.addWidget(self.connect_to_robot)

        # Connection progress bar
        self.progressBar = QtWidgets.QProgressBar(self.connection_group)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setProperty("value", 0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setMaximumHeight(10)
        conn_layout.addWidget(self.progressBar)

        conn_layout.addStretch()
        self.controls_layout.addWidget(self.connection_group, stretch=1)

    def _setup_telemetry_section(self):
        """Set up the telemetry section with all sensor and system data."""
        self.telemetry_group = QtWidgets.QGroupBox(self.controls_widget)
        self.telemetry_group.setObjectName("telemetry_group")
        self.telemetry_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.telemetry_group.setMinimumWidth(280)

        telemetry_layout = QtWidgets.QVBoxLayout(self.telemetry_group)
        telemetry_layout.setContentsMargins(10, 25, 10, 10)
        telemetry_layout.setSpacing(6)

        # Grid layout for telemetry data (2 columns)
        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(4)

        row = 0

        # --- System Stats ---
        # CPU
        self.lcd_cpu = QtWidgets.QLCDNumber(self.telemetry_group)
        self.lcd_cpu.setObjectName("lcd_cpu")
        self.lcd_cpu.setProperty("readoutType", "system")
        self.lcd_cpu.setMinimumHeight(25)
        self.lcd_cpu.setDigitCount(4)
        grid.addWidget(self.lcd_cpu, row, 0)
        self.label_cpu = QtWidgets.QLabel(self.telemetry_group)
        self.label_cpu.setObjectName("label_cpu")
        grid.addWidget(self.label_cpu, row, 1)

        # RAM
        self.lcd_ram = QtWidgets.QLCDNumber(self.telemetry_group)
        self.lcd_ram.setObjectName("lcd_ram")
        self.lcd_ram.setProperty("readoutType", "system")
        self.lcd_ram.setMinimumHeight(25)
        self.lcd_ram.setDigitCount(4)
        grid.addWidget(self.lcd_ram, row, 2)
        self.label_ram = QtWidgets.QLabel(self.telemetry_group)
        self.label_ram.setObjectName("label_ram")
        grid.addWidget(self.label_ram, row, 3)

        row += 1

        # WiFi
        self.lcd_wifi = QtWidgets.QLCDNumber(self.telemetry_group)
        self.lcd_wifi.setObjectName("lcd_wifi")
        self.lcd_wifi.setProperty("readoutType", "system")
        self.lcd_wifi.setMinimumHeight(25)
        self.lcd_wifi.setDigitCount(5)
        grid.addWidget(self.lcd_wifi, row, 0)
        self.label_wifi = QtWidgets.QLabel(self.telemetry_group)
        self.label_wifi.setObjectName("label_wifi")
        grid.addWidget(self.label_wifi, row, 1)

        row += 1

        # --- Frame Rates ---
        # Video FPS
        self.lcd_video_fps = QtWidgets.QLCDNumber(self.telemetry_group)
        self.lcd_video_fps.setObjectName("lcd_video_fps")
        self.lcd_video_fps.setProperty("readoutType", "system")
        self.lcd_video_fps.setMinimumHeight(25)
        self.lcd_video_fps.setDigitCount(4)
        grid.addWidget(self.lcd_video_fps, row, 0)
        self.label_video_fps = QtWidgets.QLabel(self.telemetry_group)
        self.label_video_fps.setObjectName("label_video_fps")
        grid.addWidget(self.label_video_fps, row, 1)

        # Depth FPS
        self.lcd_depth_fps = QtWidgets.QLCDNumber(self.telemetry_group)
        self.lcd_depth_fps.setObjectName("lcd_depth_fps")
        self.lcd_depth_fps.setProperty("readoutType", "system")
        self.lcd_depth_fps.setMinimumHeight(25)
        self.lcd_depth_fps.setDigitCount(4)
        grid.addWidget(self.lcd_depth_fps, row, 2)
        self.label_depth_fps = QtWidgets.QLabel(self.telemetry_group)
        self.label_depth_fps.setObjectName("label_depth_fps")
        grid.addWidget(self.label_depth_fps, row, 3)

        row += 1

        # Separator
        telemetry_layout.addLayout(grid)
        line = QtWidgets.QFrame(self.telemetry_group)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        telemetry_layout.addWidget(line)

        # --- Sensors Grid ---
        sensors_grid = QtWidgets.QGridLayout()
        sensors_grid.setHorizontalSpacing(15)
        sensors_grid.setVerticalSpacing(4)

        row = 0

        # Temperature
        self.lcd_temperature = QtWidgets.QLCDNumber(self.telemetry_group)
        self.lcd_temperature.setObjectName("lcd_temperature")
        self.lcd_temperature.setMinimumHeight(25)
        sensors_grid.addWidget(self.lcd_temperature, row, 0)
        self.label_temperature = QtWidgets.QLabel(self.telemetry_group)
        self.label_temperature.setObjectName("label_temperature")
        sensors_grid.addWidget(self.label_temperature, row, 1)

        # Voltage
        self.lcd_voltage = QtWidgets.QLCDNumber(self.telemetry_group)
        self.lcd_voltage.setObjectName("lcd_voltage")
        self.lcd_voltage.setMinimumHeight(25)
        sensors_grid.addWidget(self.lcd_voltage, row, 2)
        self.label_voltage = QtWidgets.QLabel(self.telemetry_group)
        self.label_voltage.setObjectName("label_voltage")
        sensors_grid.addWidget(self.label_voltage, row, 3)

        row += 1

        # Ultrasound
        self.ultrasonic_sensor_lcd = QtWidgets.QLCDNumber(self.telemetry_group)
        self.ultrasonic_sensor_lcd.setObjectName("ultrasonic_sensor_lcd")
        self.ultrasonic_sensor_lcd.setMinimumHeight(25)
        sensors_grid.addWidget(self.ultrasonic_sensor_lcd, row, 0)
        self.label_ultrasound = QtWidgets.QLabel(self.telemetry_group)
        self.label_ultrasound.setObjectName("label_ultrasound")
        sensors_grid.addWidget(self.label_ultrasound, row, 1)

        telemetry_layout.addLayout(sensors_grid)
        telemetry_layout.addStretch()

        self.controls_layout.addWidget(self.telemetry_group, stretch=1)

    def _setup_connections(self):
        """Set up signal/slot connections."""
        # Motor speed dial -> LCD display
        self.motor_speed.valueChanged['int'].connect(self.motor_speed_lcd.display)
        # Turret speed dial -> LCD display
        self.turret_speed.valueChanged['int'].connect(self.turret_speed_lcd.display)

    def retranslateUi(self, MainWindow):
        """Set up text translations."""
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "K.O.C Robot Control"))

        # Tab names
        self.video_tab_widget.setTabText(0, _translate("MainWindow", "📹 Streams"))
        self.video_tab_widget.setTabText(1, _translate("MainWindow", "🔲 Point Cloud"))

        # Video labels
        self.kinect_video.setText(_translate("MainWindow", "Video Stream"))
        self.kinect_depth.setText(_translate("MainWindow", "Depth Stream"))

        # Locomotion section
        self.locomotion.setTitle(_translate("MainWindow", "Locomotion"))
        self.label_left_encoder.setText(_translate("MainWindow", "Left Encoder"))
        self.label_right_encoder.setText(_translate("MainWindow", "Right Encoder"))

        # Button shortcuts
        self.left_full.setToolTip(_translate("MainWindow", "Strafe Left (Q)"))
        self.left_full.setShortcut(_translate("MainWindow", "Q"))
        self.forward.setToolTip(_translate("MainWindow", "Forward (W)"))
        self.forward.setShortcut(_translate("MainWindow", "W"))
        self.right_full.setToolTip(_translate("MainWindow", "Strafe Right (E)"))
        self.right_full.setShortcut(_translate("MainWindow", "E"))
        self.left.setToolTip(_translate("MainWindow", "Turn Left (A)"))
        self.left.setShortcut(_translate("MainWindow", "A"))
        self.backward.setToolTip(_translate("MainWindow", "Backward (S)"))
        self.backward.setShortcut(_translate("MainWindow", "S"))
        self.right.setToolTip(_translate("MainWindow", "Turn Right (D)"))
        self.right.setShortcut(_translate("MainWindow", "D"))

        # Turret section
        self.turret_controls.setTitle(_translate("MainWindow", "Turret"))
        self.label_turret_encoder.setText(_translate("MainWindow", "Turret Encoder"))
        self.label_color_sensor.setText(_translate("MainWindow", "Color Sensor"))
        self.label_turret_angle.setText(_translate("MainWindow", "Turret Angle"))
        self.turret_left.setToolTip(_translate("MainWindow", "Turret Left ([)"))
        self.turret_left.setShortcut(_translate("MainWindow", "["))
        self.turret_right.setToolTip(_translate("MainWindow", "Turret Right (])"))
        self.turret_right.setShortcut(_translate("MainWindow", "]"))
        self.turret_reset.setText(_translate("MainWindow", "Reset Turret"))

        # Connection section
        self.connection_group.setTitle(_translate("MainWindow", "Connection"))
        self.label_robot_ip.setText(_translate("MainWindow", "Robot's IP"))
        self.robot_ip_address.setText(_translate("MainWindow", "192.168.10.187"))
        self.connect_to_robot.setText(_translate("MainWindow", "Connect"))

        # Telemetry section
        self.telemetry_group.setTitle(_translate("MainWindow", "Telemetry"))
        self.label_cpu.setText(_translate("MainWindow", "CPU %"))
        self.label_ram.setText(_translate("MainWindow", "RAM %"))
        self.label_wifi.setText(_translate("MainWindow", "WiFi Mbps"))
        self.label_video_fps.setText(_translate("MainWindow", "Video FPS"))
        self.label_depth_fps.setText(_translate("MainWindow", "Depth FPS"))
        self.label_temperature.setText(_translate("MainWindow", "Temp °C"))
        self.label_voltage.setText(_translate("MainWindow", "Voltage V"))
        self.label_ultrasound.setText(_translate("MainWindow", "Ultrasound"))
