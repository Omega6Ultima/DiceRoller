import argparse;
import asyncio
import logging;
import os;
import platform;
import sys;
import threading;
import unittest;
from typing import Any, Callable;

import discord;
import dotenv;
import playsound3;

import RollerUtils;
from DiceMode import DiceMode;
from DiceSet import Colors, DiceError, DiceSet;
from Rdp import Rdp;

# Tab character for use in f-strings
Tab: str = "\t";
# Newline character for use in f-strings
NL: str = "\n";
# The default dicemode filename
DefaultDicemodeFile: str = "dicemodes.txt";
# The pre-defined dicemodes, will be written to file if it doesn't exist
# noinspection SpellCheckingInspection
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


class SoundTimer:
	def __init__(self, time_sec: int, sound: str):
		self.sound = sound;
		self._timer = threading.Timer(time_sec, self.run);

		self._timer.start();

	def run(self):
		playsound3.playsound(self.sound);


class AppState(dict):
	def __init__(self):
		super().__init__();


def eval_fstr(template: str, **kwargs) -> str:
	"""Delayed f-string evaluation"""
	return eval(f"f'''{template}'''", kwargs);


def discord_format(text: str) -> str:
	"""Formats a string to be output in discord, escapes certain discord formatting characters"""
	output: str = text;

	output = output.replace("*", r"\*");

	# Collapse multiple consecutive newlines into one
	while "\n\n" in output:
		output = output.replace("\n\n", "\n");

	return output;


def exit_main(app_state: AppState) -> str:
	"""Sets the flag for exiting the main loop of active mode"""
	if app_state["options"].mode == "active":
		app_state["done"] = True;

		return "Exiting ...";

	return "";


def get_help(app_state: AppState, context: str = "") -> str:
	"""Get general or contextual help"""

	match context:
		case "dicemode" | "dicemodes":
			return DicemodeHelpStr;
		case _:
			# Use mode to tailor general help, i.e. exit and timer don't do anything in discord mode
			return eval_fstr(HelpStr, Tab=Tab, mode=app_state['options'].mode, Colors=Colors);


def start_timer(app_state: AppState, seconds: str = "", sound: str = "alarm-clock-1.wav") -> str:
	if seconds == "":
		return "No seconds give for timer";

	if app_state["options"].mode == "active":
		SoundTimer(int(seconds), sound);

	return "";


def switch_dicemode(app_state: AppState, mode: str = "") -> str:
	"""Switch or clear active dicemode"""
	if mode == "":
		app_state["dicemode"] = "";

		return "Clearing dicemode";
	elif mode in app_state["dicemodes"]:
		app_state["dicemode"] = mode;

		return f"Switching to {mode}";
	else:
		return f"No dicemode named '{mode}'";


def inspect_dicemode(app_state: AppState, mode: str = "") -> str:
	"""Outputs the action list for the given dicemode"""
	if mode in app_state["dicemodes"]:
		mode_str: str = str(app_state["dicemodes"][mode]);

		if app_state["options"].mode == "discord":
			mode_str = mode_str.replace("\t", "-");

		return "\n" + mode_str;

	return f"No dicemode named '{mode}'";


def submit_dicemode(app_state: AppState, text: str = "") -> str:
	"""Enter a mode-dependant submit (sub)mode, returns whether a dicemode was added"""
	match app_state["options"].mode:
		case "active" | "auto":
			print("Entering dicemode submission mode, enter an empty line to exit");
			name: str = "";
			action_list: list[str] = [];
			submit_done: bool = False;

			while not submit_done:
				name = input("Enter a name for the new dicemode: ");

				if name == "":
					return "";

				if name in app_state["dicemodes"]:
					print(f"A dicemode named '{name}' already exists");
				else:
					submit_done = True;

			submit_done = False;

			while not submit_done:
				line: str = input("Enter an action: ");

				if line == "":
					submit_done = True;
				else:
					action_list.append(line);

			if name and action_list:
				dice: str = input("Enter a dice string to validate the Dicemode");
				dm: DiceMode = DiceMode(name, action_list);
				valid: tuple[bool, str] = dm.validate(dice);

				if valid[0]:
					app_state["dicemodes"][name] = dm;

					return "";
				else:
					return f"Dicemode failed validation ({valid[1]})";

			return "";
		case "discord":
			# print(f"'{text}'");

			lines: list[str] = text.split("\n");

			if lines and lines[0].startswith("dicemode"):
				name: str = lines[0].removeprefix("dicemode").strip("():");
				actions: list[str] = [];

				if name in app_state["dicemodes"]:
					return f"A dicemode named '{name}' already exists";

				for line in lines[1:-1]:
					actions.append(line.replace("-", "\t").removeprefix("\t"));

				if name and actions:
					dice: str = lines[-1].strip();
					dm: DiceMode = DiceMode(name, actions);
					valid: tuple[bool, str] = dm.validate(dice);

					if valid[0]:
						app_state["dicemodes"][name] = dm;

						return "";
					else:
						return f"Dicemode failed validation ({valid[1]})";

			return "";
		case _:
			return "submit command ran under unknown mode";


def toss_coins(_app_state: AppState, num: str = "1") -> str:
	"""Toss coin(s) aka 1d2's"""
	num_coins: int = int(num);

	results: list[tuple[list[int], int]] = DiceSet(num_coins, 2).get_results();

	coin_results: list[str] = ["Heads" if r == 1 else "Tails" for r in results[0][0]];

	return str(coin_results);


def count_dice(_app_state: AppState, dice: str) -> str:
	"""Count the instances of rolls"""
	if dice == "":
		return "No dice given to count";

	dice_set: DiceSet = DiceSet.from_str(dice);
	results: list[tuple[list[int], int]] = dice_set.get_results();
	builder: list[str] = [];

	for i in RollerUtils.range_incl(1, dice_set.dice_sides):
		just_amt: int = len(str(dice_set.dice_sides));
		roll_count: int = results[0][0].count(i);
		builder.append(f"{NL}#{i:>0{just_amt}} = {roll_count} ({round(roll_count / dice_set.num_dice * 100, 2)}%)");

	return "".join(builder);


HelpStr: str = """
Commands:
{Tab}help <context>{Tab * 2}get help with topic
{f'{Tab}exit{Tab * 4}exit the program' if mode == 'active' else ''}
{f'{Tab}stop{Tab * 4}stop the program' if mode == 'active' else ''}
{f'{Tab}quit{Tab * 4}quit the program' if mode == 'active' else ''}
{f'{Tab}timer <sec> [sound]{Tab * 1}start a timer for <sec> seconds and with [sound]' if mode == 'active' else ''}
{f'{Tab}clear{Tab * 4}clear the output' if mode == 'active' else ''}
{Tab}coin{Tab * 4}toss a coin
{Tab}coin <num>{Tab * 3}toss num coins
{Tab}dicemodes{Tab * 3}list available dicemodes
{Tab}dicemode <mode>{Tab * 2}switch to <mode> dicemode, all subsequent rolls with be processed through that dicemode
{Tab}inspect <mode>{Tab * 2}print the action list for given dicemode
{Tab}submit{f' <text>{Tab * 2}' if mode == 'discord' else f'{Tab * 4}'}submit a new dicemode{f''', lines after the dicemode name must be started with '-', use multiple '-' for indent levels, last line should be dice used to validate the dicemode'''}
{Tab}count <dice>{Tab * 2}roll the 'dice' and count each roll result and display the statistics
{f'''Example submit:
{Tab}submit dicemode(1_nova):
{Tab}-store(0, zero)
{Tab}-store(1, one)
{Tab}-roll(dice)
{Tab}-count(eq, 1, ones)
{Tab}-while(ones, gt, zero)
{Tab}--roll(dice)
{Tab}--calc(ones, sub, one)
{Tab}-total(sum)
{Tab}-print(sum)
{Tab}5d4''' if mode == "discord" else ""}
Dice rolls:
{Tab}1d4{Tab * 5}roll a 1d4
{Tab}1d6+1{Tab * 4}roll a 1d6 and add 1
{Tab}1d8-3{Tab * 4}roll a 1d8 and subtract 3
{Tab}3*1d10+2{Tab * 3}roll 3 sets of 1d10+2
{Tab}6d12{{1}}{Tab * 4}roll 6d12 and reroll any 1's
{Tab}6d12{{<6}}{Tab * 3}roll 6d12 and reroll any matching the condition
{Tab}6d12{{low}}{Tab * 3}roll 6d12 and reroll the lowest roll
{Tab}6d12{{high}}{Tab * 3}roll 6d12 and reroll the highest roll
{Tab}3d20[20]{Tab * 3}roll 3d20 and remove any and all 20's
{Tab}3d20[>=16]{Tab * 3}roll 3d20 and remove any rolls matching the condition
{Tab}3d20[low]{Tab * 3}roll 3d20 and remove the lowest roll
{Tab}3d20[high]{Tab * 3}roll 3d20 and remove the highest roll
{Tab}2d6<red>{Tab * 3}roll 2d6 and display the dice in red text
{Tab * 2}Possible colors are {', '.join(Colors.keys())}
Math expressions:
{Tab}10 + 14{Tab * 4}addition
{Tab}54 - 19{Tab * 4}subtraction
{Tab}4 * 8{Tab * 4}multiplication
{Tab}27 / 9{Tab * 4}division
{Tab}50 % 4{Tab * 4}modulo (division remainder)
{Tab}2 ^ 3{Tab * 4}exponents
{Tab}3 * ( 2 + 7 ){Tab * 2}parenthesis
{Tab}'1,000 * 5,000'{Tab * 2}using numbers with commas needs the expression quoted 
{Tab}
coin, 1d6, 12 * 2{Tab * 2}multiple commands/dice/math can done at the same time
""";
# noinspection SpellCheckingInspection
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
	"exit": exit_main,
	"quit": exit_main,
	"stop": exit_main,
	"timer": start_timer,
	"clear": lambda state: os.system("cls") if "win" in platform.system().lower() else os.system("clear"),
	"coin": toss_coins,
	"dicemodes": lambda state: ", ".join(state["dicemodes"].keys()),
	"dicemode": switch_dicemode,
	"inspect": inspect_dicemode,
	"submit": submit_dicemode,
	"count": count_dice,
};


def load_dicemodes(filename: str, dicemodes: dict[str, DiceMode]) -> None:
	"""Load DiceModes from filename and store in dicemode"""
	with open(filename, "r") as mode_file:
		parsing_mode: str = "";
		mode_actions: list[str] = [];

		for line in mode_file:
			# Strip off newline and any trailing spaces
			line = line.rstrip();

			if line.startswith("dicemode("):
				if parsing_mode:
					dicemodes[parsing_mode] = DiceMode(parsing_mode, mode_actions);
					mode_actions.clear();

				parsing_mode = line.removeprefix("dicemode").strip("():");
			elif line.strip() == "":
				dicemodes[parsing_mode] = DiceMode(parsing_mode, mode_actions);
				parsing_mode = "";
				mode_actions.clear();
			else:
				# Remove single tab from actions to align outer actions with no indent level
				mode_actions.append(line.replace("    ", "\t").removeprefix("\t"));

		if parsing_mode:
			dicemodes[parsing_mode] = DiceMode(parsing_mode, mode_actions);


async def process_input(text_in: str, app_state: AppState) -> str:
	"""Figure what to do with text_in and do it"""
	texts: list[str];
	output: list[str] = [];

	# Split any comma separated commands, dice, or math
	if "," in text_in:
		texts = [t.strip() for t in text_in.split(",")];
	else:
		texts = [text_in, ];

	# Rejoin any split text that was quoted
	texts_index: int = 0;

	while texts_index < len(texts):
		if texts[texts_index].count("'") == 1:
			texts[texts_index] += f",{texts[texts_index + 1]}";

			del texts[texts_index + 1];
		else:
			texts_index += 1;

	for text in texts:
		text = text.strip("'");

		if any([text.lower().startswith(key) for key in Commands]):
			# Process commands
			# Special case, discord mode submitting dicemodes will probably have commas incorrectly split of above
			if app_state["options"].mode == "discord" and text.lower().startswith("submit"):
				text = ",".join(texts);
				texts.clear();

			args: list[str] = text.split(" ");
			cmd_output: None | str;

			if len(args) == 1:
				cmd_output = Commands[args[0].lower()](app_state);
			else:
				cmd_output = Commands[args[0].lower()](app_state, *args[1:]);

			if cmd_output:
				output.append(f"{text} => {cmd_output}");
			if not cmd_output and args[0].lower() == "submit":
				output.append("Dicemode submitted successfully");
		elif DiceSet.is_dice(text):
			# Process dice
			try:
				if app_state["dicemode"]:
					dicemode: DiceMode = app_state["dicemodes"][app_state["dicemode"]];

					dm_vars: dict[str, Any] = dicemode.run(text, app_state["options"].debug, capture_print=True);

					output.append(f"{text} => {dm_vars["output"]}");
				else:
					output.append(f"{text} => {str(DiceSet.from_str(text))}");
			except DiceError as e:
				output.append(f"{text} => {str(e)}");
		# Math text is the only kind that might need quoted
		elif Rdp.is_math(text):
			# Process math
			try:
				output.append(f"{text} => {str(app_state["rdp"].eval_exp(text))}");
			except (SyntaxError, ZeroDivisionError, OverflowError) as e:
				output.append(f"{text} => {str(e)}");
		else:
			output.append(f"Entered text '{text}' is not a command, dice, or math expression");

	return "\n".join(output);


def main() -> int:
	"""Main function, parses command line args, loads dicemodes, and runs a loop according to mode"""
	app_state: AppState = AppState();

	# Parse command line options
	parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]).removesuffix(".py"), description="A utility packed dice roller and calculator");
	parser.add_argument("-d", "--debug", action="store_true", default=False, help="Run in dicemode debug mode");
	parser.add_argument("-l", "--load", nargs="*", help="Load an additional dicemode file");
	parser.add_argument("-m", "--mode", choices=["unit", "active", "auto", "discord"], default="active", help="Run in unit testing mode, interactive mode, automation mode or discord mode");
	parser.add_argument("-i", "--input", help="The input to process in auto mode, ignored in all other modes");

	# Set up semi-global variables
	app_state["options"] = parser.parse_args();
	app_state["dicemode"] = "";
	app_state["dicemodes"] = {};
	app_state["rdp"] = Rdp();
	app_state["done"] = False;

	# Are we running in unit mode?
	if app_state["options"].mode == "unit":
		test_suite: unittest.TestSuite = unittest.TestLoader().discover("tests");
		runner: unittest.TextTestRunner = unittest.TextTestRunner();

		runner.run(test_suite);

		exit(0);

	# Load dicemodes
	if not os.path.isfile(DefaultDicemodeFile):
		with open(DefaultDicemodeFile, "w") as outfile:
			for mode in DefaultDicemodes:
				outfile.write(DefaultDicemodes[mode].lstrip());

	load_dicemodes(DefaultDicemodeFile, app_state["dicemodes"]);

	if os.path.isfile("dicemodes_user.txt"):
		load_dicemodes("dicemodes_user.txt", app_state["dicemodes"]);

	if app_state["options"].load is not None:
		for filename in app_state["options"].load:
			if os.path.isfile(filename):
				load_dicemodes(filename, app_state["dicemodes"]);

	# Select which main loop based on mode argument
	if app_state["options"].mode == "active":
		while not app_state["done"]:
			prompt: str = input(f"Enter commands, dice, or math{f' ({app_state["dicemode"]})' if app_state['dicemode'] else ''}: ").strip();

			output: str = asyncio.run(process_input(prompt, app_state));

			print(output);
	elif app_state["options"].mode == "auto":
		prompt: str = app_state["options"].input.strip();
		output: str = asyncio.run(process_input(prompt, app_state));

		print(output);
	elif app_state["options"].mode == "discord":
		# File logger for discord log messages
		log_handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w");

		# Set up default intents and reading message content
		intents: discord.Intents = discord.Intents.default();
		# PyCharm incorrectly reports 2 warnings here due to how the Intents class populates flags
		intents.message_content = True; # noqa

		# Create discord client
		client: discord.Client = discord.Client(intents=intents);


		# Client event-driven functions
		@client.event
		async def on_ready() -> None:
			print(f"Logged in as {client.user} (ID: {client.user.id})");


		@client.event
		async def on_message(message: discord.message.Message) -> None:
			# Skip our own messages
			if message.author.id == client.user.id:
				return;

			# Skip messages with mentions of users other than us
			if message.mentions:
				if any([user.id != client.user.id for user in message.mentions]):
					return;

			content: str = message.content;

			# Remove the text that mentions us
			for user in message.mentions:
				content = content.replace(user.mention, "").strip();

			# Process input
			reply: str = await process_input(content, app_state);

			if reply:
				if len(reply) > 3950:
					reply = "Reply message is too large for discord";

				if app_state["dicemode"] != "":
					reply = f"{app_state['dicemode']}\n{reply}";

				await message.channel.send(discord_format(reply));


		# Load a .env file to get the secret stuff
		dotenv.load_dotenv(".env");

		# Run client
		client.run(os.getenv("BOT_TOKEN"), log_handler=log_handler);

	if any([d not in DefaultDicemodes for d in app_state["dicemodes"]]):
		with open("dicemodes_user.txt", "w") as outfile:
			for name, mode in app_state["dicemodes"].items():
				if name not in DefaultDicemodes:
					outfile.write(f"dicemode({name}):{NL}");

					for action in mode.actions:
						outfile.write(f"{Tab}{action}{NL}");

					outfile.write(NL);

	return 0;


if __name__ == "__main__":
	return_code: int = main();

	exit(return_code);