NUMVARS = 26;
DELIMETER = 1;
VARIABLE = 2;
NUMBER = 3;

class RDP():
    def __init__(self):
        self.exp = "";
        self.expind = 0;
        self.token = "";
        self.tok_type = 0;
        self.vars = {};
        #self.vars = [0,]*NUMVARS;
    def eval_exp(self, expression):
        result = 0;
        self.exp = expression;
        self.expind = 0;

        self.get_token();

        if not self.token:
            self.serror(2);
            return 0.0;

        result = self.eval_exp1(result);

#        if self.token:
#            self.serror(0);

        return result;

    def eval_exp1(self, result):
        slot = 0;
        temp_tok_type = 0;
        temp_token = "";

        if(self.tok_type == VARIABLE):
            temp_token = self.token;
            temp_tok_type = self.tok_type;
            #slot = int(ord(self.token.upper())) - ord('A');

            self.get_token();

            if self.token != '=':
                self.putback();
                self.token = temp_token;
                self.tok_type = temp_tok_type;
            else:
                #assignment
                self.get_token();
                result = self.eval_exp2(result);
                self.vars[temp_token] = result;
                return;

        result = self.eval_exp2(result);

        return result;

    def eval_exp2(self, result):
        op = '';
        temp = 0;

        result = self.eval_exp3(result);

        op = self.token;
        while op == '+' or op == '-':
            self.get_token();

            temp = self.eval_exp3(temp);

            if op == '-':
                result -= temp;
            elif op == '+':
                result += temp;

            op = self.token;

        return result;

    def eval_exp3(self, result):
        op = '';
        temp = 0;

        result = self.eval_exp4(result);

        op = self.token;
        while op == '*' or op == '/' or op == '%':
            self.get_token();

            temp = self.eval_exp4(temp);

            if op == '*':
                result *= temp;
            elif op == '/':
                result /= temp;
            elif op == '%':
                result %= int(temp);

            op = self.token;

        return result;

    def eval_exp4(self, result):
        temp = 0;
        ex = 0;
        t = 0;

        result = self.eval_exp5(result);

        if self.token == '^':
            self.get_token();

            temp = self.eval_exp4(temp);

            ex = result;

            if temp == 0.0:
                result = 1.0;
                return;
            for t in range(int(temp-1)):
                result *= ex;

        return result;

    def eval_exp5(self, result):
        op = 0;

        if self.tok_type == DELIMETER and (self.token == '+' or self.token == '-'):
            op = self.token;
            self.get_token();

        result = self.eval_exp6(result);

        if op == '-':
            result = -result;

        return result;

    def eval_exp6(self, result):
        if self.token == '(':
            self.get_token();
            result = self.eval_exp2(result);

            if not self.token == ')':
                self.serror(1);

            self.get_token();
        else:
            result = self.atom(result);

        return result;

    def atom(self, result):
        if self.tok_type == VARIABLE:
            result = self.find_var(self.token);
            self.get_token();
            return result;
        elif self.tok_type == NUMBER:
            result = float(self.token);
            self.get_token();
            return result;
        else:
            self.serror(0);

    def get_token(self):
        temp = "";

        self.tok_type = 0;
        #temp = '\0';

        if self.expind >= len(self.exp):
            return;

        while self.exp[self.expind].isspace():
            self.expind += 1;

        if self.exp[self.expind] in "+-*/%^=()":
            self.tok_type = DELIMETER;
            temp += self.exp[self.expind];
            self.expind += 1;
        elif self.exp[self.expind].isalpha():
            while self.expind < len(self.exp) and not self.isdelim(self.exp[self.expind]):
                temp += self.exp[self.expind];
                self.expind += 1;
            self.tok_type = VARIABLE;
        elif self.exp[self.expind].isdigit():
            while self.expind < len(self.exp) and not self.isdelim(self.exp[self.expind]):
                temp += self.exp[self.expind];
                self.expind += 1;
            self.tok_type = NUMBER;

        #temp += '\0';
        self.token = temp;

    def serror(self, e):
        errors = ["Syntax Error", "Unbalanced Paranthesis", "No Expression", ];
        print(errors[e]);
##        exit(1);

    def isdelim(self, char):
        if char in " +-*/%^=()" or char == 9 or char == '\r' or char == 0:
            return 1;
        else:
            return 0;

    def find_var(self, varname):
        if not varname.isalpha():
            self.serror(1);
            return 0.0;
        else:
            #slot = int(ord(varname[0].upper())) - ord('A');
            return self.vars[varname];

    def putback(self):
        t = '';
        t = self.token;
        for i in range(len(t)):
            self.expind -= 1;
