import unittest;

import RollerUtils;


class RollerUtilsTest(unittest.TestCase):
	def test_range_incl(self):
		self.assertListEqual(RollerUtils.range_incl(1, 4), [1, 2, 3, 4]);
		self.assertListEqual(RollerUtils.range_incl(2, 10), [2, 3, 4, 5, 6, 7, 8, 9, 10]);
		self.assertListEqual(RollerUtils.range_incl(0, 3), [0, 1, 2, 3]);
		self.assertListEqual(RollerUtils.range_incl(-2, 2), [-2, -1, 0, 1, 2]);
		self.assertListEqual(RollerUtils.range_incl(-10, 1), [-10, -9, -8, -7, -6, -5, -4, -3, -2, -1, 0, 1]);


	def test_is_digit(self):
		self.assertTrue(RollerUtils.is_digit("123"));
		self.assertTrue(RollerUtils.is_digit("123.456"));
		self.assertTrue(RollerUtils.is_digit("-123"));
		self.assertTrue(RollerUtils.is_digit("-0"));
		self.assertTrue(RollerUtils.is_digit("123"));
		self.assertFalse(RollerUtils.is_digit("12a3"));
		self.assertFalse(RollerUtils.is_digit("abc"));
		self.assertFalse(RollerUtils.is_digit("number"));
		self.assertTrue(RollerUtils.is_digit("nan"));