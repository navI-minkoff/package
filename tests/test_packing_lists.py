from utils.photoshop_utils import packingLists
from utils.file_utils import getJpegFilenames


def test_packing_lists():
    return


def test_packing_lists_dark():
    return

def test_packing_lists_dark_even_pages():
    test_packing_lists_dark_even_pages_standard()
    test_packing_lists_dark_even_pages_with_individual_lists()
def test_packing_lists_dark_even_pages_standard():
    return

def test_packing_lists_dark_even_pages_with_individual_lists():
    return

def test_packing_lists_with_path(path:str):
    input_path = path + '/input'
    output_path = path + '/output'
    reference_path = path + '/reference'

    all_photos = getJpegFilenames(input_path)
    packingLists()

