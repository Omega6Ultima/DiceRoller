import argparse
import platform
import sys
import re;
from argparse import Namespace

import winsound, threading, time, random, math, os;

import RollerUtils
from Multiple_Dice_roller_defaults import DEFAULT_DICEMODES;
from Multiple_Dice_roller_defaults import DEFAULT_TIMER_FILE;
from Rdp import Rdp;
import Rdp;
from RollerUtils import *;
from typing import Callable;
import playsound3;

# DEFAULT_TIMER_SOUND = "alarmclock";
# TIMER_SOUND = "alarmclock";

# LESS = 0;
# GREATER = 1;
# LESSEQUAL = 2;
# GREATEREQUAL = 3;
# SIGNS = ("<", ">", "<=", ">=");
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
		self.actions: list[str] = actions;
		self.action_index: int = 0;
		self.done: bool = False;
		self.loop_entry: None | int = None;
		self.loop_end: None | int = None;


	def run(self, dice: str, debug: bool = False) -> None:
		self.done = False;
		self.loop_entry = None;
		self.loop_end = None;
		# TODO change pre-defined vars to have __
		mode_vars: dict[str, any] = {
			"True": True,
			"False": False,
			"dice": DiceSet.from_str(dice),
			"rolls": [],
			"rolls_adj": 0,
		};

		while not self.done:
			self._execute_action(self.actions[self.action_index], mode_vars, debug);

			self.action_index += 1;

			if self.action_index > len(self.actions):
				if self.loop_entry is not None:
					self.action_index = self.loop_entry;
				else:
					self.done = True;

		if debug:
			print(mode_vars);


	@staticmethod
	def _collect_args(text: str) -> list[str]:
		action: str = text[:text.find("(")];
		arg_str: str = text.removeprefix(action).removesuffix(")");
		arg_list: list[str] = [a.strip() for a in arg_str.split(",")];

		arg_index: int = 0;

		while arg_index < len(arg_list):
			if "(" in arg_list[arg_index] and not ")" in arg_list[arg_index]:
				arg_list[arg_index] += f", {arg_list[arg_index + 1]}";
			else:
				arg_index += 1;

		return arg_list;


	def _execute_action(self, action: str, mode_vars: dict[str, any], debug: bool = False) -> None:
		if self.loop_entry is not None:
			if self.action_index > self.loop_end:
				self.action_index = self.loop_entry;

				action = self.actions[self.action_index];

		clean_action: str = action.lstrip();

		if debug:
			print(f"Executing action #{self.action_index} '{clean_action}'");

		if clean_action.startswith("store("):
			args: list[str] = self._collect_args(clean_action);

			val: float = float(args[0]);
			var: str = args[1];

			if debug:
				print(f"  Storing {val} into '{var}'");

			mode_vars[var] = val;
		elif clean_action.startswith("check("):
			args: list[str] = self._collect_args(clean_action);

			die_sides: int = int(args[0].removeprefix("d"));

			if debug:
				print(f"  Checking dice are d{die_sides}'s");

			if not mode_vars["dice"].verify_dice(die_sides):
				self.done = True;

				print(f"Using dicemode {self.name} with non-d{die_sides}, dice passed are {mode_vars['dice'].dice_sides}");
		elif clean_action.startswith("roll("):
			args: list[str] = self._collect_args(clean_action);
			result: list[tuple[list[int], int]] = [];

			dice: str = args[0];

			try:
				if dice == "dice":
					if debug:
						print(f"  Rolling {mode_vars['dice'].display()}");

					result.extend(mode_vars["dice"].get_result());
				else:
					if debug:
						print(f"  Rolling {dice}");

					result.extend(DiceSet.from_str(dice).get_results());
			except DiceError as e:
				print(e);

				self.done = True;

				return;

			for i in range(len(result)):
				mode_vars["rolls"].extend(result[i][0]);
				mode_vars["roll_adj"] += result[i][1];
		elif clean_action.startswith("rollinto("):
			args: list[str] = self._collect_args(clean_action);
			result: int = 0;

			dice: str = args[0];
			var: str = args[1];

			try:
				if debug:
					print(f"  Rolling {dice} and storing into {var}");

				result += int(DiceSet.from_str(dice));
			except DiceError as e:
				print(e);

				self.done = True;

				return;

			mode_vars[var] = result;
		elif clean_action.startswith("total("):
			args: list[str] = self._collect_args(clean_action);

			var: str = args[0];

			if debug:
				print(f"  Totaling dice rolls and storing into {var}");

			mode_vars[var] = sum(mode_vars["rolls"]) + mode_vars["rolls_adj"];
		elif clean_action.startswith("count("):
			args: list[str] = self._collect_args(clean_action);

			comp: str = args[0];
			val: float = float(args[1]);
			var: str = args[2];

			if comp not in Comparisons:
				print(f"'{comp}' is not a valid comparison");

				self.done = True;

				return;

			if debug:
				print(f"  Counting rolls that match {comp} {val} and storing into {var}");

			count: int = 0;

			for roll in mode_vars["rolls"]:
				if Comparisons[comp](roll, val):
					count += 1;

			if debug:
				print(f"  Matching rolls: {count}, Non-matching rolls: {len(mode_vars["rolls"]) - count}");

			mode_vars[var] = count;
		elif clean_action.startswith("calc("):
			args: list[str] = self._collect_args(clean_action);

			var1: str = args[0];
			op: str = args[1];
			var2: str = args[2];

			if var1 not in mode_vars:
				print(f"'{var1}' has not been set before use");

				self.done = True;

				return;

			if op not in Calculations:
				print(f"'{op}' is not a valid calculation");

				self.done = True;

				return;

			if var2 not in mode_vars:
				print(f"'{var2}' has not been set before use");

				self.done = True;

				return;

			if debug:
				print(f"  Calculating '{var1} {op} {var2}' and storing into '{var1}'");

			mode_vars[var1] = Calculations[op](mode_vars[var1], mode_vars[var2]);
		elif clean_action.startswith("if("):
			args: list[str] = self._collect_args(clean_action);

			var1: str = args[0];
			comp: str = args[1];
			var2: str = args[2];
			sub_action = args[3];

			if var1 not in mode_vars:
				print(f"'{var1}' has not been set before use");

				self.done = True;

				return;

			if comp not in Comparisons:
				print(f"'{comp}' is not a valid calculation");

				self.done = True;

				return;

			if var2 not in mode_vars:
				print(f"'{var2}' has not been set before use");

				self.done = True;

				return;

			if debug:
				print(f"  If '{var1} {comp} {var2}' is True, then execute '{sub_action}'");
				print(f"  {mode_vars[var1]} {comp} {mode_vars[var2]} = {Comparisons[comp](mode_vars[var1], mode_vars[var2])}");

			if Comparisons[comp](mode_vars[var1], mode_vars[var2]):
				self._execute_action(sub_action, mode_vars, debug);
		elif clean_action.startswith("foreach("):
			args: list[str] = self._collect_args(clean_action);

			var: str = args[0];
			sub_action: str = args[1];

			if var not in mode_vars:
				print(f"'{var}' has not been set before use");

				self.done = True;

				return;

			if debug:
				print(f"  Looping {mode_vars[var]} times and running '{sub_action}'");

			for _ in range(mode_vars[var]):
				self._execute_action(sub_action, mode_vars, debug);
		elif clean_action.startswith("while("):
			args: list[str] = self._collect_args(clean_action);

			var1: str = args[0];
			comp: str = args[1];
			var2: str = args[2];

			if var1 not in mode_vars:
				print(f"'{var1}' has not been set before use");

				self.done = True;

				return;

			if comp not in Comparisons:
				print(f"'{comp}' is not a valid calculation");

				self.done = True;

				return;

			if var2 not in mode_vars:
				print(f"'{var2}' has not been set before use");

				self.done = True;

				return;

			# Calculate loop_end
			loop_end: int = self.action_index + 1;
			indent_level: str = self.actions[loop_end].count("\t") * "\t";

			while self.actions[loop_end].startswith(indent_level):
				loop_end += 1;

			if debug:
				print(f"  Looping while '{var1} {comp} {var2}' from action #{self.action_index} to {loop_end}");
				print(f"  {mode_vars[var1]} {comp} {mode_vars[var2]} = {Comparisons[comp](mode_vars[var1], mode_vars[var2])}");

			if Comparisons[comp](mode_vars[var1], mode_vars[var2]):
				self.loop_entry = self.action_index;
				self.loop_end = loop_end;
		elif clean_action.startswith("break"):
			if self.loop_entry is None:
				print("Break action outside of loop");

			if debug:
				print(f"  Breaking out from loop({self.loop_entry}-{self.loop_end})");

			self.action_index = self.loop_end + 1;
			self.loop_entry = None;
			self.loop_end = None;
		elif clean_action.startswith("print("):
			args: list[str] = self._collect_args(clean_action);

			var: str = args[0];

			if var not in mode_vars:
				print(f"'{var}' has not been set before use");

				self.done = True;

				return;

			if debug:
				print(f"  Printing value of '{var}'");

			print(f"{var} = {mode_vars[var]}");
		# elif clean_action.startswith("store("):
		#     args: list[str] = self._collect_args(clean_action);

# def checkdice(dice, correct_dice):
# #    if re.search(r"^\d+"+correct_dice+"\D+.*$", dice, flags=re.DOTALL):
# #        return True;
# #   else:
# #        return False;
#     if correct_dice in dice:
#         ind = dice.find(correct_dice)+len(correct_dice);
#         if ind >= len(dice):
#             return True;
#         char = dice[ind];
#         if not is_digit(char):
#             return True;
#     else:
#         return False;
#
# def rollandprint(d, printf=0, listvals=0):
#     dice = "";
#     diceRolls = [];
#     total = 0;
#     addon = 0;      #can be any integer
#     limit = None;   #low
#     reroll = None;  #any interger or [sign, integer]
#     count = None;   #[sign, number, total]
#     org_d = d;
#
#     #parsing the string to check for valid input
#     #for c in d[:d.find("[")]:
#     for c in d:
#         if c.isalpha() and c != "d" and c != "[" and c != "]" \
#                 and c != "{" and c != "}" and c != "<" and c != ">" \
#                 and c != "=" and c != "+" and c != "-" and not (d.find("[") < d.find(c) < d.find("]")):
# ##            print "Invalid Format For Parsing";
# ##            return;
#             raise DiceError("bad Dice format");
#
#     #check to see if the string is formatted for counting rolls
#     if SIGNS[LESSEQUAL] in d and not "[" in d and not "]" in d and not "{" in d and not "}" in d:
#         count = [LESSEQUAL, int(d[d.find(SIGNS[LESSEQUAL])+2:]), 0];
#         d = d[:d.find(SIGNS[LESSEQUAL])];
#     elif SIGNS[GREATEREQUAL] in d and not "[" in d and not "]" in d and not "{" in d and not "}" in d:
#         count = [GREATEREQUAL, int(d[d.find(SIGNS[GREATEREQUAL])+2:]), 0];
#         d = d[:d.find(SIGNS[GREATEREQUAL])];
#     elif SIGNS[LESS] in d and not "[" in d and not "]" in d and not "{" in d and not "}" in d:
#         count = [LESS, int(d[d.find(SIGNS[LESS])+1:]), 0];
#         d = d[:d.find(SIGNS[LESS])];
#     elif SIGNS[GREATER] in d and not "[" in d and not "]" in d and not "{" in d and not "}" in d:
#         count = [GREATER, int(d[d.find(SIGNS[GREATER])+1:]), 0];
#         d = d[:d.find(SIGNS[GREATER])];
#
#     #check if the string needs to repeat a set of dice
#     if "*" in d:
#         #print "repeating";
#         repeat = int(d[:d.find("*")]);
#
#         for t in range(repeat):
#             diceRolls.append(rollandprint(d[d.find("*")+1:len(d)], printf, listvals));
#         return diceRolls;
#
#     #check to see if there are any limits to the dice rolls
#     if "[" in d and "]" in d:
#         if is_digit(d[d.find("[") + 1:d.find("]")]):
#             limit = int(d[d.find("[")+1:d.find("]")]);
#         elif "low" in d[d.find("[")+1:d.find("]")]:
#             limit = "low";
#         else:
#             if SIGNS[LESSEQUAL] in d:
#                 limit = [LESSEQUAL, int(d[d.find(SIGNS[LESSEQUAL])+2:d.find("]")])];
#             elif SIGNS[GREATEREQUAL] in d:
#                 limit = [GREATEREQUAL, int(d[d.find(SIGNS[GREATEREQUAL])+2:d.find("]")])];
#             elif SIGNS[LESS] in d:
#                 limit = [LESS, int(d[d.find(SIGNS[LESS])+1:d.find("]")])];
#             elif SIGNS[GREATER] in d:
#                 limit = [GREATER, int(d[d.find(SIGNS[GREATER])+1:d.find("]")])];
#         d = d[:d.find("[")];
#
#     #check for any rerolls
#     elif "{" in d and "}" in d:
#         if is_digit(d[d.find("{") + 1:d.find("}")]):
#             reroll = int(d[d.find("{")+1:d.find("}")]);
#         else:
#             if SIGNS[LESSEQUAL] in d:
#                 reroll = [LESSEQUAL, int(d[d.find(SIGNS[LESSEQUAL])+2:d.find("}")])];
#             elif SIGNS[GREATEREQUAL] in d:
#                 reroll = [GREATEREQUAL, int(d[d.find(SIGNS[GREATEREQUAL])+2:d.find("}")])];
#             elif SIGNS[LESS] in d:
#                 reroll = [LESS, int(d[d.find(SIGNS[LESS])+1:d.find("}")])];
#             elif SIGNS[GREATER] in d:
#                 reroll = [GREATER, int(d[d.find(SIGNS[GREATER])+1:d.find("}")])];
#         d = d[:d.find("{")];
#
#     #check to see if there are any modifiers to the dice roll
#     if "+" in d:
#         addon += int(d[d.find("+")+1: len(d)]);
#         maxnum = int(d[d.find("d")+1: d.find("+")]);
#     elif "-" in d:
#         addon += -int(d[d.find("-")+1: len(d)]);
#         maxnum = int(d[d.find("d")+1: d.find("-")]);
#     else:
#         addon = 0;
#         maxnum = int(d[d.find("d")+1: len(d)]);
#
#     #handle fractional dice rolls
#     org_times = float(d[0:d.find("d")]);
#
#     times_frac = round(math.modf(org_times)[0], len(d[d.find(".")+1:d.find("d")]));
#     if times_frac:
#         if count != None:
#             roll = rollandprint("1d"+str(int(maxnum*times_frac))+"+"+str(addon)+SIGNS[count[0]]+str(count[1]), 0, 0);
#         elif isinstance(limit, int):
#             roll = rollandprint("1d"+str(int(maxnum*times_frac))+"+"+str(addon)+"["+str(limit)+"]", 0, 0);
#         elif isinstance(limit, list):
#             roll = rollandprint("1d"+str(int(maxnum*times_frac))+"+"+str(addon)+"["+SIGNS[limit[0]]+str(limit[1])+"]", 0, 0);
#         elif isinstance(limit, str) and limit == "low":
#             roll = rollandprint("1d"+str(int(maxnum*times_frac))+"+"+str(addon)+"["+limit+"]", 0, 0);
#         elif isinstance(reroll, int):
#             roll = rollandprint("1d"+str(int(maxnum*times_frac))+"+"+str(addon)+"{"+reroll+"+"+"}", 0, 0);
#         elif isinstance(reroll, list):
#             roll = rollandprint("1d"+str(int(maxnum*times_frac))+"+"+str(addon)+"{"+SIGNS[reroll[0]]+str(reroll[1])+"}", 0, 0);
#         else:
#             roll = rollandprint("1d"+str(int(maxnum*times_frac))+"+"+str(addon), 0, 0);
#         diceRolls.append(roll);
#         total += roll;
#
#     #check to see how many dice to rolls
#     times = int(org_times);
#
#     #roll the dice
#     for r in range(times):
#         roll = random.randint(1, maxnum);
#         if reroll != None:
#             if isinstance(reroll, int) and roll == reroll:
#                 roll = rollandprint("1d"+str(maxnum)+"{"+str(reroll)+"}", 0, 0);
#             elif isinstance(reroll, list):
#                 if reroll[0] == LESS:
#                     if roll < reroll[1]:
#                         roll = rollandprint("1d"+str(maxnum)+"{"+SIGNS[LESS]+str(reroll[1])+"}", 0, 0);
#                 elif reroll[0] == GREATER:
#                     if roll > reroll[1]:
#                         roll = rollandprint("1d"+str(maxnum)+"{"+SIGNS[GREATER]+str(reroll[1])+"}", 0, 0);
#                 elif reroll[0] == LESSEQUAL:
#                     if roll <= reroll[1]:
#                         roll = rollandprint("1d"+str(maxnum)+"{"+SIGNS[LESSEQUAL]+str(reroll[1])+"}", 0, 0);
#                 elif reroll[0] == GREATEREQUAL:
#                     if roll >= reroll[1]:
#                         roll = rollandprint("1d"+str(maxnum)+"{"+SIGNS[GREATEREQUAL]+str(reroll[1])+"}", 0, 0);
#         total += roll;
#         diceRolls.append(roll);
#
#     #if the limit was the lowest roll, take it out
#     removeDice = [];
#     if isinstance(limit, str) and limit == "low":
#         lowest = maxnum;
#         for n in diceRolls:
#             if n < lowest:
#                 lowest = n;
#         diceRolls.remove(lowest);
#         total -= lowest;
#         times -= 1;
#         org_times -= 1;
#     elif isinstance(limit, int):
#         for n in diceRolls:
#             if n == limit:
#                 removeDice.append(n);
# ##                diceRolls.remove(n);
#                 total -= n;
#                 times -= 1;
#                 org_times -= 1;
#     elif isinstance(limit, list):
#         for n in diceRolls:
#             if limit[0] == LESS:
#                 if n < limit[1]:
#                     removeDice.append(n);
# ##                    diceRolls.remove(n);
#                     total -= n;
#                     times -= 1;
#                     org_times -= 1;
#             elif limit[0] == GREATER:
#                 if n > limit[1]:
#                     removeDice.append(n);
# ##                    diceRolls.remove(n);
#                     total -= n;
#                     times -= 1;
#                     org_times -= 1;
#             elif limit[0] == LESSEQUAL:
#                 if n <= limit[1]:
#                     removeDice.append(n);
# ##                    diceRolls.remove(n);
#                     total -= n;
#                     times -= 1;
#                     org_times -= 1;
#             elif limit[0] == GREATEREQUAL:
#                 if n >= limit[1]:
#                     removeDice.append(n);
# ##                    diceRolls.remove(n);
#                     total -= n;
#                     times -= 1;
#                     org_times -= 1;
#
#     if removeDice:
#         for n in removeDice:
#             diceRolls.remove(n);
#
#     #if the function was called to print
#     if printf:
#         if count == None:
#             if times_frac:
#
#                 if addon:
#                     print(str(d)+" ("+str(times)+d[d.find("d"):]+", 1d"+str(int(maxnum*times_frac))+"+"+str(addon) + "):\t\tmax possible: "+str(int(org_times*maxnum)+addon));
#                 else:
#                     print(str(d)+" ("+str(times)+d[d.find("d"):]+", 1d"+str(int(maxnum*times_frac))+"):\t\tmax possible: "+str(int(org_times*maxnum)+addon));
#             else:
#                 if limit != None:
#                     print(str(org_times)+"d"+str(maxnum)+":\t\tmax possible: "+str(int(org_times*maxnum)+addon));
#                 else:
#                     print(str(d)+":\t\tmax possible:"+str(int(org_times*maxnum)+addon));
#             print(diceRolls);
#             print(str(total + addon)+"\n");
#         else:
#             if count[0] == LESS:
#                 for r in diceRolls:
#                     if r < count[1]:
#                         count[2] += 1;
#             elif count[0] == GREATER:
#                 for r in diceRolls:
#                     if r > count[1]:
#                         count[2] += 1;
#             elif count[0] == LESSEQUAL:
#                 for r in diceRolls:
#                     if r <= count[1]:
#                         count[2] += 1;
#             elif count[0] == GREATEREQUAL:
#                 for r in diceRolls:
#                     if r >= count[1]:
#                         count[2] += 1;
#             if times_frac:
#                 if addon:
#                     print(str(d)+" ("+str(times)+d[d.find("d"):]+", 1d"+str(int(maxnum*times_frac))+"+"+str(addon)+")");
#                 else:
#                     print(str(d)+" ("+str(times)+d[d.find("d"):]+", 1d"+str(int(maxnum*times_frac))+")");
#             else:
#                 print(str(org_d));
#             print(diceRolls);
#             print(count[2], '\n');
#     elif listvals:
#         return diceRolls;
#     else:
#         return total+addon;
#
# def calculateandprint(d, printf=0):
# ##    if d.isalpha(): #***not sufficient enough, do full check
# ##        print "Invalid Format For Parsing";
# ##        return;
#
#     if "." in d:
#         temp = "";
#         strs = d.split('.');
#         if len(strs) > 1:
#             for c in range(len(strs)):
#                 temp += strs[c];
#                 if len(strs[c]) < 1:
#                     temp += "0.";
#                 elif c == len(strs)-1:
#                     continue;
#                 elif (len(strs[c]) > 0 and strs[c][-1].isdigit()):
#                     temp += ".";
#                 elif (len(strs[c]) > 0 and not strs[c][-1].isdigit()):
#                     temp += "0.";
#                 else:
#                     temp += ".";
#             d = temp;
#     elif "(" in d and ")" in d:
#         temp = "";
#         strs = d.split('(');
#         if len(strs) > 1:
#             for c in range(len(strs)):
#                 temp += strs[c];
#                 if c == len(strs)-1:
#                     continue;
#                 elif len(temp) > 0 and temp[-1].isdigit():
#                     temp += "*(";
#                 else:
#                     temp += "(";
#             d = temp;
#
#         temp = "";
#         strs = d.split(')');
#         if len(strs) > 1:
#             for c in range(len(strs)):
#                 temp += strs[c];
#                 if c == len(strs)-1:
#                     continue;
#                 elif c < len(strs)-1 and len(strs[c+1]) > 0 and strs[c+1][0].isdigit():
#                     temp += ")*";
#                 else:
#                     temp += ")";
#             d = temp;
#
#     result = recursivedescentparser.eval_exp(d);
#     if printf:
#         if result != None:
#             print(str(d)+" = "+str(result));
#         else:
#             if "=" in d:
#                 print(str(d)+" = "+str(recursivedescentparser.eval_exp(d[d.find("=")+1:])));
#             else:
#                 print(d);
#     else:
#         return result;
#
# def enchant(casterlevel):
#     nums1 = rollandprint("20d20+"+str(casterlevel), 0, 1);
#     nums2 = rollandprint("20d20+"+str(casterlevel), 0, 1);
#     passes1 = 0;
#     passes2 = 0;
#
#     for i in range(len(nums1)):
#         if nums1[i] >= 10:
#             passes1 += 1;
#         if nums2[i] >= 10:
#             passes2 += 1;
#     passes = (passes1 + passes2)/2;
#
#     if passes < 10:
#         print("enchant FAILED");
#         return;
#
#     useroll = rollandprint("1d8", 0, 0);
#     for i in range(passes-10):
#         if(useroll < 3):
#             break;
#         useroll = rollandprint("1d8", 0, 0);
#
#     print("based on the spell and usage limit: "+str(useroll)+"and the average passes of: "+str(passes)+"...");
# ##    print "and the average passes of: "+str(passes)+"...";
#     string = raw_input("pick an appriate dice combo ");
#     result = (rollandprint(string, 0, 0));
#     print("The results of the enchant are: ");
#     print("20d20: "+str(passes1)+"\n20d20: "+str(passes2)+"\t"+str(passes));
#     print("usage limits: "+str(useroll));
#     print("dice combo: "+str(string)+": "+str(result)+"+"+str(passes-10));
#
# #dice roll pre and post processing
# def none(d):
#     rollandprint(d, 1, 0);
#
# #***add the capability that when you roll a certain number, it rolls another dice of the same type, kinda have with tenagain dicemodes
# #***adjust the printed output when using removal syntax, 10d6[<=5]
# #***count coin totals
# #main program
# if __name__ == "__main__":
#     #This code is used to implement different dicemodes that can be read in, even when this is compiled into an exe
#     #The source will be a python script but will not be executed directly
#     #read in the MDR_dicemodes.py
#     infile = openOrCreate("Multiple_Dice_roller_dicemodes.py", 'r', DEFAULT_DICEMODES, 1);
#     if infile:
#         temp = "".join(infile.readlines());
#         infile.close();
#     else:
#         temp = DEFAULT_DICEMODES;
#     #exec the text from MDR_dicemodes.py, defining all the functions from that module in this module
#     exec(temp); #***optimize/safety
#     #import the module to get the function names from it
#     import Multiple_Dice_roller_dicemodes;
#     flist = dir(Multiple_Dice_roller_dicemodes);
#     del Multiple_Dice_roller_dicemodes;
#     dicemodes = {"none":none,};
#     for func in flist:
#         if not func.startswith("__"):
#             dicemodes[func] = globals()[func];  #add the names of the functions to the dicemode list
#     #set the default dicemode
#     dicemode = ("none", none);
#     locked = False;
#     passw = None;
#     dice = "";
#     Timerlist = [];
#     recursivedescentparser = Rdp();
#     print("(If you dont know what your doing type help)");
#
#     while True:
#         dice = input("Enter the dice to roll: ").lower();
#         if locked and dice == passw:
#             locked = False;
#             print("UNLOCKED");
#             continue;
#         elif locked:
#             print("LOCKED");
#             continue;
#         elif dice == "exit" or dice == "quit" or dice=="stop":
#             break;
#         elif dice == "cls":
#             os.system("cls");
#             continue;
#         elif dice == "test":
#             rollandprint("13d13", 1, 0);
#             rollandprint("1d4+5", 0, 1);
#             rollandprint("1d20-4");
#             rollandprint("4*4d6");
#             rollandprint("10d2{1}");
#             rollandprint("4d6[low]");
#             rollandprint("5d6[2]");
#             rollandprint("10d6[<=5]");
#             rollandprint("12d12>=6", 1, 0);
#             rollandprint("12d20{>=10}", 1, 0);
#             rollandprint("12d10{<3}", 1, 0);
#             rollandprint("5.5d12", 1);
#             calculateandprint("10+14", 1);
#             calculateandprint("54-19", 1);
#             calculateandprint("4*8", 1);
#             calculateandprint("27/9", 1);
#             calculateandprint("50%4", 1);
#             calculateandprint("3*(2+7)", 1);
#             calculateandprint("2^3", 1);
#             calculateandprint("-43-17", 1);
#             calculateandprint(".75+.5", 1);
#             calculateandprint("(2*3.14)-3.14", 1);
#             calculateandprint("75*(1+.5)/(1+.75)", 1);
#             calculateandprint("7(1+1)", 1);
#             calculateandprint("(2+4)6", 1);
#             calculateandprint("a=32", 1);
#             calculateandprint("a + 2", 1);
#             calculateandprint("b = a ^ 2", 1);
#             checkdice("1d6", "d6");
#             checkdice("14d10+8", "d10");
#             os.system("cls");
#             print("Tests completed");
#             continue;
#         elif dice == "help":
#             os.system("cls");
#             def tab(n):
#                 return ("\t"*n)+'-';
#             helpmsg = \
# """HELP:
#     commands:
#     exit, quit, stop(tab3)exit the Dice Roller
#     cls(tab7)clear the output
#     test(tab6)test the roller and calculator
#     timer:6(tab6)set a timer for 6 seconds
#     cmd:tsound(tab5)print the current timer sound
#     cmd:tsound:filename(tab3)select a wav sound for all new timers
#     cmd:tsound:default(tab3)select the default sound for timers
#     cmd:tstop(tab5)stop all currently playing timer sounds
#     cmd:lock:pass(tab4)lock the program with password: pass
#     cmd:dicemode(tab4)print the current dicemode
#     cmd:dicemode?(tab4)print all available dicemodes in MDR_dicemodes.py
#     cmd:dicemode:default(tab2)reset the dicemode to normal
#     cmd:dicemode:ndicemode(tab2)set the current dicemode to be ndicemode
#     1d10(tab6)roll a dice normallly
#     1d10+3(tab6)roll a dice and add to it
#     1d10-4(tab6)roll a dice and subtract from it
#     1d6, 1d8, 1d10(tab4)roll different dice at the same time
#     2*2d6(tab6)same as 2d6, 2d6
#     2*2d6+4(tab6)same as 2d6+4, 2d6+4
#     1d10{4}(tab6)roll a dice and reroll any 4s
#     1d20{<=5}(tab5)roll a dice and reroll any number that fits the conditional
#     4d6[low](tab5)take out the lowest roll
#     5d6[2](tab6)take out any 2s
#     10d6[<=5](tab5)take out any number that fits the conditional
#     2.5d6, 3.78d10(tab4)roll a dice with a fractional part
#     10+14(tab6)add numbers
#     54-19(tab6)subtract numbers
#     4*8(tab7)multiply numbers
#     27/9(tab6)divide numbers
#     2^3(tab7)take a number to a power
#     a = 23(tab6)store 23 to variable 'a'
#     a * 3(tab6)use 'a' in a calculation
#     PI = 3.141592654(tab3)store pi into PI""";
#             print(helpmsg.replace("(tab1)", tab(1)).replace("(tab2)", tab(2)).replace("(tab3)", tab(3)).replace("(tab4)", tab(4)).replace("(tab5)", tab(5)).replace("(tab6)", tab(6)).replace("(tab7)", tab(7)));
#
#             continue;
#
#         dicelist = dice.split(',');
#
#         for d in dicelist:
#             d = d.strip();
#             if d.startswith("enchant:"):
#                 enchant(int(d[8:]));
#             elif d == "abilities":
#                 while True:
#                     total = 0;
#                     nums = rollandprint("7*4d6[low]", 0, 0);
#                     lowest = 18;
#                     for n in nums:
#                         if n < lowest:
#                             lowest = n;
#                         total += n;
#                     nums.remove(lowest);
#                     total -= lowest;
#                     if total/6 < 10:
#                         continue;
#                     print(nums);
#                     break;
#             elif d.startswith("timer:"):
#                 temptimer = SoundTimer(int(d[6:]), TIMER_SOUND);
#                 Timerlist.append(temptimer);
#             elif d.startswith("coin:"):
#                 dice = d[5:]+"d2";
#                 rolls = rollandprint(dice, 0, 1);
#                 print(d[5:]+" coins:");
#                 heads = 0;
#                 tails = 0;
#                 for r in rolls:
#                     if r == 1:
#                         heads += 1;
#                     else:
#                         tails += 1;
#                 print(heads, " heads and");
#                 print(tails, "tails ");
#             elif d.startswith("cmd:"):  #list of commands
#                 cmd = d[4:];
#                 if cmd == "tsound":
#                     print(TIMER_SOUND);
#                 elif cmd.startswith("tsound:"):
#                     snd = cmd[7:];
#                     if snd == "default":
#                         TIMER_SOUND = "alarmclock";
#                     else:
#                         tempfile = open(snd);
#                         if not tempfile:
#                             print(snd+" is not a valid file. Please check the name and try again.");
#                         else:
#                             TIMER_SOUND = snd;
#                         tempfile.close();
# ##                elif cmd.startswith("tsound:"):
# ##                    snd = cmd[7:];
# ##                    if snd == "default":
# ##                        snd = DEFAULT_TIMER_SOUND
# ##                    tmpfile = open(snd);
# ##                    if not (tmpfile):
# ##                        print snd+" is not a valid file. Please check the name and try again.";
# ##                    else:
# ##                        TIMER_SOUND = snd;
# ##                    tmpfile.close();
#                 elif cmd == "tstop":
#                     winsound.PlaySound(None, winsound.SND_NOWAIT | winsound.SND_PURGE);
#                 elif cmd.startswith("lock:"):
#                     passw = cmd[5:];
#                     locked = True;
#                     print("LOCKED");
#                 elif cmd == "dicemode":
#                     print("dicemode is: "+str(dicemode));
#                 elif cmd == "dicemode?":
#                     for dm in dicemodes:
#                         print(dm);
#                 elif cmd.startswith("dicemode:"):
#                     tempmode = cmd[9:];
#                     if tempmode in dicemodes:
#                         dicemode = (tempmode, dicemodes[tempmode]);
#                     elif tempmode == "default":
#                         dicemode = ("none", none);
#                     else:
#                         dicemode = ("none", none);
#                         print(tempmode+" is not a valid mode. Resetting to none.");
#             elif "d" in d:
#                 try:
#                     dicemode[1](d);
#                 except DiceError:
#                     try:
#                         calculateandprint(d, 1);
#                     except:
#                         print("Malformed expression");
#             else:
#                 calculateandprint(d, 1);


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
	"clear": lambda: os.system("cls") if "win" in platform.system() else os.system("clear"),
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
		self.assertEqual(dice.add_mod, None);
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


def main():
	parser = argparse.ArgumentParser(description="A utility packed dice roller and calculator");
	parser.add_argument("-u", "--unit", action="store_true", help="Run all unit tests");
	parser.add_argument("-d", "--debug", action="store_true", help="Run in dicemode debug mode");
	parser.add_argument("-l", "--load", nargs="*", help="Load an additional dicemode file");
	options: Namespace = parser.parse_args();

	if options.unit:
		unittest.main(argv=[sys.argv[0], ]);

	if not os.path.isfile(DefaultDicemodeFile):
		# TODO do this last
		pass;

	rdp: Rdp.Rdp = Rdp.Rdp();
	dicemodes: dict[str, Dicemode] = {};
	active_dicemode: str = "";
	done: bool = False;

	with open(DefaultDicemodeFile, "r") as mode_file:
		cur_mode: str = "";
		mode_actions: list[str] = [];

		for line in mode_file:
			line = line.rstrip();

			if line.startswith("dicemode("):
				if cur_mode:
					dicemodes[cur_mode] = Dicemode(cur_mode, mode_actions);
					mode_actions.clear();

				cur_mode = line.removeprefix("dicemode").strip("():");
				mode_actions.append(line);
			elif line.strip() == "":
				dicemodes[cur_mode] = Dicemode(cur_mode, mode_actions);
				cur_mode = "";
				mode_actions.clear();
			else:
				mode_actions.append(line);

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