import logging

import zmq
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QImage, QPainter, QPixmap
from PyQt5.QtWidgets import QMainWindow, QDialog
from cv2 import cv2

from app.client.HelloClient import HelloClient
from app.Networking.CommandPacket import CommandPacket, TurnLeft, TurnRight, \
    TurretLeft, TurretRight, GoForward, GoBackward, GoLeft, GoRight, TurretReset
from app.Networking.KinectPacket import KinectPacket
from app.Networking.TelemetryPacket import TelemetryPacket
from app.client.gui.main_window import Ui_MainWindow
from app.common.Misc import decompress, compress


class CommandServer(QtCore.QThread):
    def __init__(self, port=5560, parent=None):
        QtCore.QThread.__init__(self, parent)
        self._logger = logging.getLogger(__name__)
        self._running = True

        context = zmq.Context()

        self._publisher = context.socket(zmq.PUB)
        self._publisher.bind('tcp://*:{}'.format(port))

    def on_command_packet(self, packet: CommandPacket):
        # self._logger.debug(packet)
        self._publisher.send(compress(packet))

    def run(self):
        while self._running:
            pass


class TelemetryClient(QtCore.QThread):

    telemetry_packet_signal = pyqtSignal(TelemetryPacket)
    kinect_packet_singal = pyqtSignal(KinectPacket)

    def __init__(self, port=5559, parent=None):
        QtCore.QThread.__init__(self, parent)
        self._logger = logging.getLogger(__name__)
        self._robot_ip_address = ''
        self._port = port

        self._hello_client = None

        self.running = True
        self.ultrasonic_sensor = 0
        self.color_sensor = 0

    def robot_ip_address(self):
        return self._robot_ip_address

    def set_robot_ip_address(self, ip):
        self._robot_ip_address = ip

    def launch_hello_client(self):
        self._hello_client = HelloClient(self._robot_ip_address, 5556)
        self._hello_client.start()

    def on_telemetry_packet(self, packet: TelemetryPacket):
        self.telemetry_packet_signal = packet

    def run(self):
        self.launch_hello_client()

        context = zmq.Context()
        # First, connect our subscriber socket
        zmq_address = "tcp://{}:{}".format(self._robot_ip_address, 5559)
        self._logger.debug("ZMQ connecting to {}".format(zmq_address))
        subscriber = context.socket(zmq.SUB)
        subscriber.connect(zmq_address)
        subscriber.setsockopt(zmq.SUBSCRIBE, b'')

        while self.running:
            try:
                data = decompress(subscriber.recv())
                if type(data) is TelemetryPacket:
                    self.telemetry_packet_signal.emit(data)
                if type(data) is KinectPacket:
                    self.kinect_packet_singal.emit(data)

            except Exception as e:
                self._logger.exception(e)
                break

        self._hello_client.join()
        subscriber.close()
        context.term()


class MainWindowWrapper(QDialog):

    robot_ip_address_signal = pyqtSignal(str)
    command_packet_signal = pyqtSignal(CommandPacket)

    def __init__(self, app, main_window: QMainWindow):
        QDialog.__init__(self)
        self._logger = logging.getLogger(__name__)
        self._main_window = Ui_MainWindow()
        self._main_window.setupUi(main_window)
        self._app = app

        self._telemetry_client = None
        self._command_server = None

        self.setup_buttons()

    def on_connect_button(self):
        ip_address = self._main_window.robot_ip_address.text()
        self._logger.info("Connecting to {}".format(ip_address))
        self._telemetry_client = TelemetryClient()
        self.robot_ip_address_signal.connect(self._telemetry_client.set_robot_ip_address)
        self.robot_ip_address_signal.emit(ip_address)        
        self._telemetry_client.start()
        self._telemetry_client.telemetry_packet_signal.connect(self.update_telemetry)
        self._telemetry_client.kinect_packet_singal.connect(self.update_kinect)

        self._command_server = CommandServer()
        self.command_packet_signal.connect(self._command_server.on_command_packet)
        self._command_server.start()

        self._main_window.connect_to_robot.setEnabled(False)

    def update_kinect(self, data: KinectPacket):
        self._logger.debug("Got kinect packet!")
        video_array = data.get_video_frame()
        # self._logger.debug(type(array))
        video_frame = cv2.cvtColor(video_array, cv2.COLOR_RGB2BGR)
        height, width, colors = video_frame.shape
        # self._logger.debug("{}|{}|{}".format(height, width, colors))
        bytes_per_line = 3 * width
        image = QImage(video_frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self._main_window.kinect_video.setPixmap(QPixmap.fromImage(image))

        depth_array = data.get_depth()
        # self._logger.debug(depth_array.shape)
        # depth_frame = cv2.cvtColor(depth_array, cv2.IMREAD_GRAYSCALE)
        # depth_height, depth_width, depth_colors = depth_frame.shape
        # self._logger.debug("{}|{}|{}".format(depth_height, depth_width, depth_colors))
        depth_height, depth_width = depth_array.shape
        # bytes_per_line = depth_width
        depth_image = QImage(video_frame.data, depth_width, depth_height, depth_width, QImage.Format_Grayscale8)
        self._main_window.label_10.setPixmap(QPixmap.fromImage(depth_image))

    def update_telemetry(self, data: TelemetryPacket):
        # self._logger.debug("Got telemetry packet!")
        self._main_window.color_sensor_lcd.display(data.color_sensor.raw)
        self._main_window.ultrasonic_sensor_lcd.display(data.ultrasound_sensor.raw)
        self._main_window.lcd_temperature.display(data.temperature)
        self._main_window.lcd_voltage.display(data.voltage)

        self._main_window.left_encoder_lcd.display(data.left_motor.angle)
        self._main_window.right_encoder_lcd.display(data.right_motor.angle)

        self._main_window.turrent_encoder_lcd.display(data.turret_motor.angle)

    def setup_buttons(self):
        self._main_window.connect_to_robot.clicked.connect(self.on_connect_button)

        self._main_window.forward.clicked.connect(self.go_forward)
        self._main_window.backward.clicked.connect(self.go_backward)

        self._main_window.left.clicked.connect(self.turn_left)
        self._main_window.right.clicked.connect(self.turn_right)
        self._main_window.left_full.clicked.connect(self.go_left)
        self._main_window.right_full.clicked.connect(self.go_right)

        self._main_window.turrent_left.clicked.connect(self.turret_left)
        self._main_window.turrent_right.clicked.connect(self.turret_right)

        self._main_window.turrent_reset.clicked.connect(self.turret_reset)

    def go_forward(self):
        command = GoForward(self._main_window.motor_speed.value())
        self.command_packet_signal.emit(command)
        # self._logger.debug(command)

    def go_backward(self):
        command = GoBackward(self._main_window.motor_speed.value())
        self.command_packet_signal.emit(command)

    def go_left(self):
        command = GoLeft(self._main_window.motor_speed.value())
        self.command_packet_signal.emit(command)

    def go_right(self):
        command = GoRight(self._main_window.motor_speed.value())
        self.command_packet_signal.emit(command)

    def turn_left(self):
        command = TurnLeft(self._main_window.motor_speed.value())
        self.command_packet_signal.emit(command)

    def turn_right(self):
        command = TurnRight(self._main_window.motor_speed.value())
        self.command_packet_signal.emit(command)

    def turret_left(self):
        command = TurretLeft(self._main_window.turrent_speed.value())
        self.command_packet_signal.emit(command)

    def turret_right(self):
        command = TurretRight(self._main_window.turrent_speed.value())
        self.command_packet_signal.emit(command)

    def turret_reset(self):
        command = TurretReset()
        self.command_packet_signal.emit(command)
