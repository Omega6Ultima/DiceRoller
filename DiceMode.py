import io;
import sys;
from io import StringIO;
from typing import TextIO;

from DiceSet import DiceSet, DiceError, Comparisons, Calculations;


class DiceMode:
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

		# Rejoin any split text within parenthesis
		arg_index: int = 0;

		while arg_index < len(arg_list):
			if "(" in arg_list[arg_index] and not ")" in arg_list[arg_index]:
				arg_list[arg_index] += f", {arg_list[arg_index + 1]}";

				del arg_list[arg_index + 1];
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

				print(f"Using dicemode {self.name} with non-d{die_sides}, dice passed are d{diceset.dice_sides}", file=self.output);
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
