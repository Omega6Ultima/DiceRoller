import winsound, threading, time, random, math, os;

DEFAULT_TIMER_SOUND = "alarm-clock-1.wav";
TIMER_SOUND = "alarm-clock-1.wav";

LESS = 0;
GREATER = 1;
LESSEQUAL = 2;
GREATEREQUAL = 3;
SIGNS = ("<", ">", "<=", ">=");

def round(num, places):
    temp = (num * (10**places));
    frac = math.modf(temp)[0];
    if(frac >= .5):
        temp += 1;
    temp -= frac;
    return (temp / (10**places));


class NewTimer():
    def __init__(self, time_sec, sound):
        self.mytime = time_sec;
        self.sound = sound;
        self._Timerobj = threading._Timer(self.mytime, self.run);
        self._Timerobj.start();
    def run(self):
        winsound.PlaySound(self.sound, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NOSTOP);

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
        self.vars = [0,]*NUMVARS;
    def eval_exp(self, expression):
        result = 0;
        self.exp = expression;
        self.expind = 0;

        self.get_token();

        if not self.token: #***dying here
            self.serror(2);
            return 0.0;

        result = self.eval_exp1(result);

##        if self.token:
##            self.serror(0);

        return result;

    def eval_exp1(self, result):
        slot = 0;
        temp_tok_type = 0;
        temp_token = "";

        if(self.tok_type == VARIABLE):
            temp_token = self.token;
            temp_tok_type = self.tok_type;
            slot = int(self.token.upper()) - int('A');

            self.get_token();

            if token != '=':
                putback();
                self.token = temp_token;
                self.tok_type = temp_tok_type;
            else:
                self.get_toke();
                self.eval_exp2(result);
                vars[slot] = result;
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
        print errors[e];

    def isdelim(self, char):
        if char in " +-*/%^=()" or char == 9 or char == '\r' or char == 0:
            return 1;
        else:
            return 0;

    def find_var(self, varname):
        if not varname.isalpha():
            serror(1);
            return 0.0;
        else:
            return self.vars[int(self.token[0].upper()) - int('A')];

    def putback(self):
        t = '';
        t = self.token;
        for i in len(t):
            self.expind -= 1;

def checkdigit(string):
    state = "";
    for c in string:
        if c.isdigit():
            state += "NUM "; #definitly a number
        elif c == '.':
            state += "NUM? ";    #maybe be part of a valid number or not
        elif c == "-":
            state += "NUM? ";    #maybe be part of a valid number or not
        else:
            state += "NOTDIGIT ";    #definitly not a number
    if "NOTDIGIT " in state:
        return 0;
    elif "NUM? " in state and not "NUM " in state:
        return 0;
    else:
        return 1;

def checkdice(dice, correct_dice):
##    if re.search(r"^\d+"+correct_dice+"\D+.*$", dice, flags=re.DOTALL):
##        return True;
##    else:
##        return False;
    if correct_dice in dice:
        ind = dice.find(correct_dice)+len(correct_dice);
        if ind >= len(dice):
            return True;
        char = dice[ind];
        if not checkdigit(char):
            return True;
    else:
        return False;

def rollandprint(d, printf=0, listvals=0):
    dice = "";
    diceRolls = [];
    total = 0;
    addon = 0;
    limit = None;
    count = None;
    org_d = d;

    #parsing the string to check for valid input
    for c in d[:d.find("[")]:
        if c.isalpha() and c != "d" and c != "[" and c != "]":
            print "Invalid Format For Parsing";
            return;

    #check to see if the string is formatted for counting rolls
    if SIGNS[LESSEQUAL] in d and not "[" in d and not "]" in d:
        count = [LESSEQUAL, int(d[d.find(SIGNS[LESSEQUAL])+2:]), 0];
        d = d[:d.find(SIGNS[LESSEQUAL])];
    elif SIGNS[GREATEREQUAL] in d and not "[" in d and not "]" in d:
        count = [GREATEREQUAL, int(d[d.find(SIGNS[GREATEREQUAL])+2:]), 0];
        d = d[:d.find(SIGNS[GREATEREQUAL])];
    elif SIGNS[LESS] in d and not "[" in d and not "]" in d:
##        print d[d.find(">"):len(d)];
        count = [LESS, int(d[d.find(SIGNS[LESS])+1:]), 0];
        d = d[:d.find(SIGNS[LESS])];
    elif SIGNS[GREATER] in d and not "[" in d and not "]" in d:
        count = [GREATER, int(d[d.find(SIGNS[GREATER])+1:]), 0];
        d = d[:d.find(SIGNS[GREATER])];

##    print count;

    #check if the string needs to repeat a set of dice
    if "*" in d:
        #print "repeating";
        repeat = int(d[:d.find("*")]);

        for t in range(repeat):
            diceRolls.append(rollandprint(d[d.find("*")+1:len(d)], printf, listvals));
        return diceRolls;

    #check to see if there are any limits to the dice rolls
    if "[" in d and "]" in d:
        if checkdigit(d[d.find("[")+1:d.find("]")]):
            limit = int(d[d.find("[")+1:d.find("]")]);
        elif "low" in d[d.find("[")+1:d.find("]")]:
            limit = "low";
        else:
            if SIGNS[LESSEQUAL] in d:
                limit = [LESSEQUAL, int(d[d.find(SIGNS[LESSEQUAL])+2:d.find("]")])];
            elif SIGNS[GREATEREQUAL] in d:
                limit = [GREATEREQUAL, int(d[d.find(SIGNS[GREATEREQUAL])+2:d.find("]")])];
            elif SIGNS[LESS] in d:
                limit = [LESS, int(d[d.find(SIGNS[LESS])+1:d.find("]")])];
            elif SIGNS[GREATER] in d:
                limit = [GREATER, int(d[d.find(SIGNS[GREATER])+1:d.find("]")])];
        d = d[:d.find("[")];

    #check to see if there are any modifiers to the dice roll
    if "+" in d:
        addon += int(d[d.find("+")+1: len(d)]);
        maxnum = int(d[d.find("d")+1: d.find("+")]);
    elif "-" in d:
        addon += -int(d[d.find("-")+1: len(d)]);
        maxnum = int(d[d.find("d")+1: d.find("-")]);
    else:
        addon = 0;
        maxnum = int(d[d.find("d")+1: len(d)]);

    #handle dractional dice rolls
    org_times = float(d[0:d.find("d")]);

    times_frac = round(math.modf(org_times)[0], len(d[d.find(".")+1:d.find("d")]));
    if times_frac:
        if count != None:
            roll = rollandprint("1d"+str(int(maxnum*times_frac))+"+"+str(addon)+SIGNS[count[0]]+str(count[1]), 0, 0);
        elif isinstance(limit, list):
            roll = rollandprint("1d"+str(int(maxnum*times_frac))+"+"+str(addon)+"["+SIGNS[limit[0]]+str(limit[1])+"]", 0, 0);
        elif isinstance(limit, str) and limit == "low":
            roll = rollandprint("1d"+str(int(maxnum*times_frac))+"+"+str(addon)+"["+limit+"]", 0, 0);
        else:
            roll = rollandprint("1d"+str(int(maxnum*times_frac))+"+"+str(addon), 0, 0);
        diceRolls.append(roll);
        total += roll;

    #check to see how many dice to rolls
    times = int(org_times);

    #roll the dice
    for r in range(times):
        roll = random.randint(1, maxnum);
        if limit != None:
            if isinstance(limit, int) and roll == limit:
                roll = rollandprint("1d"+str(maxnum)+"["+str(limit)+"]", 0, 0);
            elif isinstance(limit, list):
                if limit[0] == LESS:
                    if roll < limit[1]:
                        roll = rollandprint("1d"+str(maxnum)+"["+SIGNS[LESS]+str(limit[1])+"]", 0, 0);
                elif limit[0] == GREATER:
                    if roll > limit[1]:
                        roll = rollandprint("1d"+str(maxnum)+"["+SIGNS[GREATER]+str(limit[1])+"]", 0, 0);
                elif limit[0] == LESSEQUAL:
                    if roll <= limit[1]:
                        roll = rollandprint("1d"+str(maxnum)+"["+SIGNS[LESSEQUAL]+str(limit[1])+"]", 0, 0);
                elif limit[0] == GREATEREQUAL:
                    if roll >= limit[1]:
                        roll = rollandprint("1d"+str(maxnum)+"["+SIGNS[GREATEREQUAL]+str(limit[1])+"]", 0, 0);
##        print "This function is not yet complete";
        total += roll;
        diceRolls.append(roll);

    #if the limit was the lowest roll, take it out
    if isinstance(limit, str) and limit == "low":
        lowest = maxnum;
        for n in diceRolls:
            if n < lowest:
                lowest = n;
        diceRolls.remove(lowest);
        total -= lowest;
        times -= 1;

    #if the function was called to print
    if printf:
        if count == None:
            if times_frac:

                if addon:
                    print str(d),"(" + str(times)+d[d.find("d"):] + ", 1d"+str(int(maxnum*times_frac))+"+"+str(addon) + ")" + ":\t\tmax possible:" + str(int(org_times*maxnum) + addon);
                else:
                    print str(d),"(" + str(times)+d[d.find("d"):] + ", 1d"+str(int(maxnum*times_frac)) + ")" + ":\t\tmax possible:" + str(int(org_times*maxnum) + addon);
            else:
                print str(d) + ":\t\tmax possible:" + str(int(org_times*maxnum) + addon);
            print diceRolls;
            print total + addon, "\n";
        else:
            if count[0] == LESS:
                for r in diceRolls:
                    if r < count[1]:
                        count[2] += 1;
            elif count[0] == GREATER:
                for r in diceRolls:
                    if r > count[1]:
                        count[2] += 1;
            elif count[0] == LESSEQUAL:
                for r in diceRolls:
                    if r <= count[1]:
                        count[2] += 1;
            elif count[0] == GREATEREQUAL:
                for r in diceRolls:
                    if r >= count[1]:
                        count[2] += 1;
            if times_frac:
                if addon:
                    print str(d), "(" + str(times)+d[d.find("d"):] + ", 1d"+str(int(maxnum*times_frac))+"+"+str(addon) + ")";
                else:
                    print str(d), "(" + str(times)+d[d.find("d"):] + ", 1d"+str(int(maxnum*times_frac)) + ")";
            else:
                print str(org_d);
            print diceRolls;
            print count[2], '\n';
    elif listvals:
        return diceRolls;
    else:
        return total+addon;

def calculateandprint(d, printf=0):

    if d.isalpha():
        print "Invalid Format For Parsing";
        return;

    recursivedescentparser = RDP();
    result = recursivedescentparser.eval_exp(d);
    if printf:
        print d, "= ", result;
    else:
        return result;
##
####    if d[0] == "(":
####        fn = d[d.find("(")+1:d.find(")")];
####
####        fn = calculateandprint(fn);
####
####        if printf:
####            print d, "=  ", float(fn);
####        else:
####            return fn;
##
##    if "+" in d:
##        fn = d[:d.find("+")];
##        sn = d[d.find("+")+1:len(d)];
##        if not checkdigit(sn):
##            sn = calculateandprint(sn);
##
##        if printf:
##            print d, "=  ", float(fn)+float(sn);
##        else:
##            return float(fn)+float(sn);
##
##    elif "-" in d:
##        fn = d[:d.find("-")];
##        sn = d[d.find("-")+1:len(d)];
##        if not checkdigit(sn):
##            sn = calculateandprint(sn);
##
##        if printf:
##            print d, "=  ", float(fn)-float(sn);
##        else:
##            return float(fn)-float(sn);
##
##    elif "*" in d:
##        fn = d[:d.find("*")];
##        sn = d[d.find("*")+1:len(d)];
##        if not checkdigit(sn):
##            sn = calculateandprint(sn);
##
##        if printf:
##            print d, "=  ", float(fn)*float(sn);
##        else:
##            return float(fn)*float(sn);
##
##    elif "/" in d:
##        fn = d[:d.find("/")];
##        sn = d[d.find("/")+1:len(d)];
##        if not checkdigit(sn):
##            sn = calculateandprint(sn);
##
##        if printf:
##            print d, "=  ", float(fn)/float(sn);
##        else:
##            return float(fn)/float(sn);



def enchant(casterlevel):
    nums1 = rollandprint("20d20+"+str(casterlevel), 0, 1);
    nums2 = rollandprint("20d20+"+str(casterlevel), 0, 1);
    passes1 = 0;
    passes2 = 0;
##    for n in nums1:
##        if n >= 10:
##            passes1 += 1
##    for n in nums2:
##        if n >= 10:
##            passes2 += 1
    for i in range(len(nums1)):
        if nums1[i] >= 10:
            passes1 += 1;
        if nums2[i] >= 10:
            passes2 += 1;
    passes = (passes1 + passes2)/2;

    if passes < 10:
        print "enchant FAILED";
        return;

    useroll = rollandprint("1d8", 0, 0);
    for i in range(passes-10):
        if(useroll < 3):
            break;
        useroll = rollandprint("1d8", 0, 0);

    print "based on the spell and usage limit:", useroll,;
    print "and the average passes of:", str(passes)+"...";
    string = raw_input("pick an appriate dice combo ");
    result = (rollandprint(string, 0, 0));
    print "The results of the enchant are: ";
    print "20d20:", passes1, "\n20d20:", passes2, "\t", passes;
    print "usage limits:", useroll;
    print "dice combo:", str(string)+": ", str(result)+"+"+str(passes-10);

#dice roll pre and post processing
def none(d):
    rollandprint(d, 1, 0);

#Sample structure
#def func_name(d):
#   if not checkdice(d, limited_dice_type):
#       print Warning message;
#       return;
#   do any pre-processing
#   roll the dice
#   do any post-processing
#   print results in desired format

def tenagain(d):
    if not checkdice(d, "d10"):
        print "Using non-d10s for "+dicemode[0]+" mode";
        return;
    rolls = rollandprint(d, 0, 1);
    successes = 0;
    for r in rolls:
        if r == 10:
            rolls += rollandprint("1d10", 0, 1);
        if r >= 8:
            successes += 1;
    print rolls;
    print successes, " successes";

def nineagain(d):
    if not checkdice(d, "d10"):
        print "Using non-d10s for "+dicemode[0]+" mode";
        return;
    rolls = rollandprint(d, 0, 1);
    successes = 0;
    for r in rolls:
        if r >= 9:
            rolls += rollandprint("1d10", 0, 1);
        if r >= 8:
            successes += 1;
    print rolls;
    print successes, " successes";

def normdmg(d):
    if not checkdice(d, "d6"):
        print "Using non-d6s for "+dicemode[0]+" mode";
        return;
    rolls = rollandprint(d, 0, 1);
    stun = 0;
    body = 0;
    for r in rolls:
        stun += r;
        if r > 1 and r < 6:
            body += 1;
        elif r == 6:
            body += 2;
    print rolls;
    print "stun damage: ", stun;
    print "body damage: ", body;

def killdmg(d):
    if not checkdice(d, "d6"):
        print "Using non-d6s for "+dicemode[0]+" mode";
        return;
    rolls = rollandprint(d, 0, 1);
    body = 0;
    stun_mult = rollandprint("1d3", 0, 0);
    for r in rolls:
        body += r;
    print rolls;
    print "stun multiplier: ", stun_mult;
    print "stun damage: ", stun_mult*body;
    print "body damage: ", body;

dicemodes = {
"normal":none,
"10again":tenagain,
"9again":nineagain,
"normdmg":normdmg,
"killdmg":killdmg,
};

#***add the capability that when you roll a certain number, it rolls another dice of the same type
#***maybe have a list passed into rollandprint that defines (with constants) what needs to be printed/returned and in what order
#main program
if __name__ == "__main__":
    dicemode = ("normal", none);
    locked = False;
    passw = None;
    dice = "";
    Timerlist = [];
    print "(If you dont know what your doing type help)";

    while True:
        dice = raw_input("Enter the dice to roll: ").lower();
        if locked and dice == passw:
            locked = False;
            print "UNLOCKED";
            continue;
        elif locked:
            print "LOCKED";
            continue;
        elif dice == "exit" or dice == "quit" or dice=="stop":
            break;
        elif dice == "cls":
            os.system("cls");
            continue;
        elif dice == "test":
            rollandprint("13d13", 1, 0);
            rollandprint("1d4+5", 0, 1);
            rollandprint("1d20-4");
            rollandprint("4*4d6");
            rollandprint("10d2[1]");
            rollandprint("4d6[low]");
            rollandprint("12d12>=6", 1, 0);
            rollandprint("12d20[>=10]", 1, 0);
            rollandprint("12d10[<3]", 1, 0);
            rollandprint("5.5d12", 1);
            calculateandprint("10+14", 1);
            calculateandprint("54-19", 1);
            calculateandprint("4*8", 1);
            calculateandprint("27/9", 1);
            calculateandprint("50%4", 1);
            calculateandprint("3*(2+7)", 1);
            calculateandprint("2^3", 1);
            calculateandprint("-43-17", 1);
            checkdice("1d6", "d6");
            os.system("cls");
            print "Tests completed";
            continue;
        elif dice == "help":
            os.system("cls");
            print """HELP:
            roll a dice normally:\t 1d10
            roll a dice and add to it:\t 1d10+3
            roll a dice and subtract from it:\t 1d10-4
            roll multiple dice at the same time:\t 1d6, 1d8, 1d10
            roll multiple dice sets of the same type:\t 2*2d6
            roll a dice and reroll a certain number:\t 1d10[number]
            roll a set of dice and take out the lowest roll:\t 4d6[low]
            roll a set of dice and take out all numbers that dont fit the condition:\t 1d20[<=5]
            roll a fractional dice combo:\t 2.5d6, 3.78d6
            use as a calculator:\t 10+14, 54-19, 4*8, 27/9

            dnd functions:
                enchant:4 \t use my enchanting method from dnd 3.5 to enchant an object at caster level 4
                abilities \t roll ability scores for my dnd (7 sets of 4d6 minus the lowest)
                timer:6 \t set a timer to go off in 6 seconds""";
            continue;

        dicelist = dice.split(',');

        for d in dicelist:
            d.strip();
            if d.startswith("enchant:"):
                enchant(int(d[8:]));
            elif d == "abilities":
                while True:
                    total = 0;
                    nums = rollandprint("7*4d6[low]", 0, 0);
                    lowest = 18;
                    for n in nums:
                        if n < lowest:
                            lowest = n;
                        total += n;
                    nums.remove(lowest);
                    total -= lowest;
                    if total/6 < 10:
                        continue;
                    print nums;
                    break;
            elif d.startswith("timer:"):
                temptimer = NewTimer(int(d[6:]), TIMER_SOUND);
                Timerlist.append(temptimer);
            elif d.startswith("cmd:"):  #list of commands
                cmd = d[4:];
                if cmd == "tsound":
                    print TIMER_SOUND;
                elif cmd.startswith("tsound:"):
                    snd = cmd[7:];
                    if snd == "default":
                        snd = DEFAULT_TIMER_SOUND
                    tmpfile = open(snd);
                    if not (tmpfile):
                        print snd, "is not a valid file. Please check the name and try again.";
                    else:
                        TIMER_SOUND = snd;
                    tmpfile.close();
                elif cmd == "tstop":
                    winsound.PlaySound(None, winsound.SND_NOWAIT);
                elif cmd.startswith("lock:"):
                    passw = cmd[5:];
                    locked = True;
                    print "LOCKED";
                elif cmd == "dicemode":
                    print "dicemode is: ", dicemode;
                elif cmd == "dicemode?":
                    for dm in dicemodes:
                        print dm;
                elif cmd.startswith("dicemode:"):
                    tempmode = cmd[9:];
                    if tempmode in dicemodes:
                        dicemode = (tempmode, dicemodes[tempmode]);
                    else:
                        dicemode = ("normal", none);
                        print tempmode, "is not a valid mode. Resetting to normal.";
            elif "d" in d:
##                rollandprint(d, 1, 0);
                dicemode[1](d);
            else:
                calculateandprint(d, 1);
