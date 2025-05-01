import unittest
import os
from PIL import Image, ImageChops
import shutil

from utils.photoshop_utils import packagingSpreads

class TestPackagingSpreadsIntegration(unittest.TestCase):
    def setUp(self):
        self.folder_path = "test_data/input"
        self.output_path = "test_data/output"
        self.teacher_path = "test_data/teacher.jpg"
        self.kind_image = "test_data/kind.jpg"
        self.jpeg_filenames = ["1.jpg", "2.jpg"]
        self.jpeg_options = None  # Подставь объект, если нужен
        self.ps = DummyPhotoshopContext()
        self.doc = DummyDocument()
        self.album_type = 'Type3'  # types_album[2]
        self.prefix = "01"

        # Очистка и подготовка папки вывода
        if os.path.exists(self.output_path):
            shutil.rmtree(self.output_path)
        os.makedirs(self.output_path)

        # Патчим глобальные переменные, если нужно
        global shared_postfix, types_album
        shared_postfix = "test_postfix.jpg"
        types_album = ["Type1", "Type2", "Type3"]

    def compare_images(self, img1_path, img2_path):
        img1 = Image.open(img1_path).convert("RGB")
        img2 = Image.open(img2_path).convert("RGB")
        diff = ImageChops.difference(img1, img2)
        return not diff.getbbox()  # True если одинаковы

    def test_output_matches_reference(self):
        packagingSpreads(self.ps, self.doc, self.jpeg_options, self.folder_path, self.jpeg_filenames,
                         self.teacher_path, self.output_path, self.album_type, prefix=self.prefix)

        expected_files = ["01.jpg", "02.jpg", "02test_postfix.jpg"]
        for fname in expected_files:
            out_path = os.path.join(self.output_path, fname)
            ref_path = os.path.join("test_data/reference", fname)
            self.assertTrue(os.path.exists(out_path), f"{out_path} was not created.")
            self.assertTrue(self.compare_images(out_path, ref_path), f"{fname} does not match reference.")

# --- Заглушки для Photoshop API ---
class DummyPhotoshopContext:
    pass  # или расширь при необходимости

class DummyDocument:
    def saveAs(self, path, jpeg_options, asCopy):
        shutil.copy("test_data/input/1.jpg", path)  # эмуляция сохранения

# Запуск
if __name__ == '__main__':
    unittest.main()
