import time;
import unittest;

from typing_extensions import override;

from DiceMode import DiceMode;
from DiceRoller import DefaultDicemodes;


class DiceModeTest(unittest.TestCase):
	@override
	def setUp(self):
		self.start_time: float = time.time();

	@override
	def tearDown(self):
		end_time: float = time.time();
		print(f"Test '{self._testMethodName}' took {end_time - self.start_time} seconds");


	def test_10_again(self):
		actions: list[str] = [];

		for line in DefaultDicemodes["10_again"].split("\n")[2:]:
			if line.strip() != "":
				actions.append(line.replace("    ", "\t").removeprefix("\t").rstrip());

		ten_again: DiceMode = DiceMode("10_again", actions);

		for num in [10, 20, 30, 40]:
			dm_vars = ten_again.run(f"{num}d10", capture_print=True, debug=False);

			self.assertEqual(dm_vars["rolls"].count(8) + dm_vars["rolls"].count(9) + dm_vars["rolls"].count(10), dm_vars["success"]);
			self.assertEqual(dm_vars["rolls"].count(10), dm_vars["rolled_tens"]);


	def test_9_again(self):
		actions: list[str] = [];

		for line in DefaultDicemodes["9_again"].split("\n")[2:]:
			if line.strip() != "":
				actions.append(line.replace("    ", "\t").removeprefix("\t").rstrip());

		ten_again: DiceMode = DiceMode("9_again", actions);

		for num in [10, 20, 30, 40]:
			dm_vars = ten_again.run(f"{num}d10", capture_print=True, debug=False);

			self.assertEqual(dm_vars["rolls"].count(8) + dm_vars["rolls"].count(9) + dm_vars["rolls"].count(10), dm_vars["success"]);
			self.assertEqual(dm_vars["rolls"].count(9) + dm_vars["rolls"].count(10), dm_vars["rolled_extras"]);


	def test_Hero_normal(self):
		actions: list[str] = [];

		for line in DefaultDicemodes["Hero_normal"].split("\n")[2:]:
			if line.strip() != "":
				actions.append(line.replace("    ", "\t").removeprefix("\t").rstrip());

		ten_again: DiceMode = DiceMode("Hero_normal", actions);

		for num in [10, 20, 30, 40]:
			dm_vars = ten_again.run(f"{num}d6", capture_print=True, debug=False);

			self.assertEqual(sum(dm_vars["rolls"]), dm_vars["stun"]);
			self.assertEqual(len(dm_vars["rolls"]) - dm_vars["rolls"].count(1) + dm_vars["rolls"].count(6), dm_vars["body"]);


	def test_Hero_kill(self):
		actions: list[str] = [];

		for line in DefaultDicemodes["Hero_kill"].split("\n")[2:]:
			if line.strip() != "":
				actions.append(line.replace("    ", "\t").removeprefix("\t").rstrip());

		ten_again: DiceMode = DiceMode("Hero_kill", actions);

		for num in [10, 20, 30, 40]:
			dm_vars = ten_again.run(f"{num}d6", capture_print=True, debug=False);

			self.assertEqual(sum(dm_vars["rolls"]), dm_vars["body"]);
			self.assertLessEqual(dm_vars["stun"] / dm_vars["body"], 3);
			self.assertGreaterEqual(dm_vars["stun"] / dm_vars["body"], 1);