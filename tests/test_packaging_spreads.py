import os
import shutil

import pytest
import filecmp
from photoshop import Session

from tests.test_packing_lists import dispatch_case
from utils.file_utils import getJpegFilenames
from utils.photoshop_utils import packagingSpreads, packingLists, packingLastListsWithGroupPages, packagingGroup, \
    types_album, fillLayer, paintLayer, designs_album


@pytest.fixture
def photoshop_session():
    def _create_session(psd_path):
        return Session(action="open", file_path=psd_path, auto_close=True)
    return _create_session

from PIL import Image, ImageChops

def images_are_equal(file1, file2):
    with Image.open(file1) as img1, Image.open(file2) as img2:
        if img1.size != img2.size or img1.mode != img2.mode:
            return False
        diff = ImageChops.difference(img1, img2)
        return not diff.getbbox()  # True если нет различий

def compare_output_with_reference(output_dir, reference_dir):
    output_files = getJpegFilenames(output_dir)
    reference_files = getJpegFilenames(reference_dir)
    assert output_files == reference_files, "Списки файлов не совпадают"
    for file in output_files:
        if file.endswith('.jpg'):
            output_file = os.path.join(output_dir, file)
            reference_file = os.path.join(reference_dir, file)
            assert images_are_equal(output_file, reference_file), f"Файл {file} отличается от эталона"
    return True

def run_test_case(test_case, photoshop_session, tmp_path):
    tmp_path = os.path.join("C:\\programms\\undr\\package\\tests\\test_data\\", test_case)
    input_dir = os.path.join(tmp_path, "input")
    output_dir = os.path.join(tmp_path, "output")
    reference_dir = os.path.join(tmp_path, "references")
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    album_type = types_album[1]

    parsed, runner = dispatch_case(test_case, input_dir)

    with photoshop_session("C:\\programms\\undr\\page.psd") as ps:
        doc = ps.active_document
        jpeg_options = ps.JPEGSaveOptions()
        jpeg_options.quality = 12 # максимальное качество

        fillLayer(ps, doc, paintLayer, designs_album[1])
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
