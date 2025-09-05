import enum;
import unittest


class TokenType(enum.Enum):
	NotToken = 0;
	Delimiter = 1;
	Variable = 2;
	Number = 3;


class Rdp:
	"""A recursive descent parser adapted from a C++ example"""
	def __init__(self):
		self.exp: str = "";
		self.index: int = 0;
		self.token: str = "";
		self.tok_type: TokenType = TokenType.NotToken;
		self.vars: dict[str, float] = {};


	def eval_exp(self, expression: str) -> float:
		"""Evaluate passed in expression"""
		result: float = 0.0;
		self.exp = expression;
		self.index = 0;

		self._get_token();

		if not self.token:
			raise SyntaxError("No expression");

		result = self._eval_exp1(result);

		return result;


	def _eval_exp1(self, result: float):
		"""Handle variables"""
		temp_tok_type: TokenType = TokenType.NotToken;
		temp_token: str = "";

		if self.tok_type == TokenType.Variable:
			temp_token = self.token;
			temp_tok_type = self.tok_type;

			self._get_token();

			if self.token != '=':
				self._putback();
				self.token = temp_token;
				self.tok_type = temp_tok_type;
			else:
				# Assignment
				self._get_token();
				result = self._eval_exp2(result);
				self.vars[temp_token] = result;
				return;

		result = self._eval_exp2(result);

		return result;


	def _eval_exp2(self, result: float):
		"""Handle addition and subtraction"""
		op: str = "";
		temp: float = 0.0;

		result = self._eval_exp3(result);
		op = self.token;

		while op == '+' or op == '-':
			self._get_token();

			temp = self._eval_exp3(temp);

			if op == '-':
				result -= temp;
			elif op == '+':
				result += temp;

			op = self.token;

		return result;


	def _eval_exp3(self, result: float):
		"""Handle multiplication, division, and modulo"""
		op: str = "";
		temp: float = 0.0;

		result = self._eval_exp4(result);

		op = self.token;
		while op == '*' or op == '/' or op == '%':
			self._get_token();

			temp = self._eval_exp4(temp);

			if op == '*':
				result *= temp;
			elif op == '/':
				result /= temp;
			elif op == '%':
				result %= int(temp);

			op = self.token;

		return result;


	def _eval_exp4(self, result: float):
		"""Handle exponents"""
		base: float = 0.0;
		exp: float = 0.0;

		result = self._eval_exp5(result);

		if self.token == '^':
			self._get_token();

			exp = self._eval_exp4(exp);

			base = result;

			if exp == 0.0:
				return 1.0;

			for _ in range(int(abs(exp) - 1)):
				result *= base;

			# Handle negative exponents
			if exp < 0:
				result = 1 / result;

		return result;


	def _eval_exp5(self, result: float):
		op: str = "";

		if self.tok_type == TokenType.Delimiter and (self.token == '+' or self.token == '-'):
			op = self.token;
			self._get_token();

		result = self._eval_exp6(result);

		if op == "-":
			result = -result;

		return result;


	def _eval_exp6(self, result: float):
		"""Handle parenthesis"""
		if self.token == "(":
			self._get_token();
			result = self._eval_exp2(result);

			if not self.token == ")":
				raise SyntaxError("Unbalanced parenthesis");

			self._get_token();
		else:
			result = self._atom();

		return result;


	def _atom(self):
		"""Convert tokens into values"""
		if self.tok_type == TokenType.Variable:
			result = self._find_var(self.token);
			self._get_token();
			return result;
		elif self.tok_type == TokenType.Number:
			result = float(self.token);
			self._get_token();
			return result;
		else:
			raise SyntaxError("Syntax error. Unexpected end of expression");


	def _get_token(self):
		"""Get the next token in the expression"""
		temp: str = "";
		self.tok_type: TokenType = TokenType.NotToken;

		if self.index >= len(self.exp):
			return;

		while self.exp[self.index].isspace():
			self.index += 1;

		if self.exp[self.index] in "+-*/%^=()":
			self.tok_type = TokenType.Delimiter;
			temp += self.exp[self.index];
			self.index += 1;
		elif self.exp[self.index].isalpha():
			while self.index < len(self.exp) and not self.is_delimiter(self.exp[self.index]):
				temp += self.exp[self.index];
				self.index += 1;
			self.tok_type = TokenType.Variable;
		elif self.exp[self.index].isdigit():
			while self.index < len(self.exp) and not self.is_delimiter(self.exp[self.index]):
				temp += self.exp[self.index];
				self.index += 1;
			self.tok_type = TokenType.Number;

		self.token = temp;


	@staticmethod
	def is_delimiter(text: str) -> bool:
		"""Determine if text is a delimiting character"""
		if text in " +-*/%^=()" or text == 9 or text == '\r' or text == 0:
			return True;
		else:
			return False;


	def _find_var(self, varname: str) -> float:
		"""Get the value stored in a variable"""
		if not varname.isalpha():
			raise SyntaxError("Invalid variable name");
		else:
			# TODO handle KeyError
			return self.vars[varname];


	def _putback(self) -> None:
		"""Move the expression index back to the start of the current token"""
		self.index -= len(self.token);

class TestRdp(unittest.TestCase):
	def setUp(self):
		self.rdp: Rdp = Rdp();


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

		with self.assertRaises(ZeroDivisionError):
			self.rdp.eval_exp("4 / 0");


if __name__ == "__main__":
	unittest.main();