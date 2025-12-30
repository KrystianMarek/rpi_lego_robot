"""
FrameProcessor - Converts raw Kinect data to displayable images.

Separates image processing from GUI code for:
- Testability
- Future point cloud support
- Depth colormap options
"""
import numpy as np
from PyQt5.QtGui import QImage

from app.common.config import Config


class FrameProcessor:
    """
    Converts raw Kinect frames to QImage for display.

    All methods are static for easy use without instantiation.
    """

    @staticmethod
    def video_to_qimage(video_frame: np.ndarray) -> QImage:
        """
        Convert RGB video frame to QImage.

        Args:
            video_frame: numpy array of shape (H, W, 3) in RGB format

        Returns:
            QImage ready for display in QLabel/QPixmap
        """
        height, width, _ = video_frame.shape
        bytes_per_line = 3 * width
        return QImage(
            video_frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888
        )

    @staticmethod
    def depth_to_qimage(
        depth_array: np.ndarray,
        colormap: str = 'grayscale'
    ) -> QImage:
        """
        Convert depth array to displayable QImage.

        Args:
            depth_array: numpy array of shape (H, W) with 11-bit depth values
            colormap: 'grayscale' (default), 'jet', or 'viridis'

        Returns:
            QImage ready for display
        """
        # Normalize depth to 8-bit
        depth_8bit = FrameProcessor.normalize_depth(depth_array)

        if colormap == 'grayscale':
            return FrameProcessor._depth_grayscale(depth_8bit)
        elif colormap == 'jet':
            return FrameProcessor._depth_colormap_jet(depth_8bit)
        elif colormap == 'viridis':
            return FrameProcessor._depth_colormap_viridis(depth_8bit)
        else:
            return FrameProcessor._depth_grayscale(depth_8bit)

    @staticmethod
    def normalize_depth(depth_array: np.ndarray) -> np.ndarray:
        """
        Normalize 11-bit Kinect depth to 8-bit for display.

        Args:
            depth_array: Raw 11-bit depth values (0-2047)

        Returns:
            8-bit normalized depth array
        """
        # Clip to 10 bits and shift to 8 bits
        depth_normalized = np.clip(depth_array, 0, 2 ** Config.DEPTH_DISPLAY_BITS - 1)
        depth_8bit = (depth_normalized >> 2).astype(np.uint8)
        return np.ascontiguousarray(depth_8bit)

    @staticmethod
    def _depth_grayscale(depth_8bit: np.ndarray) -> QImage:
        """Create grayscale QImage from 8-bit depth."""
        height, width = depth_8bit.shape
        return QImage(
            depth_8bit.data,
            width,
            height,
            width,  # bytes per line = width for grayscale
            QImage.Format_Grayscale8
        )

    @staticmethod
    def _depth_colormap_jet(depth_8bit: np.ndarray) -> QImage:
        """
        Apply jet colormap to depth for better visualization.

        Jet: blue (near) -> cyan -> green -> yellow -> red (far)
        """
        height, width = depth_8bit.shape

        # Create RGB image
        rgb = np.zeros((height, width, 3), dtype=np.uint8)

        # Simple jet colormap approximation
        # Normalize to 0-1
        normalized = depth_8bit.astype(np.float32) / 255.0

        # Red channel
        rgb[:, :, 0] = np.clip(1.5 - np.abs(4 * normalized - 3), 0, 1) * 255
        # Green channel
        rgb[:, :, 1] = np.clip(1.5 - np.abs(4 * normalized - 2), 0, 1) * 255
        # Blue channel
        rgb[:, :, 2] = np.clip(1.5 - np.abs(4 * normalized - 1), 0, 1) * 255

        rgb = np.ascontiguousarray(rgb)
        bytes_per_line = 3 * width
        return QImage(rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)

    @staticmethod
    def _depth_colormap_viridis(depth_8bit: np.ndarray) -> QImage:
        """
        Apply viridis colormap to depth.

        Viridis: purple (near) -> blue -> green -> yellow (far)
        Perceptually uniform, good for scientific visualization.
        """
        height, width = depth_8bit.shape

        # Simplified viridis approximation
        rgb = np.zeros((height, width, 3), dtype=np.uint8)
        normalized = depth_8bit.astype(np.float32) / 255.0

        # Approximate viridis colors
        rgb[:, :, 0] = (68 + 187 * normalized).astype(np.uint8)   # R: 68 -> 255
        rgb[:, :, 1] = (1 + 230 * normalized).astype(np.uint8)    # G: 1 -> 231
        rgb[:, :, 2] = (84 - 30 * normalized).astype(np.uint8)    # B: 84 -> 54

        rgb = np.ascontiguousarray(rgb)
        bytes_per_line = 3 * width
        return QImage(rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)

    @staticmethod
    def depth_to_pointcloud(
        depth_array: np.ndarray,
        fx: float = None,
        fy: float = None,
        cx: float = None,
        cy: float = None
    ) -> np.ndarray:
        """
        Convert depth image to XYZ point cloud.

        Uses Kinect intrinsic camera parameters to project 2D depth
        pixels into 3D world coordinates.

        Args:
            depth_array: Raw depth values from Kinect
            fx, fy: Focal lengths (default from Config)
            cx, cy: Principal point (default from Config)

        Returns:
            numpy array of shape (N, 3) containing XYZ points
        """
        # Use config defaults if not specified
        fx = fx or Config.KINECT_FX
        fy = fy or Config.KINECT_FY
        cx = cx or Config.KINECT_CX
        cy = cy or Config.KINECT_CY

        height, width = depth_array.shape

        # Create pixel coordinate grids
        u = np.arange(width)
        v = np.arange(height)
        u, v = np.meshgrid(u, v)

        # Convert raw depth to meters (approximate formula for Kinect v1)
        # Note: Raw depth is disparity, not distance
        z = depth_array.astype(np.float32)

        # Filter invalid depth values
        valid_mask = (z > Config.DEPTH_MIN_VALID) & (z < Config.DEPTH_MAX_VALID)

        # Convert to 3D coordinates
        x = (u - cx) * z / fx
        y = (v - cy) * z / fy

        # Stack into Nx3 array, only valid points
        points = np.stack([x, y, z], axis=-1)
        valid_points = points[valid_mask]

        return valid_points

    @staticmethod
    def depth_to_colored_pointcloud(
        depth_array: np.ndarray,
        video_frame: np.ndarray,
        fx: float = None,
        fy: float = None,
        cx: float = None,
        cy: float = None
    ) -> tuple:
        """
        Convert depth to point cloud with RGB colors from video.

        Note: This assumes depth and RGB are roughly aligned.
        For precise alignment, camera calibration is needed.

        Args:
            depth_array: Raw depth values
            video_frame: RGB video frame (same resolution assumed)
            fx, fy, cx, cy: Camera intrinsics

        Returns:
            Tuple of (points, colors) where:
            - points: (N, 3) XYZ coordinates
            - colors: (N, 3) RGB values (0-255)
        """
        fx = fx or Config.KINECT_FX
        fy = fy or Config.KINECT_FY
        cx = cx or Config.KINECT_CX
        cy = cy or Config.KINECT_CY

        height, width = depth_array.shape

        u = np.arange(width)
        v = np.arange(height)
        u, v = np.meshgrid(u, v)

        z = depth_array.astype(np.float32)
        valid_mask = (z > Config.DEPTH_MIN_VALID) & (z < Config.DEPTH_MAX_VALID)

        x = (u - cx) * z / fx
        y = (v - cy) * z / fy

        points = np.stack([x, y, z], axis=-1)
        valid_points = points[valid_mask]

        # Get colors for valid points
        # Note: video_frame might have different resolution
        if video_frame.shape[:2] == depth_array.shape:
            colors = video_frame[valid_mask]
        else:
            # Simple nearest-neighbor resampling
            scale_y = video_frame.shape[0] / height
            scale_x = video_frame.shape[1] / width
            vy = (v * scale_y).astype(int)
            vx = (u * scale_x).astype(int)
            vy = np.clip(vy, 0, video_frame.shape[0] - 1)
            vx = np.clip(vx, 0, video_frame.shape[1] - 1)
            all_colors = video_frame[vy, vx]
            colors = all_colors[valid_mask]

        return valid_points, colors

