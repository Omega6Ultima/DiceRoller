import io;
import sys;
from io import StringIO;
from typing import Any, Callable, TextIO;

from DiceSet import DiceSet, DiceError, Comparisons, Calculations;


class DiceMode:
	def _store(self, action: str, _diceset: DiceSet, mode_vars: dict[str, Any], debug: bool = False):
		"""Store value 'val' in 'var'"""
		args: list[str] = self._collect_args(action);

		val: float = float(args[0]);
		var: str = args[1];

		if debug:
			print(f"  Storing {val} into '{var}'", file=self._output);

		mode_vars[var] = val;


	def _check(self, action: str, diceset: DiceSet, _mode_vars: dict[str, Any], debug: bool = False):
		"""If the dice passed in do not have the same number of sides as 'die_sides' exit dicemode"""
		args: list[str] = self._collect_args(action);

		die_sides: int = int(args[0].removeprefix("d"));

		if debug:
			print(f"  Checking dice are d{die_sides}'s", file=self._output);

		if not diceset.verify_dice(die_sides):
			self._done = True;

			print(f"Using dicemode {self.name} with non-d{die_sides}, dice passed are d{diceset.dice_sides}", file=self._output);


	def _roll(self, action: str, diceset: DiceSet, mode_vars: dict[str, Any], debug: bool = False):
		"""Roll either dice passed in or 'dice' and add to the master roll list"""
		args: list[str] = self._collect_args(action);
		result: list[tuple[list[int], int]] = [];

		dice: str = args[0];

		try:
			if dice == "dice":
				if debug:
					print(f"  Rolling {diceset.display()}", file=self._output);

				result.extend(diceset.get_results());
			else:
				if debug:
					print(f"  Rolling {dice}", file=self._output);

				result.extend(DiceSet.from_str(dice).get_results());
		except DiceError as e:
			print(e, file=self._output);

			self._done = True;

			return;

		for i in range(len(result)):
			mode_vars["rolls"].extend(result[i][0]);
			mode_vars["rolls_adj"] += result[i][1];


	# noinspection SpellCheckingInspection
	def _rollinto(self, action: str, _diceset: DiceSet, mode_vars: dict[str, Any], debug: bool = False):
		"""Roll 'dice' and store into 'var'"""
		args: list[str] = self._collect_args(action);
		result: int = 0;

		dice: str = args[0];
		var: str = args[1];

		try:
			if debug:
				print(f"  Rolling {dice} and storing into '{var}'", file=self._output);

			result += int(DiceSet.from_str(dice));
		except DiceError as e:
			print(e, file=self._output);

			self._done = True;

			return;

		mode_vars[var] = result;


	def _total(self, action: str, _diceset: DiceSet, mode_vars: dict[str, Any], debug: bool = False):
		"""Add up all the dice from all roll actions, as well as any addition/subtraction modifier and store into 'var'"""
		args: list[str] = self._collect_args(action);

		var: str = args[0];

		if debug:
			print(f"  Totaling dice rolls and storing into '{var}'", file=self._output);

		mode_vars[var] = sum(mode_vars["rolls"]) + mode_vars["rolls_adj"];


	def _count(self, action: str, _diceset: DiceSet, mode_vars: dict[str, Any], debug: bool = False):
		"""Count the number of dice from roll actions that match the condition 'comp val' and store into 'var'"""
		args: list[str] = self._collect_args(action);

		comp: str = args[0];
		val: float = float(args[1]);
		var: str = args[2];

		if comp not in Comparisons:
			print(f"'{comp}' is not a valid comparison", file=self._output);

			self._done = True;

			return;

		if debug:
			print(f"  Counting rolls that match {comp} {val} and storing into '{var}'", file=self._output);

		count: int = 0;

		for roll in mode_vars["rolls"]:
			if Comparisons[comp](roll, val):
				count += 1;

		if debug:
			print(f"  Matching rolls: {count}, Non-matching rolls: {len(mode_vars["rolls"]) - count}", file=self._output);

		mode_vars[var] = count;


	def _calc(self, action: str, _diceset: DiceSet, mode_vars: dict[str, Any], debug: bool = False):
		"""Calculate the result of 'var1 op var2' and store into 'var1'"""
		args: list[str] = self._collect_args(action);

		var1: str = args[0];
		op: str = args[1];
		var2: str = args[2];

		if var1 not in mode_vars:
			print(f"'{var1}' has not been set before use", file=self._output);

			self._done = True;

			return;

		if op not in Calculations:
			print(f"'{op}' is not a valid calculation", file=self._output);

			self._done = True;

			return;

		if var2 not in mode_vars:
			print(f"'{var2}' has not been set before use", file=self._output);

			self._done = True;

			return;

		if debug:
			print(f"  Calculating '{var1} {op} {var2}' and storing into '{var1}'", file=self._output);
			print(f"  {mode_vars[var1]} {op} {mode_vars[var2]} = {Calculations[op](mode_vars[var1], mode_vars[var2])}", file=self._output);

		mode_vars[var1] = Calculations[op](mode_vars[var1], mode_vars[var2]);


	def _if(self, action: str, diceset: DiceSet, mode_vars: dict[str, Any], debug: bool = False):
		"""If the condition 'var1 comp var2' evaluates to True, execute action 'sub_action'"""
		args: list[str] = self._collect_args(action);

		var1: str = args[0];
		comp: str = args[1];
		var2: str = args[2];
		sub_action = args[3];

		if var1 not in mode_vars:
			print(f"'{var1}' has not been set before use", file=self._output);

			self._done = True;

			return;

		if comp not in Comparisons:
			print(f"'{comp}' is not a valid calculation", file=self._output);

			self._done = True;

			return;

		if var2 not in mode_vars:
			print(f"'{var2}' has not been set before use", file=self._output);

			self._done = True;

			return;

		if debug:
			print(f"  If '{var1} {comp} {var2}' is True, then execute '{sub_action}'", file=self._output);
			print(f"  {mode_vars[var1]} {comp} {mode_vars[var2]} = {Comparisons[comp](mode_vars[var1], mode_vars[var2])}", file=self._output);

		if Comparisons[comp](mode_vars[var1], mode_vars[var2]):
			self._execute_action(sub_action, diceset, mode_vars, debug);


	def _foreach(self, action: str, diceset: DiceSet, mode_vars: dict[str, Any], debug: bool = False):
		"""Repeat 'sub_action' 'var' times"""
		args: list[str] = self._collect_args(action);

		var: str = args[0];
		sub_action: str = args[1];

		if var not in mode_vars:
			print(f"'{var}' has not been set before use", file=self._output);

			self._done = True;

			return;

		if debug:
			print(f"  Looping {int(mode_vars[var])} times and running '{sub_action}'", file=self._output);

		for _ in range(int(mode_vars[var])):
			self._execute_action(sub_action, diceset, mode_vars, debug);


	def _while(self, action: str, _diceset: DiceSet, mode_vars: dict[str, Any], debug: bool = False):
		"""Repeat the following indented actions while 'var1 comp var2' evaluates to True"""
		args: list[str] = self._collect_args(action);

		var1: str = args[0];
		comp: str = args[1];
		var2: str = args[2];

		if var1 not in mode_vars:
			print(f"'{var1}' has not been set before use", file=self._output);

			self._done = True;

			return;

		if comp not in Comparisons:
			print(f"'{comp}' is not a valid calculation", file=self._output);

			self._done = True;

			return;

		if var2 not in mode_vars:
			print(f"'{var2}' has not been set before use", file=self._output);

			self._done = True;

			return;

		# Calculate loop_end
		if self._loop_end is None:
			loop_end: int = self._action_index + 1;
			indent_level: str = self.actions[loop_end].count("\t") * "\t";

			while self.actions[loop_end].startswith(indent_level):
				loop_end += 1;

			self._loop_end = loop_end - 1;

		if debug:
			print(f"  Looping while '{var1} {comp} {var2}' from action #{self._action_index} to #{self._loop_end}", file=self._output);
			print(f"  {mode_vars[var1]} {comp} {mode_vars[var2]} = {Comparisons[comp](mode_vars[var1], mode_vars[var2])}", file=self._output);

		if Comparisons[comp](mode_vars[var1], mode_vars[var2]):
			self._loop_entry = self._action_index;
		else:
			self._action_index = self._loop_end;
			self._loop_entry = None;
			self._loop_end = None;


	def _break(self, _action: str, _diceset: DiceSet, _mode_vars: dict[str, Any], debug: bool = False):
		"""Force the exiting of a while action without re-checking the condition"""
		if self._loop_entry is None:
			print("Break action outside of loop", file=self._output);

		if debug:
			print(f"  Breaking out from loop({self._loop_entry}-{self._loop_end})", file=self._output);

		self._action_index = self._loop_end;
		self._loop_entry = None;
		self._loop_end = None;


	def _print(self, action: str, _diceset: DiceSet, mode_vars: dict[str, Any], debug: bool = False):
		"""Print out the name and value of 'var'"""
		args: list[str] = self._collect_args(action);

		var: str = args[0];

		if var not in mode_vars:
			print(f"'{var}' has not been set before use", file=self._output);

			self._done = True;

			return;

		if debug:
			print(f"  Printing value of '{var}'", file=self._output);

		print(f"{var} = {mode_vars[var]}", file=self._output);


	_Actions: dict[str, Callable] = {
		"store": _store,
		"check": _check,
		# noinspection SpellCheckingInspection
		"rollinto": _rollinto, # Check rollinto first so 'roll' doesn't match it
		"roll": _roll,
		"total": _total,
		"count": _count,
		"calc": _calc,
		"if": _if,
		"foreach": _foreach,
		"while": _while,
		"break": _break,
		"print": _print,
	};


	def __init__(self, name: str, actions: list[str]):
		self.name: str = name;
		self.actions: list[str] = actions.copy();
		self._action_index: int = 0;
		self._done: bool = False;
		self._loop_entry: None | int = None;
		self._loop_end: None | int = None;
		self._output: TextIO | StringIO = sys.stdout;


	@staticmethod
	def _collect_args(line: str) -> list[str]:
		action: str = line[:line.find("(") + 1];
		arg_str: str = line.removeprefix(action).removesuffix(")");
		arg_list: list[str] = [a.strip() for a in arg_str.split(",")];

		# Rejoin any split text within parenthesis
		arg_index: int = 0;

		while arg_index < len(arg_list):
			if "(" in arg_list[arg_index] and not ")" in arg_list[arg_index]:
				arg_list[arg_index] += f", {arg_list[arg_index + 1]}";

				del arg_list[arg_index + 1];
			else:
				arg_index += 1;

		return arg_list;


	def validate(self, dice: str, capture_output: bool = False) -> tuple[bool, str]:
		# Initialize execution state
		self._done = False;
		self._loop_entry = None;
		self._loop_end = None;
		self._action_index = 0;
		# Create a StringIO to capture output, but we just drop it like its hot when we're done
		self._output = io.StringIO();
		v_output: StringIO = StringIO();

		diceset: DiceSet = DiceSet.from_str(dice);

		# Variables this mode will operate on
		mode_vars: dict[str, Any] = {
			"True": True,
			"False": False,
			"rolls": [],
			"rolls_adj": 0,
		};

		while not self._done:
			# Check to see if the current action is a valid action
			if not any([self.actions[self._action_index].lstrip().startswith(f"{action}(") for action in self._Actions]):
				print(f"Validate failed. Unknown action({self.actions[self._action_index]}) on line{self._action_index}", file=(v_output if capture_output else sys.stdout));

				return False, v_output.getvalue();

			# Execute single action
			try:
				self._execute_action(self.actions[self._action_index], diceset, mode_vars);
			except Exception as e:
				print(e, file=(v_output if capture_output else sys.stdout));

				return False, v_output.getvalue();

			if self._done == True and self._action_index < len(self.actions):
				# Exited early, probably due to an error
				print(f"Validate failed. Last action({self.actions[self._action_index]}) on line {self._action_index} cause an early exit", file=(v_output if capture_output else sys.stdout));

				return False, v_output.getvalue();

			# Move to next action
			self._action_index += 1;

			if self._action_index >= len(self.actions):
				# If the end of the action list is hit, and we are in a loop, go back to loop_entry
				if self._loop_entry is not None:
					self._action_index = self._loop_entry;
				else:
					self._done = True;

		return self._done, v_output.getvalue();


	def run(self, dice: str, debug: bool = False, capture_print: bool = False) -> dict[str, Any]:
		# Initialize execution state
		self._done = False;
		self._loop_entry = None;
		self._loop_end = None;
		self._action_index = 0;

		if capture_print:
			self._output = io.StringIO();

		diceset: DiceSet = DiceSet.from_str(dice);

		# Variables this mode will operate on
		mode_vars: dict[str, Any] = {
			"True": True,
			"False": False,
			"rolls": [],
			"rolls_adj": 0,
		};

		while not self._done:
			# Execute single action
			self._execute_action(self.actions[self._action_index], diceset, mode_vars, debug);

			# Move to next action
			self._action_index += 1;

			if self._action_index >= len(self.actions):
				# If the end of the action list is hit, and we are in a loop, go back to loop_entry
				if self._loop_entry is not None:
					self._action_index = self._loop_entry;
				else:
					self._done = True;

		if debug:
			print(mode_vars);

		if capture_print:
			mode_vars["output"] = self._output.getvalue();

			self._output = sys.stdout;

		return mode_vars;


	def _execute_action(self, line: str, diceset: DiceSet, mode_vars: dict[str, Any], debug: bool = False) -> None:
		if self._loop_entry is not None:
			# If we are in a loop and the action index is greater than loop_end, go back to loop_entry
			if self._action_index > self._loop_end:
				self._action_index = self._loop_entry;

				line = self.actions[self._action_index];

		clean_line: str = line.lstrip();

		if debug:
			print(f"Executing action #{self._action_index} '{clean_line}'", file=self._output);

		# Execute the func associated with the action on the current line
		for action, func in self._Actions.items():
			if clean_line.startswith(f"{action}("):
				func(self, line, diceset, mode_vars, debug);

				continue;
