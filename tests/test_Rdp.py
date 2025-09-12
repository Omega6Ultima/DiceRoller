import time;
import unittest;

from typing_extensions import override;

import Rdp;


class TestRdp(unittest.TestCase):
	@override
	def setUp(self):
		self.rdp: Rdp.Rdp = Rdp.Rdp();
		self.start_time: float = time.time();


	@override
	def tearDown(self):
		end_time: float = time.time();
		print(f"Test '{self._testMethodName}' took {end_time - self.start_time} seconds");


	def test_add(self):
		self.assertEqual(self.rdp.eval_exp("1 + 2"), 3);
		self.assertEqual(self.rdp.eval_exp("0 + 4"), 4);
		self.assertEqual(self.rdp.eval_exp("3 + 3"), 6);

		self.assertEqual(self.rdp.eval_exp("-9 + 5"), -4);
		self.assertEqual(self.rdp.eval_exp("5 + -9"), -4);
		self.assertEqual(self.rdp.eval_exp("-5 + -5"), -10);


	def test_sub(self):
		self.assertEqual(self.rdp.eval_exp("1 - 2"), -1);
		self.assertEqual(self.rdp.eval_exp("0 - 4"), -4);
		self.assertEqual(self.rdp.eval_exp("3 - 3"), 0);

		self.assertEqual(self.rdp.eval_exp("-9 - 5"), -14);
		self.assertEqual(self.rdp.eval_exp("5 - -9"), 14);
		self.assertEqual(self.rdp.eval_exp("-5 - -5"), 0);


	def test_mul(self):
		self.assertEqual(self.rdp.eval_exp("1 * 2"), 2);
		self.assertEqual(self.rdp.eval_exp("0 * 4"), 0);
		self.assertEqual(self.rdp.eval_exp("3 * 3"), 9);

		self.assertEqual(self.rdp.eval_exp("-9 * 5"), -45);
		self.assertEqual(self.rdp.eval_exp("5 * -9"), -45);
		self.assertEqual(self.rdp.eval_exp("-5 * -5"), 25);


	def test_div(self):
		self.assertEqual(self.rdp.eval_exp("1 / 2"), 0.5);
		self.assertEqual(self.rdp.eval_exp("0 / 4"), 0);
		self.assertEqual(self.rdp.eval_exp("3 / 3"), 1);

		self.assertEqual(self.rdp.eval_exp("-9 / 5"), (-9 / 5));
		self.assertEqual(self.rdp.eval_exp("5 / -9"), (5 / -9));
		self.assertEqual(self.rdp.eval_exp("-5 / -5"), 1);


	def test_mod(self):
		self.assertEqual(self.rdp.eval_exp("1 % 2"), 1);
		self.assertEqual(self.rdp.eval_exp("0 % 4"), 0);
		self.assertEqual(self.rdp.eval_exp("3 % 3"), 0);

		self.assertEqual(self.rdp.eval_exp("-9 % 5"), (-9 % 5));
		self.assertEqual(self.rdp.eval_exp("5 % -9"), (5 % -9));
		self.assertEqual(self.rdp.eval_exp("-5 % -5"), 0);


	def test_factorial(self):
		self.assertEqual(self.rdp.eval_exp("1!"), 1);
		self.assertEqual(self.rdp.eval_exp("0!"), 1);
		self.assertEqual(self.rdp.eval_exp("3!"), 6);

		self.assertEqual(self.rdp.eval_exp("-9!"), -362880);
		self.assertEqual(self.rdp.eval_exp("5!"), 120);
		self.assertEqual(self.rdp.eval_exp("-5!"), -120);


	def test_pow(self):
		self.assertEqual(self.rdp.eval_exp("1 ^ 2"), 1);
		self.assertEqual(self.rdp.eval_exp("0 ^ 4"), 0);
		self.assertEqual(self.rdp.eval_exp("3 ^ 3"), 27);

		self.assertEqual(self.rdp.eval_exp("-9 ^ 5"), -59049);
		self.assertEqual(self.rdp.eval_exp("5 ^ -9"), 0.000000512);
		self.assertEqual(self.rdp.eval_exp("-5 ^ -5"), -0.00032);


	def test_parens(self):
		self.assertEqual(self.rdp.eval_exp("5 - 7 * 3"), -16);
		self.assertEqual(self.rdp.eval_exp("5 - (7 * 3)"), -16);
		self.assertEqual(self.rdp.eval_exp("(5 - 7) * 3"), -6);

		self.assertEqual(self.rdp.eval_exp("4 + 5 * 6 - 2"), 32);
		self.assertEqual(self.rdp.eval_exp("4 + (5 * 6) - 2"), 32);
		self.assertEqual(self.rdp.eval_exp("(4 + 5) * 6 - 2"), 52);
		self.assertEqual(self.rdp.eval_exp("4 + 5 * (6 - 2)"), 24);
		self.assertEqual(self.rdp.eval_exp("(4 + 5) * (6 - 2)"), 36);


	def test_brackets(self):
		self.assertEqual(self.rdp.eval_exp("5 - 7 * 3"), -16);
		self.assertEqual(self.rdp.eval_exp("5 - [7 * 3]"), -16);
		self.assertEqual(self.rdp.eval_exp("[5 - 7] * 3"), -6);

		self.assertEqual(self.rdp.eval_exp("4 + 5 * 6 - 2"), 32);
		self.assertEqual(self.rdp.eval_exp("4 + [5 * 6] - 2"), 32);
		self.assertEqual(self.rdp.eval_exp("[4 + 5] * 6 - 2"), 52);
		self.assertEqual(self.rdp.eval_exp("4 + 5 * [6 - 2]"), 24);
		self.assertEqual(self.rdp.eval_exp("[4 + 5] * (6 - 2)"), 36);


	def test_commas(self):
		self.assertEqual(self.rdp.eval_exp("573,000 + 4"), 573_004);
		self.assertEqual(self.rdp.eval_exp("82,000 - 4"), 81_996);
		self.assertEqual(self.rdp.eval_exp("3,000 * 4"), 12_000);
		self.assertEqual(self.rdp.eval_exp("1,800,064 / 4"), 450_016);
		self.assertEqual(self.rdp.eval_exp("53,286,000 / 6,000"), 8_881);


	def test_vars(self):
		self.rdp.eval_exp("a = 2");
		self.assertEqual(self.rdp.eval_exp("a * 4"), 8);

		self.rdp.eval_exp("b = 17");
		self.assertEqual(self.rdp.eval_exp("b + 5"), 22);

		self.assertEqual(self.rdp.eval_exp("a + b"), 19);


	def test_errors(self):
		with self.assertRaises(SyntaxError):
			self.rdp.eval_exp("1 +");

		with self.assertRaises(SyntaxError):
			self.rdp.eval_exp("3 * (2");

		with self.assertRaises(SyntaxError):
			self.rdp.eval_exp("3 * [2");

		with self.assertRaises(SyntaxError):
			self.rdp.eval_exp("3 * [2)");

		with self.assertRaises(ZeroDivisionError):
			self.rdp.eval_exp("4 / 0");

		with self.assertRaises(OverflowError):
			self.rdp.eval_exp("4 ^ 20000");