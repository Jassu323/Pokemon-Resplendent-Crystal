"""Independent polarity, padding, blank and orientation controls."""
import unittest
from PIL import Image
from tools.pokedex_footprint_assets import convert


class FootprintConversionTests(unittest.TestCase):
    def test_emerald_foreground_is_white_and_background_black(self):
        original = Image.new('RGB', (16, 16), 'white')
        original.putpixel((3, 7), (98, 98, 98))
        converted = convert(original).convert('RGB')
        self.assertEqual(converted.getpixel((3, 7)), (255, 255, 255))
        self.assertEqual(converted.getpixel((7, 3)), (0, 0, 0))

    def test_platinum_padding_is_removed_without_scaling(self):
        original = Image.new('RGB', (32, 16), 'black')
        original.paste('white', (0, 0, 16, 16))
        original.putpixel((15, 15), (0, 0, 0))
        result = convert(original).convert('RGB')
        self.assertEqual(result.size, (16, 16))
        self.assertEqual(result.getpixel((15, 15)), (255, 255, 255))
        self.assertEqual(result.getpixel((14, 15)), (0, 0, 0))

    def test_blank_asset_remains_background_only(self):
        self.assertEqual(convert(Image.new('RGB', (16, 16), 'white')).getcolors(), [(256, 1)])

    def test_nonuniform_padding_is_rejected(self):
        original = Image.new('RGB', (32, 16), 'white')
        original.putpixel((17, 2), (0, 0, 0))
        with self.assertRaises(ValueError):
            convert(original)

    def test_wrong_dimensions_are_rejected(self):
        with self.assertRaises(ValueError):
            convert(Image.new('RGB', (8, 8), 'white'))

    def test_unexpected_color_is_rejected(self):
        with self.assertRaises(ValueError):
            convert(Image.new('RGB', (16, 16), 'red'))

    def test_visible_pixel_oracle_rejects_wrong_polarity(self):
        from tools.dex_timing.footprints import pixel_issues
        mask = [False] * 256
        mask[7 * 16 + 3] = True
        frame = Image.new('RGB', (160, 144), (41, 41, 41))
        frame.putpixel((141 + 3, 8 + 7), (255, 255, 255))
        self.assertEqual(pixel_issues(frame, mask, 141, 8), 0)
        frame.putpixel((141 + 3, 8 + 7), (0, 0, 0))
        self.assertEqual(pixel_issues(frame, mask, 141, 8), 1)

    def test_visible_pixel_oracle_rejects_stale_mark_on_blank(self):
        from tools.dex_timing.footprints import pixel_issues
        frame = Image.new('RGB', (160, 144), (41, 41, 41))
        frame.putpixel((141, 8), (255, 255, 255))
        self.assertEqual(pixel_issues(frame, [False] * 256, 141, 8), 1)


if __name__ == '__main__':
    unittest.main()
