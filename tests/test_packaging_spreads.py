import os
import pytest
import filecmp
from photoshop import Session

from tests.test_packing_lists import dispatch_case
from utils.file_utils import getJpegFilenames
from utils.photoshop_utils import packagingSpreads, packingLists, packingLastListsWithGroupPages, packagingGroup, types_album

@pytest.fixture
def photoshop_session():
    def _create_session(psd_path):
        return Session(action="open", file_path=psd_path, auto_close=True)
    return _create_session

def compare_output_with_reference(output_dir, reference_dir):
    output_files = getJpegFilenames(output_dir)
    reference_files = getJpegFilenames(reference_dir)
    assert output_files == reference_files, "Списки файлов не совпадают"
    for file in output_files:
        if file.endswith('.jpg'):
            output_file = os.path.join(output_dir, file)
            reference_file = os.path.join(reference_dir, file)
            assert filecmp.cmp(output_file, reference_file, shallow=False), f"Файл {file} отличается от эталона"
    return True

def run_test_case(test_case, photoshop_session, tmp_path):
    tmp_path = os.path.join("C:\\programms\\undr\\package\\tests\\test_data\\", test_case)
    input_dir = os.path.join(tmp_path, "input")
    output_dir = os.path.join(tmp_path, "output")
    reference_dir = os.path.join(tmp_path, "reference")
    os.makedirs(output_dir, exist_ok=True)
    album_type = types_album[1]  # Например, "Премиум"

    parsed, runner = dispatch_case(test_case, input_dir)

    with photoshop_session("C:\\programms\\undr\\page.psd") as ps:
        doc = ps.active_document
        jpeg_options = ps.JPEGSaveOptions()
        jpeg_options.quality = 12
        runner(ps, doc, jpeg_options, parsed, output_dir, album_type)
        compare_output_with_reference(output_dir, reference_dir)

@pytest.mark.parametrize("test_case", [
    "dark_album\\spreads\\standard",
    "dark_album\\lists\\even_pages\\standard",
    "dark_album\\lists\\odd_pages\\standard",
    "dark_album\\lists_groups\\even_pages\\standard",
    "dark_album\\lists_groups\\even_pages\\with_individual_groups",
    "dark_album\\lists_groups\\even_pages\\with_individual_lists",
    "dark_album\\lists_groups\\even_pages\\with_individual_lists_and_groups",
    "dark_album\\lists_groups\\odd_pages\\standard",
    "dark_album\\lists_groups\\odd_pages\\with_individual_groups",
    "dark_album\\lists_groups\\odd_pages\\with_individual_lists",
    "dark_album\\lists_groups\\odd_pages\\with_individual_lists_and_groups",
    "dark_album\\groups\\even_pages\\standard",
    "dark_album\\groups\\even_pages\\with_individual_groups",
    "dark_album\\groups\\odd_pages\\standard",
])
def test_album_case(test_case, photoshop_session, tmp_path):
    run_test_case(test_case, photoshop_session, tmp_path)
