#DiceRoller utility functions


def range_incl(start: int, stop: int):
	return [v for v in range(start, stop + 1)];


def is_digit(text: str):
	try:
		float(text);
	except (TypeError, ValueError):
		return False;

	return True;