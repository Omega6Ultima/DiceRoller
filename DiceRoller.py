import argparse
import io
import os
import platform
import random
import re;
import sys
import threading
from argparse import Namespace
from io import StringIO
from typing import Callable, TextIO;

import playsound3;

import Rdp;
import RollerUtils
from Rdp import Rdp;
from RollerUtils import *;

# Tab character for use in f-strings
Tab: str = "\t";
# Comparison signs and their related functions
Comparisons: dict[str, Callable] = {
	"<=": lambda a, b: a <= b,
	">=": lambda a, b: a >= b,
	"<": lambda a, b: a < b,
	">": lambda a, b: a > b,
	"==": lambda a, b: a == b,
	"!=": lambda a, b: a != b,

	"lte": lambda a, b: a <= b,
	"gte": lambda a, b: a >= b,
	"lt": lambda a, b: a < b,
	"gt": lambda a, b: a > b,
	"eq": lambda a, b: a == b,
	"neq": lambda a, b: a != b,
};
# Calculation signs and their related functions
Calculations: dict[str, Callable] = {
	"+": lambda a, b: a + b,
	"-": lambda a, b: a - b,
	"*": lambda a, b: a * b,
	"/": lambda a, b: a / b,

	"add": lambda a, b: a + b,
	"sub": lambda a, b: a - b,
	"mul": lambda a, b: a * b,
	"div": lambda a, b: a / b,
};
# The default dicemode filename
DefaultDicemodeFile: str = "dicemodes.txt";
# The pre-defined dicemodes, will be written to file if it doesn't exist
DefaultDicemodes: dict[str, str] = {
	"10_again":"""
dicemode(10_again):
    store(0, rolled_tens)
    store(0, zero)
    check(d10)
    roll(dice)
    count(eq, 10, tens)
    while(tens, gt, zero)
        foreach(tens, roll(1d10))
        calc(rolled_tens, +, tens)
        count(eq, 10, tens)
        calc(tens, -, rolled_tens)
    count(gte, 8, success)
    print(success)

""",
	"9_again":"""
dicemode(9_again):
    store(0, rolled_extras)
    store(0, zero)
    check(d10)
    roll(dice)
    count(gte, 9, extras)
    while(extras, gt, zero)
        foreach(extras, roll(1d10))
        calc(rolled_extras, +, extras)
        count(gte, 9, extras)
        calc(extras, -, rolled_extras)
    count(gte, 8, success)
    print(success)

""",
	"Hero_normal":"""
dicemode(Hero_normal):
    check(d6)
    roll(dice)
    total(stun)
    count(gt, 1, body)
    count(eq, 6, more_body)
    calc(body, +, more_body)
    print(stun)
    print(body)

""",
	"Hero_kill":"""
dicemode(Hero_kill):
    check(d6)
    roll(dice)
    rollinto(1d3, stun)
    total(body)
    calc(stun, mul, body)
    print(stun)
    print(body)

""",
};

class DiceError(Exception):
	def __init__(self, text: str):
		Exception.__init__(self, text);
		self.msg = text;


	def __str__(self) -> str:
		return f"DiceError {self.msg}";


class SoundTimer:
	def __init__(self, time_sec: int, sound: str):
		self.sound = sound;
		self._timer = threading.Timer(time_sec, self.run);

		self._timer.start();

	def run(self):
		playsound3.playsound(self.sound);


class DiceSet:
	ValidComparisons: list[str] = ["<=", ">=", "<", ">"];
	DicePattern: re.Pattern = re.compile(r"""(\d+\*)?            		# optional multiplier
											\d+(?:\.\d+)?               		# number of dice
											d
											\d+                         		# number of sides
											([+-]\d+)?                  		# optional add/sub
											(?:									# one of (or none)
											(\{(?:[<>=]*\d+ | low | high)})? |	# optional reroll modifier
											(\[(?:[<>=]*\d+ | low | high)])?	# optional remove modifier
											)?""", re.X);

	def __init__(self, num_dice: float, dice_sides: int, mul: None | int = None, add: None | int = None, reroll: None | str = None, remove: None | str = None):
		self.num_dice: float = num_dice;
		self.dice_sides: int = dice_sides;

		self.mul_mod: None | int = mul;
		self.add_mod: int = add if add else 0;
		self.reroll_mod: None | tuple[str, int] = None;
		self.remove_mod: None | tuple[str, int] = None;

		self.result: None | list[int] = None;
		self.sub_dice: None | list[DiceSet] = None;
		self._display: None | str = None;

		# Validity checks
		if self.mul_mod is not None and self.mul_mod <= 0:
			raise DiceError("Mul mod cannot be 0 or negative");

		if reroll and remove:
			raise DiceError("Cannot specify reroll and remove modifiers together");

		# Process passed modifiers
		if reroll:
			if RollerUtils.is_digit(reroll):
				self.reroll_mod = ("==", int(reroll));
			elif any([comp in reroll for comp in self.ValidComparisons]):
				for comp in self.ValidComparisons:
					if comp in reroll:
						self.reroll_mod = (comp, int(reroll.removeprefix(comp)));

						break;
			else:
				raise DiceError(f"Invalid reroll modifier '{reroll}'");

			if Comparisons[self.reroll_mod[0]](1, self.reroll_mod[1]) and Comparisons[self.reroll_mod[0]](self.dice_sides, self.reroll_mod[1]):
				raise DiceError(f"Reroll modifier '{self.reroll_mod[0]}{self.reroll_mod[1]}' would reroll all possible values");
		elif remove:
			if RollerUtils.is_digit(remove):
				self.remove_mod = ("==", int(remove));
			elif any([comp in remove for comp in self.ValidComparisons]):
				for comp in self.ValidComparisons:
					if comp in remove:
						self.remove_mod = (comp, int(remove.removeprefix(comp)));

						break;
			else:
				raise DiceError(f"Invalid remove modifier '{remove}'");

			if Comparisons[self.remove_mod[0]](1, self.remove_mod[1]) and Comparisons[self.remove_mod[0]](self.dice_sides, self.remove_mod[1]):
				raise DiceError(f"Remove modifier '{self.remove_mod[0]}{self.remove_mod[1]}' would remove all possible values");

		if self.mul_mod is not None:
			self.sub_dice = [];

			for _ in range(self.mul_mod - 1):
				dice: DiceSet = DiceSet(self.num_dice, self.dice_sides, add=self.add_mod);
				dice.reroll_mod = self.reroll_mod;
				dice.remove_mod = self.remove_mod;

				self.sub_dice.append(dice);


	def roll_single(self) -> int:
		"""Roll a single die and return the result"""
		return random.randint(1, self.dice_sides);


	@classmethod
	def from_str(cls, text: str) -> "DiceSet":
		"""Parse the passed string and return a DiceSet constructed from the string"""
		if DiceSet.is_dice(text):
			num_dice: str = text[:text.find("d")];
			dice_side: str = text[text.find("d") + 1:];

			mods: dict[str, any] = {};

			# Peel off modifiers starting from the front or back and work inwards
			if "*" in num_dice:
				mul, num_dice = num_dice.split("*");

				mods["mul"] = int(mul);

			if "{" in dice_side:
				dice_side, reroll = dice_side.split("{");

				mods["reroll"] = reroll.strip("{}");
			elif "[" in dice_side:
				dice_side, remove = dice_side.split("[");

				mods["remove"] = remove.strip("[]");

			if "+" in dice_side:
				dice_side, add = dice_side.split("+");

				mods["add"] = int(add);
			elif "-" in dice_side:
				dice_side, sub = dice_side.split("-");

				mods["add"] = int(sub);

			try:
				return DiceSet(float(num_dice), int(dice_side), **mods);
			except ValueError as e:
				print(e);

		raise DiceError(f"Invalid dice format {text}");


	@staticmethod
	def is_dice(text: str) -> bool:
		if DiceSet.DicePattern.fullmatch(text):
			return True;

		return False;


	def verify_dice(self, die_sides: int) -> bool:
		"""Return True if the diceset uses the number of sides passed in"""
		return self.dice_sides == die_sides;


	def process(self) -> None:
		"""Process the DiceSet and roll the dice represented by the DiceSet"""
		self._display = None;

		if self.result is None:
			self.result = [];
		else:
			self.result.clear();

		for _ in range(int(self.num_dice)):
			self.result.append(self.roll_single());

		if self.reroll_mod:
			for i in range(len(self.result)):
				while Comparisons[self.reroll_mod[0]](self.result[i], self.reroll_mod[1]):
					self.result[i] = self.roll_single();
		elif self.remove_mod:
			to_remove: list[int] = [];

			for i in range(len(self.result)):
				if Comparisons[self.remove_mod[0]](self.result[i], self.remove_mod[1]):
					to_remove.append(i);

			for i in reversed(to_remove):
				del self.result[i];

		if self.sub_dice:
			for dice in self.sub_dice:
				dice.process();


	def display(self) -> str:
		"""Return a string representing the DiceSet"""
		if self._display is None:
			builder: list[str] = [];

			if self.mul_mod:
				builder.append(f"{self.mul_mod}*");

			builder.append(f"{self.num_dice}d{self.dice_sides}");

			if self.add_mod:
				if self.add_mod > 0:
					builder.append(f"+{self.add_mod}");
				else:
					builder.append(f"-{self.add_mod}");

			if self.reroll_mod:
				builder.append(f"{{{self.reroll_mod[0]}{self.reroll_mod[1]}}}");

			if self.remove_mod:
				builder.append(f"[{self.remove_mod[0]}{self.remove_mod[1]}]");

			self._display = "".join(builder);

		return self._display;


	def get_results(self) -> list[tuple[list[int], int]]:
		"""Returns the results of rolling the DiceSet"""
		results: list[tuple[list[int], int]] = [];

		if self.result is None:
			self.process();

		results.append((self.result, self.add_mod));

		if self.sub_dice:
			for dice in self.sub_dice:
				results.append((dice.result, dice.add_mod));

		return results;


	def __str__(self) -> str:
		builder: list[str] = [];

		if self.result is None:
			self.process();

		builder.append(f"{self.result}");

		if self.add_mod:
			if self.add_mod > 0:
				builder.append(f" + {self.add_mod}");
			else:
				builder.append(f" - {self.add_mod}");

		if self.sub_dice:
			for dice in self.sub_dice:
				builder.append(f", {str(dice)}");

		builder.append(f" = {int(self)}");

		return "".join(builder);


	def __int__(self) -> int:
		total: int = 0;

		if self.result is None:
			self.process();

		total += sum(self.result) + self.add_mod;

		if self.sub_dice:
			for dice in self.sub_dice:
				total += sum(dice.result) + dice.add_mod;

		return total;


	def __eq__(self, other: "DiceSet") -> bool:
		if not isinstance(other, DiceSet):
			raise TypeError(f"Trying to compare DiceSet to {type(other)}");

		if self.num_dice != other.num_dice:
			return False;

		if self.dice_sides != other.dice_sides:
			return False;

		if self.add_mod != other.add_mod:
			return False;

		if self.mul_mod != other.mul_mod:
			return False;

		if self.reroll_mod != other.reroll_mod:
			return False;

		if self.remove_mod != other.remove_mod:
			return False;

		return True;


class Dicemode:
	def __init__(self, name: str, actions: list[str]):
		self.name: str = name;
		self.actions: list[str] = actions.copy();
		self.action_index: int = 0;
		self.done: bool = False;
		self.loop_entry: None | int = None;
		self.loop_end: None | int = None;
		self.output: TextIO | StringIO = sys.stdout;


	def run(self, dice: str, debug: bool = False, capture_print: bool = False) -> dict[str, any]:
		self.done = False;
		self.loop_entry = None;
		self.loop_end = None;
		self.action_index = 0;

		if capture_print:
			self.output = io.StringIO();

		diceset: DiceSet = DiceSet.from_str(dice);

		mode_vars: dict[str, any] = {
			"True": True,
			"False": False,
			"rolls": [],
			"rolls_adj": 0,
		};

		while not self.done:
			self._execute_action(self.actions[self.action_index], diceset, mode_vars, debug);

			self.action_index += 1;

			if self.action_index >= len(self.actions):
				if self.loop_entry is not None:
					self.action_index = self.loop_entry;
				else:
					self.done = True;

		if debug:
			print(mode_vars);

		if capture_print:
			mode_vars["output"] = self.output.getvalue();

			self.output = sys.stdout;

		return mode_vars;


	@staticmethod
	def _collect_args(text: str) -> list[str]:
		action: str = text[:text.find("(") + 1];
		arg_str: str = text.removeprefix(action).removesuffix(")");
		arg_list: list[str] = [a.strip() for a in arg_str.split(",")];

		arg_index: int = 0;

		while arg_index < len(arg_list):
			if "(" in arg_list[arg_index] and not ")" in arg_list[arg_index]:
				arg_list[arg_index] += f", {arg_list[arg_index + 1]}";
			else:
				arg_index += 1;

		return arg_list;


	def _execute_action(self, action: str, diceset: DiceSet, mode_vars: dict[str, any], debug: bool = False) -> None:
		if self.loop_entry is not None:
			if self.action_index > self.loop_end:
				self.action_index = self.loop_entry;

				action = self.actions[self.action_index];

		clean_action: str = action.lstrip();

		if debug:
			print(f"Executing action #{self.action_index} '{clean_action}'", file=self.output);

		if clean_action.startswith("store("):
			args: list[str] = self._collect_args(clean_action);

			val: float = float(args[0]);
			var: str = args[1];

			if debug:
				print(f"  Storing {val} into '{var}'", file=self.output);

			mode_vars[var] = val;
		elif clean_action.startswith("check("):
			args: list[str] = self._collect_args(clean_action);

			die_sides: int = int(args[0].removeprefix("d"));

			if debug:
				print(f"  Checking dice are d{die_sides}'s", file=self.output);

			if not diceset.verify_dice(die_sides):
				self.done = True;

				print(f"Using dicemode {self.name} with non-d{die_sides}, dice passed are {diceset.dice_sides}", file=self.output);
		elif clean_action.startswith("roll("):
			args: list[str] = self._collect_args(clean_action);
			result: list[tuple[list[int], int]] = [];

			dice: str = args[0];

			try:
				if dice == "dice":
					if debug:
						print(f"  Rolling {diceset.display()}", file=self.output);

					result.extend(diceset.get_results());
				else:
					if debug:
						print(f"  Rolling {dice}", file=self.output);

					result.extend(DiceSet.from_str(dice).get_results());
			except DiceError as e:
				print(e, file=self.output);

				self.done = True;

				return;

			for i in range(len(result)):
				mode_vars["rolls"].extend(result[i][0]);
				mode_vars["rolls_adj"] += result[i][1];
		elif clean_action.startswith("rollinto("):
			args: list[str] = self._collect_args(clean_action);
			result: int = 0;

			dice: str = args[0];
			var: str = args[1];

			try:
				if debug:
					print(f"  Rolling {dice} and storing into '{var}'", file=self.output);

				result += int(DiceSet.from_str(dice));
			except DiceError as e:
				print(e, file=self.output);

				self.done = True;

				return;

			mode_vars[var] = result;
		elif clean_action.startswith("total("):
			args: list[str] = self._collect_args(clean_action);

			var: str = args[0];

			if debug:
				print(f"  Totaling dice rolls and storing into '{var}'", file=self.output);

			mode_vars[var] = sum(mode_vars["rolls"]) + mode_vars["rolls_adj"];
		elif clean_action.startswith("count("):
			args: list[str] = self._collect_args(clean_action);

			comp: str = args[0];
			val: float = float(args[1]);
			var: str = args[2];

			if comp not in Comparisons:
				print(f"'{comp}' is not a valid comparison", file=self.output);

				self.done = True;

				return;

			if debug:
				print(f"  Counting rolls that match {comp} {val} and storing into '{var}'", file=self.output);

			count: int = 0;

			for roll in mode_vars["rolls"]:
				if Comparisons[comp](roll, val):
					count += 1;

			if debug:
				print(f"  Matching rolls: {count}, Non-matching rolls: {len(mode_vars["rolls"]) - count}", file=self.output);

			mode_vars[var] = count;
		elif clean_action.startswith("calc("):
			args: list[str] = self._collect_args(clean_action);

			var1: str = args[0];
			op: str = args[1];
			var2: str = args[2];

			if var1 not in mode_vars:
				print(f"'{var1}' has not been set before use", file=self.output);

				self.done = True;

				return;

			if op not in Calculations:
				print(f"'{op}' is not a valid calculation", file=self.output);

				self.done = True;

				return;

			if var2 not in mode_vars:
				print(f"'{var2}' has not been set before use", file=self.output);

				self.done = True;

				return;

			if debug:
				print(f"  Calculating '{var1} {op} {var2}' and storing into '{var1}'", file=self.output);
				print(f"  {mode_vars[var1]} {op} {mode_vars[var2]} = {Calculations[op](mode_vars[var1], mode_vars[var2])}", file=self.output);

			mode_vars[var1] = Calculations[op](mode_vars[var1], mode_vars[var2]);
		elif clean_action.startswith("if("):
			args: list[str] = self._collect_args(clean_action);

			var1: str = args[0];
			comp: str = args[1];
			var2: str = args[2];
			sub_action = args[3];

			if var1 not in mode_vars:
				print(f"'{var1}' has not been set before use", file=self.output);

				self.done = True;

				return;

			if comp not in Comparisons:
				print(f"'{comp}' is not a valid calculation", file=self.output);

				self.done = True;

				return;

			if var2 not in mode_vars:
				print(f"'{var2}' has not been set before use", file=self.output);

				self.done = True;

				return;

			if debug:
				print(f"  If '{var1} {comp} {var2}' is True, then execute '{sub_action}'", file=self.output);
				print(f"  {mode_vars[var1]} {comp} {mode_vars[var2]} = {Comparisons[comp](mode_vars[var1], mode_vars[var2])}", file=self.output);

			if Comparisons[comp](mode_vars[var1], mode_vars[var2]):
				self._execute_action(sub_action, diceset, mode_vars, debug);
		elif clean_action.startswith("foreach("):
			args: list[str] = self._collect_args(clean_action);

			var: str = args[0];
			sub_action: str = args[1];

			if var not in mode_vars:
				print(f"'{var}' has not been set before use", file=self.output);

				self.done = True;

				return;

			if debug:
				print(f"  Looping {int(mode_vars[var])} times and running '{sub_action}'", file=self.output);

			for _ in range(int(mode_vars[var])):
				self._execute_action(sub_action, diceset, mode_vars, debug);
		elif clean_action.startswith("while("):
			args: list[str] = self._collect_args(clean_action);

			var1: str = args[0];
			comp: str = args[1];
			var2: str = args[2];

			if var1 not in mode_vars:
				print(f"'{var1}' has not been set before use", file=self.output);

				self.done = True;

				return;

			if comp not in Comparisons:
				print(f"'{comp}' is not a valid calculation", file=self.output);

				self.done = True;

				return;

			if var2 not in mode_vars:
				print(f"'{var2}' has not been set before use", file=self.output);

				self.done = True;

				return;

			# Calculate loop_end
			if self.loop_end is None:
				loop_end: int = self.action_index + 1;
				indent_level: str = self.actions[loop_end].count("\t") * "\t";

				while self.actions[loop_end].startswith(indent_level):
					loop_end += 1;

				self.loop_end = loop_end - 1;

			if debug:
				print(f"  Looping while '{var1} {comp} {var2}' from action #{self.action_index} to #{self.loop_end}", file=self.output);
				print(f"  {mode_vars[var1]} {comp} {mode_vars[var2]} = {Comparisons[comp](mode_vars[var1], mode_vars[var2])}", file=self.output);

			if Comparisons[comp](mode_vars[var1], mode_vars[var2]):
				self.loop_entry = self.action_index;
			else:
				self.action_index = self.loop_end;
				self.loop_entry = None;
				self.loop_end = None;
		elif clean_action.startswith("break"):
			if self.loop_entry is None:
				print("Break action outside of loop", file=self.output);

			if debug:
				print(f"  Breaking out from loop({self.loop_entry}-{self.loop_end})", file=self.output);

			self.action_index = self.loop_end;
			self.loop_entry = None;
			self.loop_end = None;
		elif clean_action.startswith("print("):
			args: list[str] = self._collect_args(clean_action);

			var: str = args[0];

			if var not in mode_vars:
				print(f"'{var}' has not been set before use", file=self.output);

				self.done = True;

				return;

			if debug:
				print(f"  Printing value of '{var}'", file=self.output);

			print(f"{var} = {mode_vars[var]}", file=self.output);


def get_help(context: str = "") -> None:
	match context:
		case "dicemode" | "dicemodes":
			print(DicemodeHelpStr);
		case _:
			print(HelpStr);


def start_timer(seconds: str, sound: str = "alarm-clock-1.wav") -> None:
	SoundTimer(int(seconds), sound);


HelpStr: str = f"""
help <context>{Tab * 3}get help with topic
exit{Tab * 5}exit the program
stop{Tab * 5}stop the program
quit{Tab * 5}quit the program
timer <sec> [sound]{Tab * 2}start a timer for <sec> seconds and with [sound]
clear{Tab * 5}clear the output
coin{Tab * 5}toss a coin
dicemode <mode>{Tab * 3}switch to <mode> dicemode, all subsequent rolls with be processed through that dicemode
1d4{Tab * 6}roll a 1d4
1d6+1{Tab * 5}roll a 1d6 and add 1
1d8-3{Tab * 5}roll a 1d8 and subtract 3
3*1d10+2{Tab * 4}roll 3 sets of 1d10+2
6d12{{1}}{Tab * 5}roll 6d12 and reroll any 1's
6d12{{<6}}{Tab * 4}roll 6d12 and reroll any matching the condition
6d12{{low}}{Tab * 4}roll 6d12 and reroll the lowest roll
3d20[20]{Tab * 4}roll 3d20 and remove any and all 20's
3d20[>=16]{Tab * 4}roll 3d20 and remove any rolls matching the condition
3d20[low]{Tab * 4}roll 3d20 and remove the lowest roll
""";
DicemodeHelpStr: str = f"""
dicemode actions:
store(0, zero){Tab}store 0 into the var 'zero'
check(d20){Tab}check that the dice passed are d20's
roll(dice){Tab}roll the dice passed and add the rolls to the master list
roll(2d10){Tab}roll the 2d10 and add the rolls to the master list
rollinto(1d4+1, uses){Tab}roll 1d4+1 and store the total into 'uses'
total(damage){Tab}add up all rolls and additions from the master list and store into 'damage'
count(eq, 20, crits){Tab}count the rolls equal to 20 and store into 'crits'
calc(damage, div, two){Tab}calculate the result of 'damage' / 2 and store into 'damage'
if(crits, gte, one, roll(1d8)){Tab}if 'crits' is greater than or equal to 'one', execute 'roll(1d8)'
foreach(hit, roll(1d10)){Tab}Repeat 'roll(1d10)' 'hit' number of times
while(hp, lt, max_hp){Tab}Repeat the indented actions below while hp is less than max hp
break{Tab}exit a while loop immediately and without checking the condition
print(damage){Tab}print "damage = <value of damage>"

Example dicemode:
{DefaultDicemodes['10_again']}
""";
Commands: dict[str, Callable] = {
	"help": get_help,
	"timer": start_timer,
	"clear": lambda: os.system("cls") if "win" in platform.system().lower() else os.system("clear"),
	"coin": lambda: print("Heads(1)" if int(DiceSet(1, 2)) == 1 else "Tails(2)"),
};

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

			roll_counts: list[int] = [result[0][0].count(i) for i in range_incl(1, dice_sides)];
			diff_counts: list[int] = [abs(roll_counts[i] - roll_counts[i + 1]) for i in range(-1, dice_sides - 1)];

			self.assertTrue(all([dc < (num_dice * 0.05) for dc in diff_counts]), msg=f"Difference between counts of dice rolls is greater than 5% from {num_dice}");


	def test_add(self):
		for i in range_incl(1, 20):
			result: list[tuple[list[int], int]] = DiceSet(1, 20, add=i).get_results();

			self._common_asserts(result[0], 20);

			self.assertEqual(result[0][1], i, msg=f"Processed add mod is not {i}, is incorrect value of {result[0][1]}");


	def test_sub(self):
		for i in range_incl(1, 20):
			result: list[tuple[list[int], int]] = DiceSet(1, 20, add=-i).get_results();

			self._common_asserts(result[0], 20);

			self.assertEqual(result[0][1], -i, msg=f"Processed sub mod is not {-i}, is incorrect value of {result[0][1]}");


	def test_mul(self):
		for i in range_incl(1, 20):
			result: list[tuple[list[int], int]] = DiceSet(1, 20, mul=i).get_results();

			self.assertEqual(len(result), i, msg=f"Number of sets of dice is not equal to mul mod {i}, is incorrect value of {len(result)}");

			for j in range(len(result)):
				self._common_asserts(result[j], 20);


	def test_reroll(self):
		num_dice: int = 1000;

		for i in range_incl(1, 20):
			result: list[tuple[list[int], int]] = DiceSet(num_dice, 20, reroll=f"{i}").get_results();

			self._common_asserts(result[0], 20);

			self.assertEqual(len(result[0][0]), num_dice, msg=f"Reroll mod resulted in fewer rolls than original, should be {num_dice}, is incorrect value of {len(result[0][0])}");

			self.assertFalse(any([r == i for r in result[0][0]]), msg=f"Reroll mod of {{{i}}} resulted in roll of {i}");


	def test_reroll_cond(self):
		num_dice: int = 1000;

		for i in range_incl(2, 20):
			result: list[tuple[list[int], int]] = DiceSet(num_dice, 20, reroll=f"<{i}").get_results();

			self._common_asserts(result[0], 20);

			self.assertEqual(len(result[0][0]), num_dice, msg=f"Reroll mod resulted in fewer rolls than original, should be {num_dice}, is incorrect value of {len(result[0][0])}");

			self.assertFalse(any([r < i for r in result[0][0]]), msg=f"Reroll mod of {{{i}}} resulted in roll of <{i}");

		for i in range_incl(2, 19):
			result: list[tuple[list[int], int]] = DiceSet(num_dice, 20, reroll=f">={i}").get_results();

			self._common_asserts(result[0], 20);

			self.assertEqual(len(result[0][0]), num_dice, msg=f"Reroll mod resulted in fewer rolls than original, should be {num_dice}, is incorrect value of {len(result[0][0])}");

			self.assertFalse(any([r >= i for r in result[0][0]]), msg=f"Reroll mod of {{{i}}} resulted in roll of >={i}");


	def test_remove(self):
		num_dice: int = 1000;

		for i in range_incl(1, 20):
			result: list[tuple[list[int], int]] = DiceSet(1000, 20, remove=f"{i}").get_results();

			self._common_asserts(result[0], 20);

			self.assertLessEqual(len(result[0][0]), 1000, msg=f"Remove mod resulted in more rolls than original, should be less than {num_dice}, is incorrect value of {len(result[0][0])}");

			self.assertFalse(any([r == i for r in result[0][0]]), msg=f"Remove mod of {{{i}}} resulted in roll of {i}");


	def test_remove_cond(self):
		num_dice: int = 1000;

		for i in range_incl(2, 20):
			result: list[tuple[list[int], int]] = DiceSet(1000, 20, remove=f"<{i}").get_results();

			self._common_asserts(result[0], 20);

			self.assertLessEqual(len(result[0][0]), 1000, msg=f"Remove mod resulted in more rolls than original, should be less than {num_dice}, is incorrect value of {len(result[0][0])}");

			self.assertFalse(any([r < i for r in result[0][0]]), msg=f"Remove mod of {{{i}}} resulted in roll of <{i}");

		for i in range_incl(2, 19):
			result: list[tuple[list[int], int]] = DiceSet(1000, 20, remove=f">={i}").get_results();

			self._common_asserts(result[0], 20);

			self.assertLessEqual(len(result[0][0]), 1000, msg=f"Remove mod resulted in more rolls than original, should be less than {num_dice}, is incorrect value of {len(result[0][0])}");

			self.assertFalse(any([r >= i for r in result[0][0]]), msg=f"Remove mod of {{{i}}} resulted in roll of >={i}");


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


def main():
	parser = argparse.ArgumentParser(description="A utility packed dice roller and calculator");
	parser.add_argument("-u", "--unit", action="store_true", default=False, help="Run all unit tests");
	parser.add_argument("-d", "--debug", action="store_true", default=False, help="Run in dicemode debug mode");
	parser.add_argument("-l", "--load", nargs="*", help="Load an additional dicemode file");
	options: Namespace = parser.parse_args();

	if options.unit:
		unittest.main(argv=[sys.argv[0], ]);

	if not os.path.isfile(DefaultDicemodeFile):
		with open(DefaultDicemodeFile, "w") as outfile:
			for mode in DefaultDicemodes:
				outfile.write(DefaultDicemodes[mode].lstrip());

	rdp: Rdp.Rdp = Rdp.Rdp();
	dicemodes: dict[str, Dicemode] = {};
	active_dicemode: str = "";
	done: bool = False;

	with open(DefaultDicemodeFile, "r") as mode_file:
		cur_mode: str = "";
		mode_actions: list[str] = [];

		for line in mode_file:
			# Strip off newline and any trailing spaces
			line = line.rstrip();

			if line.startswith("dicemode("):
				if cur_mode:
					dicemodes[cur_mode] = Dicemode(cur_mode, mode_actions);
					mode_actions.clear();

				cur_mode = line.removeprefix("dicemode").strip("():");
				# mode_actions.append(line);
			elif line.strip() == "":
				dicemodes[cur_mode] = Dicemode(cur_mode, mode_actions);
				cur_mode = "";
				mode_actions.clear();
			else:
				# Remove single tab from actions to align outer actions with no indent level
				mode_actions.append(line.replace("    ", "\t").removeprefix("\t"));

		if cur_mode:
			dicemodes[cur_mode] = Dicemode(cur_mode, mode_actions);

	while not done:
		prompt: str = input("Enter commands, dice, or math: ").strip();

		if prompt == "exit" or prompt == "stop" or prompt == "quit":
			done = True;
		elif prompt.startswith("dicemode "):
			# Process dicemode
			dicemode = prompt.removeprefix("dicemode").strip();

			if dicemode in dicemodes:
				active_dicemode = dicemode;
		elif any([prompt.startswith(key) for key in Commands]):
			# Process commands
			args: list[str] = prompt.split(" ");

			if len(args) == 1:
				Commands[args[0]]();
			else:
				Commands[args[0]](*args[1:]);
		elif DiceSet.is_dice(prompt):
			# Process dice
			if active_dicemode:
				dicemodes[active_dicemode].run(prompt, options.debug);
			else:
				print(DiceSet.from_str(prompt));
		else:
			# Process math
			try:
				print(rdp.eval_exp(prompt));
			except (SyntaxError, ZeroDivisionError) as e:
				print(e);


if __name__ == "__main__":
	main();