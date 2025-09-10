import random;
import re;
from typing import Callable;

import RollerUtils;

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


class DiceError(Exception):
	def __init__(self, text: str):
		Exception.__init__(self, text);
		self.msg = text;


	def __str__(self) -> str:
		return f"DiceError {self.msg}";


class DiceSet:
	ValidComparisons: list[str] = ["<=", ">=", "<", ">"];
	DicePattern: re.Pattern = re.compile(r"""(\d+\*)?            		# optional multiplier
											\d+(?:\.\d+)?               		# number of dice
											[dD]
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
			elif reroll == "low":
				self.reroll_mod = ("low", 0);
			elif reroll == "high":
				self.reroll_mod = ("high", 0);
			else:
				raise DiceError(f"Invalid reroll modifier '{reroll}'");

			if self.reroll_mod[0] in Comparisons:
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
			elif remove == "low":
				self.remove_mod = ("low", 0);
			elif remove == "high":
				self.remove_mod = ("high", 0);
			else:
				raise DiceError(f"Invalid remove modifier '{remove}'");

			if self.remove_mod[0] in Comparisons:
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
		text = text.lower();

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
		# Remove any spaces first to simply regex
		text = text.replace(" ", "");


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
			if self.reroll_mod[0] == "low":
				min_val: int = min(self.result);

				self.result[self.result.index(min_val)] = self.roll_single();
			elif self.reroll_mod[0] == "high":
				max_val: int = max(self.result);

				self.result[self.result.index(max_val)] = self.roll_single();
			else:
				for i in range(len(self.result)):
					while Comparisons[self.reroll_mod[0]](self.result[i], self.reroll_mod[1]):
						self.result[i] = self.roll_single();
		elif self.remove_mod:
			to_remove: list[int] = [];

			if self.remove_mod[0] == "low":
				min_val: int = min(self.result);

				to_remove.append(self.result.index(min_val));
			elif self.remove_mod[0] == "high":
				max_val: int = max(self.result);

				to_remove.append(self.result.index(max_val));
			else:
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
				dice_str: str = str(dice);

				# Remove subdice total and equal sign
				builder.append(f", {dice_str[:dice_str.find("=") - 1]}");

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
