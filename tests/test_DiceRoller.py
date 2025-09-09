import unittest;

import RollerUtils;
from DiceRoller import DiceError, DefaultDicemodes, Dicemode, DiceSet


class DiceSetTest(unittest.TestCase):
	def _common_asserts(self, result: tuple[list[int], int], dice_sides: int) -> None:
		self.assertFalse(any([r < 1 for r in result[0]]), msg="Roll is less than 1");
		self.assertFalse(any([r > dice_sides for r in result[0]]), msg="Roll is greater than maximum die value");


	def test_dice(self):
		for dice in [4, 6, 8, 10, 12, 20, 100, 3, 7, 11, 13, 42]:
			result: list[tuple[list[int], int]] = DiceSet(10, dice).get_results();

			self._common_asserts(result[0], dice);


	def test_fairness(self):
		num_dice: int = 100000;
		result: list[tuple[list[int], int]] = DiceSet(num_dice, 2).get_results();

		self._common_asserts(result[0], 2);

		ones: int = result[0].count(1);
		twos: int = result[0].count(2);

		# Difference of 5% seems fair, right?
		self.assertTrue(abs(ones - twos) < (num_dice * 0.05), msg=f"Difference in number of 1's and 2's is greater than 5% from {num_dice}");


	def test_fairness2(self):
		num_dice: int = 100000;

		for dice_sides in [4, 6, 8, 10, 12, 20]:
			result: list[tuple[list[int], int]] = DiceSet(num_dice, dice_sides).get_results();

			self._common_asserts(result[0], dice_sides);

			roll_counts: list[int] = [result[0][0].count(i) for i in RollerUtils.range_incl(1, dice_sides)];
			diff_counts: list[int] = [abs(roll_counts[i] - roll_counts[i + 1]) for i in range(-1, dice_sides - 1)];

			self.assertTrue(all([dc < (num_dice * 0.05) for dc in diff_counts]), msg=f"Difference between counts of dice rolls is greater than 5% from {num_dice}");


	def test_add(self):
		for i in RollerUtils.range_incl(1, 20):
			result: list[tuple[list[int], int]] = DiceSet(1, 20, add=i).get_results();

			self._common_asserts(result[0], 20);

			self.assertEqual(result[0][1], i, msg=f"Processed add mod is not {i}, is incorrect value of {result[0][1]}");


	def test_sub(self):
		for i in RollerUtils.range_incl(1, 20):
			result: list[tuple[list[int], int]] = DiceSet(1, 20, add=-i).get_results();

			self._common_asserts(result[0], 20);

			self.assertEqual(result[0][1], -i, msg=f"Processed sub mod is not {-i}, is incorrect value of {result[0][1]}");


	def test_mul(self):
		for i in RollerUtils.range_incl(1, 20):
			result: list[tuple[list[int], int]] = DiceSet(1, 20, mul=i).get_results();

			self.assertEqual(len(result), i, msg=f"Number of sets of dice is not equal to mul mod {i}, is incorrect value of {len(result)}");

			for j in range(len(result)):
				self._common_asserts(result[j], 20);


	def test_reroll(self):
		num_dice: int = 1000;

		for i in RollerUtils.range_incl(1, 20):
			result: list[tuple[list[int], int]] = DiceSet(num_dice, 20, reroll=f"{i}").get_results();

			self._common_asserts(result[0], 20);

			self.assertEqual(len(result[0][0]), num_dice, msg=f"Reroll mod resulted in fewer rolls than original, should be {num_dice}, is incorrect value of {len(result[0][0])}");

			self.assertFalse(any([r == i for r in result[0][0]]), msg=f"Reroll mod of {{{i}}} resulted in roll of {i}");


	def test_reroll_cond(self):
		num_dice: int = 1000;

		for i in RollerUtils.range_incl(2, 20):
			result: list[tuple[list[int], int]] = DiceSet(num_dice, 20, reroll=f"<{i}").get_results();

			self._common_asserts(result[0], 20);

			self.assertEqual(len(result[0][0]), num_dice, msg=f"Reroll mod resulted in fewer rolls than original, should be {num_dice}, is incorrect value of {len(result[0][0])}");

			self.assertFalse(any([r < i for r in result[0][0]]), msg=f"Reroll mod of {{{i}}} resulted in roll of <{i}");

		for i in RollerUtils.range_incl(2, 19):
			result: list[tuple[list[int], int]] = DiceSet(num_dice, 20, reroll=f">={i}").get_results();

			self._common_asserts(result[0], 20);

			self.assertEqual(len(result[0][0]), num_dice, msg=f"Reroll mod resulted in fewer rolls than original, should be {num_dice}, is incorrect value of {len(result[0][0])}");

			self.assertFalse(any([r >= i for r in result[0][0]]), msg=f"Reroll mod of {{{i}}} resulted in roll of >={i}");


	def test_reroll_special(self):
		num_dice: int = 1000;

		for reroll in ["low", "high"]:
			result: list[tuple[list[int], int]] = DiceSet(num_dice, 20, reroll=reroll).get_results();

			self._common_asserts(result[0], 20);

			self.assertEqual(len(result[0][0]), num_dice, msg=f"Reroll mod resulted in fewer rolls than original, should be {num_dice}, is incorrect value of {len(result[0][0])}");


	def test_remove(self):
		num_dice: int = 1000;

		for i in RollerUtils.range_incl(1, 20):
			result: list[tuple[list[int], int]] = DiceSet(1000, 20, remove=f"{i}").get_results();

			self._common_asserts(result[0], 20);

			self.assertLessEqual(len(result[0][0]), 1000, msg=f"Remove mod resulted in more rolls than original, should be less than {num_dice}, is incorrect value of {len(result[0][0])}");

			self.assertFalse(any([r == i for r in result[0][0]]), msg=f"Remove mod of {{{i}}} resulted in roll of {i}");


	def test_remove_cond(self):
		num_dice: int = 1000;

		for i in RollerUtils.range_incl(2, 20):
			result: list[tuple[list[int], int]] = DiceSet(1000, 20, remove=f"<{i}").get_results();

			self._common_asserts(result[0], 20);

			self.assertLessEqual(len(result[0][0]), 1000, msg=f"Remove mod resulted in more rolls than original, should be less than {num_dice}, is incorrect value of {len(result[0][0])}");

			self.assertFalse(any([r < i for r in result[0][0]]), msg=f"Remove mod of {{{i}}} resulted in roll of <{i}");

		for i in RollerUtils.range_incl(2, 19):
			result: list[tuple[list[int], int]] = DiceSet(1000, 20, remove=f">={i}").get_results();

			self._common_asserts(result[0], 20);

			self.assertLessEqual(len(result[0][0]), 1000, msg=f"Remove mod resulted in more rolls than original, should be less than {num_dice}, is incorrect value of {len(result[0][0])}");

			self.assertFalse(any([r >= i for r in result[0][0]]), msg=f"Remove mod of {{{i}}} resulted in roll of >={i}");


	def test_remove_special(self):
		num_dice: int = 1000;

		for remove in ["low", "high"]:
			result: list[tuple[list[int], int]] = DiceSet(1000, 20, remove=remove).get_results();

			self._common_asserts(result[0], 20);

			self.assertLessEqual(len(result[0][0]), 1000, msg=f"Remove mod resulted in more rolls than original, should be less than {num_dice}, is incorrect value of {len(result[0][0])}");


	def test_is_dice(self):
		self.assertTrue(DiceSet.is_dice("1d6"));
		self.assertTrue(DiceSet.is_dice("1d12"));
		self.assertTrue(DiceSet.is_dice("1d6+1"));
		self.assertTrue(DiceSet.is_dice("1d6-10"));
		self.assertTrue(DiceSet.is_dice("5*1d6+2"));
		self.assertTrue(DiceSet.is_dice("10*1d6-1"));
		self.assertTrue(DiceSet.is_dice("1d6{1}"));
		self.assertTrue(DiceSet.is_dice("1d6{<2}"));
		self.assertTrue(DiceSet.is_dice("1d6+1{<=2}"));
		self.assertTrue(DiceSet.is_dice("4*1d6{>=5}"));
		self.assertTrue(DiceSet.is_dice("4*1d6{low}"));
		self.assertTrue(DiceSet.is_dice("10d6[1]"));
		self.assertTrue(DiceSet.is_dice("10d6[<2]"));
		self.assertTrue(DiceSet.is_dice("10d20+2[<=3]"));
		self.assertTrue(DiceSet.is_dice("10d12[>=5]"));
		self.assertTrue(DiceSet.is_dice("10d20[low]"));
		self.assertTrue(DiceSet.is_dice("2.5d6"));
		self.assertTrue(DiceSet.is_dice("2.5d6+1"));
		self.assertTrue(DiceSet.is_dice("2*2.5d6"));
		self.assertTrue(DiceSet.is_dice("4*2.5d6+1"));
		self.assertTrue(DiceSet.is_dice("2.5d6+10{1}"));
		self.assertTrue(DiceSet.is_dice("2.5d6-10[>=6]"));
		self.assertFalse(DiceSet.is_dice("10+10"));
		self.assertFalse(DiceSet.is_dice("d=10"));
		self.assertFalse(DiceSet.is_dice("d20"));
		self.assertFalse(DiceSet.is_dice("4d20{wol}"));
		self.assertFalse(DiceSet.is_dice("1d20{1}[20]"));
		self.assertFalse(DiceSet.is_dice("1d20{1}{2}"));
		self.assertFalse(DiceSet.is_dice("snafu"));


	def test_dice_from_str(self):
		dice: DiceSet = DiceSet.from_str("1d20");

		self.assertEqual(dice.num_dice, 1);
		self.assertEqual(dice.dice_sides, 20);
		self.assertEqual(dice.add_mod, 0);
		self.assertEqual(dice.mul_mod, None);
		self.assertEqual(dice.reroll_mod, None);
		self.assertEqual(dice.remove_mod, None);

		dice = DiceSet.from_str("4*3d8+7{1}");

		self.assertEqual(dice.num_dice, 3);
		self.assertEqual(dice.dice_sides, 8);
		self.assertEqual(dice.add_mod, 7);
		self.assertEqual(dice.mul_mod, 4);
		self.assertEqual(dice.reroll_mod, ("==", 1));
		self.assertEqual(dice.remove_mod, None);

		self.assertEqual(len(dice.sub_dice), 3);
		self.assertEqual(dice.sub_dice[0], dice.sub_dice[1]);

		dice = DiceSet.from_str("4*3d8+7[1]");

		self.assertEqual(dice.num_dice, 3);
		self.assertEqual(dice.dice_sides, 8);
		self.assertEqual(dice.add_mod, 7);
		self.assertEqual(dice.mul_mod, 4);
		self.assertEqual(dice.reroll_mod, None);
		self.assertEqual(dice.remove_mod, ("==", 1));

		self.assertEqual(len(dice.sub_dice), 3);
		self.assertEqual(dice.sub_dice[0], dice.sub_dice[1]);


	def test_error(self):
		with self.assertRaises(DiceError):
			# 0 Multiplier would be no dice rolled
			DiceSet(1, 20, mul=0);

		with self.assertRaises(DiceError):
			# Reroll and remove modifiers is undefined behavior
			DiceSet(1, 20, reroll="1", remove="1");

		with self.assertRaises(DiceError):
			# Reroll mod is not a number
			DiceSet(1, 20, reroll="abc");

		with self.assertRaises(DiceError):
			# Reroll mod would reroll all values
			DiceSet(1, 20, reroll=">0");

		with self.assertRaises(DiceError):
			# Remove mod is not a number
			DiceSet(1, 20, remove="abc");

		with self.assertRaises(DiceError):
			# Remove mod would remove all values
			DiceSet(1, 20, remove=">0");

		with self.assertRaises(DiceError):
			# Remove mod would remove all values
			DiceSet.from_str("I am not a die");


class DicemodeTest(unittest.TestCase):
	def test_10_again(self):
		actions: list[str] = [];

		for line in DefaultDicemodes["10_again"].split("\n")[2:]:
			if line.strip() != "":
				actions.append(line.replace("    ", "\t").removeprefix("\t").rstrip());

		ten_again: Dicemode = Dicemode("10_again", actions);

		for num in [10, 20, 30, 40]:
			dm_vars = ten_again.run(f"{num}d10", capture_print=True);

			self.assertEqual(dm_vars["rolls"].count(8) + dm_vars["rolls"].count(9) + dm_vars["rolls"].count(10), dm_vars["success"]);
			self.assertEqual(dm_vars["rolls"].count(10), dm_vars["rolled_tens"]);


	def test_9_again(self):
		actions: list[str] = [];

		for line in DefaultDicemodes["9_again"].split("\n")[2:]:
			if line.strip() != "":
				actions.append(line.replace("    ", "\t").removeprefix("\t").rstrip());

		ten_again: Dicemode = Dicemode("9_again", actions);

		for num in [10, 20, 30, 40]:
			dm_vars = ten_again.run(f"{num}d10", capture_print=True);

			self.assertEqual(dm_vars["rolls"].count(8) + dm_vars["rolls"].count(9) + dm_vars["rolls"].count(10), dm_vars["success"]);
			self.assertEqual(dm_vars["rolls"].count(9) + dm_vars["rolls"].count(10), dm_vars["rolled_extras"]);


	def test_Hero_normal(self):
		actions: list[str] = [];

		for line in DefaultDicemodes["Hero_normal"].split("\n")[2:]:
			if line.strip() != "":
				actions.append(line.replace("    ", "\t").removeprefix("\t").rstrip());

		ten_again: Dicemode = Dicemode("Hero_normal", actions);

		for num in [10, 20, 30, 40]:
			dm_vars = ten_again.run(f"{num}d6", capture_print=True);

			self.assertEqual(sum(dm_vars["rolls"]), dm_vars["stun"]);
			self.assertEqual(len(dm_vars["rolls"]) - dm_vars["rolls"].count(1) + dm_vars["rolls"].count(6), dm_vars["body"]);


	def test_Hero_kill(self):
		actions: list[str] = [];

		for line in DefaultDicemodes["Hero_kill"].split("\n")[2:]:
			if line.strip() != "":
				actions.append(line.replace("    ", "\t").removeprefix("\t").rstrip());

		ten_again: Dicemode = Dicemode("Hero_kill", actions);

		for num in [10, 20, 30, 40]:
			dm_vars = ten_again.run(f"{num}d6", capture_print=True);

			self.assertEqual(sum(dm_vars["rolls"]), dm_vars["body"]);
			self.assertLessEqual(dm_vars["stun"] / dm_vars["body"], 3);
			self.assertGreaterEqual(dm_vars["stun"] / dm_vars["body"], 1);