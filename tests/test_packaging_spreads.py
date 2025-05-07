import pytest
from pathlib import Path

@pytest.fixture
def input_folder():
    # Путь к папке с вашими реальными тестовыми изображениями
    return Path("tests/input/packagingSpreads")

@pytest.fixture
def reference_folder():
    # Путь к папке с эталонными результатами
    return Path("tests/reference/packagingSpreads")


def test_packagingSpreads_produces_expected_files(input_folder, reference_folder, tmp_path):
    output_folder = tmp_path / "output"
    output_folder.mkdir()

    # Вызов вашей функции с реальными входными данными
    packagingSpreads(..., str(input_folder), ..., str(output_folder), ...)

    # Сравнение результатов
    compare_folders_by_hash(str(output_folder), str(reference_folder))
