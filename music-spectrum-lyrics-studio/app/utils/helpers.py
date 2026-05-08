"""
Utility helpers for the application.
"""
import os
import shutil
import subprocess
import logging
import platform
import json
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)


def check_ffmpeg():
    """Check if FFmpeg is installed and return version info."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version_line = result.stdout.split("\n")[0]
            return True, version_line
        return False, "FFmpeg not found"
    except FileNotFoundError:
        return False, "FFmpeg not installed"
    except Exception as e:
        return False, str(e)


def install_ffmpeg():
    """Attempt to install FFmpeg via winget (Windows)."""
    if platform.system() != "Windows":
        return False, "Auto-install only supported on Windows"
    try:
        result = subprocess.run(
            ["winget", "install", "Gyan.FFmpeg", "--accept-package-agreements", "--accept-source-agreements"],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            return True, "FFmpeg installed successfully"
        return False, result.stderr
    except FileNotFoundError:
        return False, "winget not available"
    except Exception as e:
        return False, str(e)


def check_gpu_available():
    """Check if CUDA GPU is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def get_device():
    """Get the best available compute device."""
    if check_gpu_available():
        return "cuda"
    return "cpu"


def get_compute_type(device):
    """Get optimal compute type for device."""
    if device == "cuda":
        return "float16"
    return "int8"


def format_time(seconds):
    """Format seconds to HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_timestamp(seconds):
    """Format seconds to SRT timestamp format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def get_file_hash(filepath):
    """Get MD5 hash of a file for caching."""
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def clean_temp_files(temp_dir):
    """Clean temporary files."""
    if os.path.exists(temp_dir):
        for item in os.listdir(temp_dir):
            path = os.path.join(temp_dir, item)
            try:
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
            except Exception as e:
                logger.warning(f"Failed to clean temp: {path}: {e}")


def estimate_output_size(duration, width, height, fps, bitrate_mbps=8):
    """Estimate output file size in MB."""
    return (bitrate_mbps * duration) / 8


def estimate_render_time(duration, width, height, fps, preset="medium"):
    """Rough estimate of render time in seconds."""
    pixel_rate = width * height * fps
    preset_factors = {
        "ultrafast": 0.3, "superfast": 0.4, "veryfast": 0.5,
        "faster": 0.7, "fast": 0.8, "medium": 1.0,
        "slow": 1.5, "slower": 2.0, "veryslow": 3.0,
    }
    factor = preset_factors.get(preset, 1.0)
    base_time = duration * (pixel_rate / (1920 * 1080 * 30)) * factor
    return max(base_time, duration * 0.5)


def safe_filename(name):
    """Create a safe filename from a string."""
    keepchars = " ._-"
    name = "".join(c for c in name if c.isalnum() or c in keepchars).strip()
    return name or "untitled"


def get_audio_duration(filepath):
    """Get audio duration using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", filepath],
            capture_output=True, text=True, timeout=30
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def get_system_info():
    """Get system information for performance profiling."""
    cpu_count = os.cpu_count() or 1
    ram_gb = 4.0
    try:
        import psutil
        cpu_count = psutil.cpu_count() or cpu_count
        ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 1)
    except ImportError:
        if platform.system() == "Windows":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                c_ulonglong = ctypes.c_ulonglong
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", c_ulonglong),
                        ("ullAvailPhys", c_ulonglong),
                        ("ullTotalPageFile", c_ulonglong),
                        ("ullAvailPageFile", c_ulonglong),
                        ("ullTotalVirtual", c_ulonglong),
                        ("ullAvailVirtual", c_ulonglong),
                        ("ullAvailExtendedVirtual", c_ulonglong),
                    ]
                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(stat)
                kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
                ram_gb = round(stat.ullTotalPhys / (1024 ** 3), 1)
            except Exception:
                pass
        else:
            try:
                with open("/proc/meminfo") as f:
                    for line in f:
                        if line.startswith("MemTotal"):
                            ram_gb = round(int(line.split()[1]) / (1024 ** 2), 1)
                            break
            except Exception:
                pass

    info = {
        "platform": platform.system(),
        "cpu_count": cpu_count,
        "ram_gb": ram_gb,
        "gpu_available": check_gpu_available(),
    }
    if info["ram_gb"] < 4:
        info["recommended_mode"] = "Low Spec"
    elif info["ram_gb"] < 8:
        info["recommended_mode"] = "Balanced"
    else:
        info["recommended_mode"] = "High Quality"
    return info


def setup_logging(log_dir):
    """Setup application logging."""
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")
    error_log = os.path.join(log_dir, "error.log")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))

    error_handler = logging.FileHandler(error_log, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        "[%(levelname)s] %(message)s"
    ))

    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)
