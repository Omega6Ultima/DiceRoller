import enum;
import re;


# TODO potentially handle comma'd numbers
# TODO factorials
class Rdp:
	# Pattern for detecting math expression parsable by the parser
	# Not perfect but good enough to help filter
	MathPattern: re.Pattern = re.compile(r"""^			# Beginning of input
												[(\[]*			# Open parenthesis
												-?\d+(?:\.\d+)?	# Int or float
												(?:
												[-+*/%^]		# Math operators
												[(\[]*			# Open parenthesis
												-?\d+(?:\.\d+)?	# Int or float
												[)\]]*			# Close parenthesis
												)*
												""", re.X);

	class TokenType(enum.Enum):
		NotToken = 0;
		Delimiter = 1;
		Variable = 2;
		Number = 3;

	"""A recursive descent parser adapted from a C++ example"""
	def __init__(self):
		self.exp: str = "";
		self.index: int = 0;
		self.token: str = "";
		self.tok_type: Rdp.TokenType = Rdp.TokenType.NotToken;
		self.vars: dict[str, float] = {};


	@staticmethod
	def is_math(text: str) -> bool:
		# Remove any spaces first to simply regex
		text = text.replace(" ", "");

		if Rdp.MathPattern.fullmatch(text):
			return True;

		return False;


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
		if self.tok_type == Rdp.TokenType.Variable:
			temp_tok_type: Rdp.TokenType = self.tok_type;
			temp_token: str = self.token;

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
		result = self._eval_exp3(result);
		op: str = self.token;

		while op == '+' or op == '-':
			temp: float = 0.0;

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
		temp: float = 0.0;

		result = self._eval_exp4(result);

		op: str = self.token;
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
		exp: float = 0.0;

		result = self._eval_exp5(result);

		if self.token == '^':
			self._get_token();

			exp = self._eval_exp4(exp);

			base: float = result;

			if exp == 0.0:
				return 1.0;
			elif exp > 1000.0:
				raise OverflowError("Exponent too large");

			for _ in range(int(abs(exp) - 1)):
				result *= base;

			# Handle negative exponents
			if exp < 0:
				result = 1 / result;

		return result;


	def _eval_exp5(self, result: float):
		op: str = "";

		if self.tok_type == Rdp.TokenType.Delimiter and (self.token == '+' or self.token == '-'):
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
		elif self.token == "[":
			self._get_token();
			result = self._eval_exp2(result);

			if not self.token == "]":
				raise SyntaxError("Unbalanced square brackets");

			self._get_token();
		else:
			result = self._atom();

		return result;


	def _atom(self):
		"""Convert tokens into values"""
		if self.tok_type == Rdp.TokenType.Variable:
			result = self._find_var(self.token);
			self._get_token();
			return result;
		elif self.tok_type == Rdp.TokenType.Number:
			result = float(self.token);
			self._get_token();
			return result;
		else:
			raise SyntaxError("Syntax error. Unexpected end of expression");


	def _get_token(self):
		"""Get the next token in the expression"""
		temp: str = "";
		self.tok_type: Rdp.TokenType = Rdp.TokenType.NotToken;

		if self.index >= len(self.exp):
			return;

		while self.exp[self.index].isspace():
			self.index += 1;

		if self.exp[self.index] in "+-*/%^=()[]":
			self.tok_type = Rdp.TokenType.Delimiter;
			temp += self.exp[self.index];
			self.index += 1;
		elif self.exp[self.index].isalpha():
			while self.index < len(self.exp) and not self.is_delimiter(self.exp[self.index]):
				temp += self.exp[self.index];
				self.index += 1;
			self.tok_type = Rdp.TokenType.Variable;
		elif self.exp[self.index].isdigit():
			while self.index < len(self.exp) and not self.is_delimiter(self.exp[self.index]):
				temp += self.exp[self.index];
				self.index += 1;
			self.tok_type = Rdp.TokenType.Number;

		self.token = temp;


	@staticmethod
	def is_delimiter(text: str) -> bool:
		"""Determine if text is a delimiting character"""
		if text in " +-*/%^=()[]" or text == 9 or text == '\r' or text == 0:
			return True;
		else:
			return False;


	def _find_var(self, varname: str) -> float:
		"""Get the value stored in a variable"""
		if not varname.isalpha():
			raise SyntaxError(f"Invalid variable name '{varname}'");
		else:
			if varname in self.vars:
				return self.vars[varname];
			else:
				raise SyntaxError(f"Variable '{varname}' referenced before assigning value");


	def _putback(self) -> None:
		"""Move the expression index back to the start of the current token"""
		self.index -= len(self.token);
