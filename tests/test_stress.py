import pytest
import numpy as np
import time
import sys
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from frontend.core.core import Core

@pytest.fixture
def core():
    # Подготавливаем аргументы по умолчанию
    default_args = [
        '--radius', '5.0',
        '--num-points', '1000',
        '--fight-radius', '15',
        '--hiss-radius', '30',
        '--window-width', '800',
        '--window-height', '600',
        '--no-use-texture',
        '--no-debug'
    ]
    
    # Патчим sys.argv для Core
    with patch.object(sys, 'argv', [''] + default_args):
        core = Core()
        return core

def test_stress_massive_state_updates(core):
    """
    Стресс-тест: Массовые обновления состояний для большого количества котов
    Проверяет производительность и стабильность core.update_states
    """
    cat_count = 100000
    window_size = (800, 600)  # 4K разрешение
    
    positions = np.random.uniform(-1, 1, (cat_count, 2)).astype(np.float64)
    
    start_time = time.time()
    for _ in range(100):  # 100 последовательных обновлений
        states = core.update_states(
            cat_count,
            positions,
            window_size[0],
            window_size[1]
        )
        positions += np.random.uniform(-0.01, 0.01, (cat_count, 2))
        
    execution_time = time.time() - start_time
    
    assert execution_time < 30, f"State updates took too long: {execution_time} seconds"
    assert len(states) == cat_count, "All cats should be processed"

def test_stress_concurrent_state_calculations(core):
    """
    Стресс-тест: Параллельные вычисления состояний
    Проверяет работу системы при одновременных вычислениях в разных потоках
    """
    cat_counts = [100000, 200000, 300000, 400000]  # Разные размеры групп
    window_size = (1920, 1080)
    
    def calculate_states(count):
        positions = np.random.uniform(-1, 1, (count, 2)).astype(np.float64)
        return core.update_states(count, positions, window_size[0], window_size[1])
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(calculate_states, count) for count in cat_counts]
        results = [future.result() for future in futures]
    
    for count, states in zip(cat_counts, results):
        assert len(states) == count, f"Incorrect number of states for {count} cats"

def test_stress_memory_usage(core):
    """
    Стресс-тест: Использование памяти
    Проверяет утечки памяти при длительной работе с большими данными
    """
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    cat_count = 500000
    window_size = (1920, 1080)
    
    for _ in range(50):  # 50 итераций с созданием новых данных
        positions = np.random.uniform(-1, 1, (cat_count, 2)).astype(np.float64)
        states = core.update_states(cat_count, positions, window_size[0], window_size[1])
        del positions
        del states
    
    final_memory = process.memory_info().rss
    memory_increase = (final_memory - initial_memory) / 1024 / 1024  # В МБ
    
    assert memory_increase < 100, f"Memory increase too high: {memory_increase}MB"

def test_stress_rapid_position_updates(core):
    """
    Стресс-тест: Быстрые обновления позиций
    Проверяет производительность при частых обновлениях позиций
    """
    cat_count = 200000
    window_size = (800, 600)
    positions = np.random.uniform(-1, 1, (cat_count, 2)).astype(np.float64)
    
    start_time = time.time()
    
    for _ in range(1000):  # 1000 быстрых обновлений
        deltas = core.generate_deltas(None, cat_count, 1.0)
        positions += deltas
        states = core.update_states(cat_count, positions, window_size[0], window_size[1])
    
    execution_time = time.time() - start_time
    
    assert execution_time < 60, f"Position updates took too long: {execution_time} seconds"

def test_stress_boundary_conditions_performance(core):
    """
    Стресс-тест: Производительность при граничных условиях
    Проверяет производительность когда все коты находятся на границах
    """
    cat_count = 300000
    window_size = (1920, 1080)
    
    # Создаем позиции на границах
    boundary_positions = np.array([
        [1.0, 1.0],  # Верхний правый угол
        [-1.0, 1.0], # Верхний левый угол
        [1.0, -1.0], # Нижний правый угол
        [-1.0, -1.0] # Нижний левый угол
    ])
    
    positions = np.repeat(boundary_positions, cat_count // 4, axis=0)
    
    start_time = time.time()
    for _ in range(100):
        states = core.update_states(len(positions), positions, window_size[0], window_size[1])
    
    execution_time = time.time() - start_time
    
    assert execution_time < 30, f"Boundary condition processing took too long: {execution_time} seconds"