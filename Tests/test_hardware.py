from collections import namedtuple
import pytest
import psutil
from unittest.mock import patch
from capacity_check import (
    get_cpu_info,
    get_memory_info,
    get_model_number,
    check_processor_type,
    reserve_cores,
    reserve_memory,
    check_hardware_requirements,
    NOT_ACCEPTED,
    NOT_ACCEPTED_CAPITALIZED
)


# Test für get_cpu_info
def test_get_cpu_info():
    with patch('psutil.cpu_count', return_value=4), \
         patch('psutil.cpu_freq', return_value=psutil._common.scpufreq(current=0.0, min=0.0, max=4000.0)):
        cpu_info = get_cpu_info()
        assert cpu_info["Anzahl der physischen Kerne"] == 4
        assert cpu_info["Maximale CPU-Frequenz"] == "4.00 GHz"


# Test für get_memory_info
def test_get_memory_info():
    # Namedtuple mit deckungsgleichem Aufbau wie das svmem-Objekt
    svmem = namedtuple('svmem', 'total available percent used free active inactive buffers cached shared slab')

    # Mock vom svmem-Objekt mit den gewünschten totalen Speicherwerten
    mock_memory = svmem(
        total=16 * 1024 ** 3, available=0, percent=0, used=0, free=0,
        active=0, inactive=0, buffers=0, cached=0, shared=0, slab=0
    )

    with patch('psutil.virtual_memory', return_value=mock_memory):
        memory_info = get_memory_info()
        assert memory_info["Gesamtspeicher"] == "16.00 GB"


# Test für get_model_number
@pytest.mark.parametrize("brand_raw, expected_model_number", [
    ("Intel Core i7-10700K", 10700),
    ("AMD Ryzen 5 3600", 3600),
    ("Apple M1", None),
    ("Intel Xeon E-2276M", 2276),
])
def test_get_model_number(brand_raw, expected_model_number):
    assert get_model_number(brand_raw) == expected_model_number


# Tests für check_processor_type
def test_check_processor_type_intel_core():
    with patch('cpuinfo.get_cpu_info', return_value={"brand_raw": "Intel Core i7-10700K"}):
        assert check_processor_type() == "Accepted"


def test_check_processor_type_amd():
    with patch('cpuinfo.get_cpu_info', return_value={"brand_raw": "AMD Ryzen 7 5800X"}):
        assert check_processor_type() == "Accepted"


def test_check_processor_type_unsupported_vendor():
    with patch('cpuinfo.get_cpu_info', return_value={"brand_raw": "Unknown Processor 3000"}):
        assert check_processor_type() == NOT_ACCEPTED


def test_check_processor_type_no_model_number():
    with patch('cpuinfo.get_cpu_info', return_value={"brand_raw": "Unknown Processor"}):
        assert check_processor_type() == "Not accepted (no model number found)"


# Test für reserve_cores
def test_reserve_cores():
    with patch('psutil.cpu_count', return_value=8), \
         patch('psutil.Process.cpu_affinity') as mock_cpu_affinity:
        reserve_cores(50)
        mock_cpu_affinity.assert_called_with([0, 1, 2, 3])


# Test für reserve_memory
def test_reserve_memory():
    with patch('psutil.virtual_memory', return_value=psutil._common.svmem(total=8 * 1024 ** 3)):
        reserved_memory = reserve_memory(50)
        assert len(reserved_memory) == 4 * 1024 ** 3  # 50% von 8GB


# Integrationstest für check_hardware_requirements
def test_check_hardware_requirements():
    # Namedtuple mit deckungsgleichem Aufbau wie das svmem-Objekt
    svmem = namedtuple('svmem', 'total available percent used free active inactive buffers cached shared slab')

    # Mock vom svmem-Objekt mit den gewünschten totalen Speicherwerten
    mock_memory = svmem(
        total=16 * 1024 ** 3, available=0, percent=0, used=0, free=0,
        active=0, inactive=0, buffers=0, cached=0, shared=0, slab=0
    )

    with patch('psutil.cpu_count', return_value=8), \
         patch('psutil.cpu_freq', return_value=psutil._common.scpufreq(current=0.0, min=0.0, max=4000.0)), \
         patch('psutil.virtual_memory', return_value=mock_memory), \
         patch('cpuinfo.get_cpu_info', return_value={"brand_raw": "Intel Core i7-10700K"}), \
         patch('capacity_check.reserve_cores') as mock_reserve_cores, \
         patch('capacity_check.reserve_memory', return_value=bytearray(1024)) as mock_reserve_memory:
        check_hardware_requirements()

        # Überprüfen, dass die Reservierungsfunktionen aufgerufen wurden
        mock_reserve_cores.assert_called_with(90)
        mock_reserve_memory.assert_called_with(30)
