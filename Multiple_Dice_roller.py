import winsound, threading, time, random, math, os;
from Multiple_Dice_roller_defaults import DEFAULT_DICEMODES;
from Multiple_Dice_roller_defaults import DEFAULT_TIMER_FILE;
from RPD import RDP;
from utils import *;

DEFAULT_TIMER_SOUND = "alarmclock";
TIMER_SOUND = "alarmclock";

LESS = 0;
GREATER = 1;
LESSEQUAL = 2;
GREATEREQUAL = 3;
SIGNS = ("<", ">", "<=", ">=");

class DiceError(Exception):
    def __init__(self, errmsg):
        Exception.__init__(self, errmsg);
        self.msg = errmsg;

class NewTimer():
    def __init__(self, time_sec, sound):
        self.mytime = time_sec;
        self.sound = sound;
        self._Timerobj = threading._Timer(self.mytime, self.run);
        self._Timerobj.start();
    def run(self):
        try:
            if self.sound == "alarmclock":
                winsound.PlaySound(DEFAULT_TIMER_FILE, winsound.SND_MEMORY | winsound.SND_NOSTOP);
            else:
                winsound.PlaySound(self.sound, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NOSTOP);
        except RuntimeError:
            print("Couldnt play the timer sound");

def checkdice(dice, correct_dice):
#    if re.search(r"^\d+"+correct_dice+"\D+.*$", dice, flags=re.DOTALL):
#        return True;
#   else:
#        return False;
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
    addon = 0;      #can be any integer
    limit = None;   #low
    reroll = None;  #any interger or [sign, integer]
    count = None;   #[sign, number, total]
    org_d = d;

    #parsing the string to check for valid input
    #for c in d[:d.find("[")]:
    for c in d:
        if c.isalpha() and c != "d" and c != "[" and c != "]" \
                and c != "{" and c != "}" and c != "<" and c != ">" \
                and c != "=" and c != "+" and c != "-" and not (d.find("[") < d.find(c) < d.find("]")):
##            print "Invalid Format For Parsing";
##            return;
            raise DiceError("bad Dice format");

    #check to see if the string is formatted for counting rolls
    if SIGNS[LESSEQUAL] in d and not "[" in d and not "]" in d and not "{" in d and not "}" in d:
        count = [LESSEQUAL, int(d[d.find(SIGNS[LESSEQUAL])+2:]), 0];
        d = d[:d.find(SIGNS[LESSEQUAL])];
    elif SIGNS[GREATEREQUAL] in d and not "[" in d and not "]" in d and not "{" in d and not "}" in d:
        count = [GREATEREQUAL, int(d[d.find(SIGNS[GREATEREQUAL])+2:]), 0];
        d = d[:d.find(SIGNS[GREATEREQUAL])];
    elif SIGNS[LESS] in d and not "[" in d and not "]" in d and not "{" in d and not "}" in d:
        count = [LESS, int(d[d.find(SIGNS[LESS])+1:]), 0];
        d = d[:d.find(SIGNS[LESS])];
    elif SIGNS[GREATER] in d and not "[" in d and not "]" in d and not "{" in d and not "}" in d:
        count = [GREATER, int(d[d.find(SIGNS[GREATER])+1:]), 0];
        d = d[:d.find(SIGNS[GREATER])];

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

    #check for any rerolls
    elif "{" in d and "}" in d:
        if checkdigit(d[d.find("{")+1:d.find("}")]):
            reroll = int(d[d.find("{")+1:d.find("}")]);
        else:
            if SIGNS[LESSEQUAL] in d:
                reroll = [LESSEQUAL, int(d[d.find(SIGNS[LESSEQUAL])+2:d.find("}")])];
            elif SIGNS[GREATEREQUAL] in d:
                reroll = [GREATEREQUAL, int(d[d.find(SIGNS[GREATEREQUAL])+2:d.find("}")])];
            elif SIGNS[LESS] in d:
                reroll = [LESS, int(d[d.find(SIGNS[LESS])+1:d.find("}")])];
            elif SIGNS[GREATER] in d:
                reroll = [GREATER, int(d[d.find(SIGNS[GREATER])+1:d.find("}")])];
        d = d[:d.find("{")];

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

    #handle fractional dice rolls
    org_times = float(d[0:d.find("d")]);

    times_frac = round(math.modf(org_times)[0], len(d[d.find(".")+1:d.find("d")]));
    if times_frac:
        if count != None:
            roll = rollandprint("1d"+str(int(maxnum*times_frac))+"+"+str(addon)+SIGNS[count[0]]+str(count[1]), 0, 0);
        elif isinstance(limit, int):
            roll = rollandprint("1d"+str(int(maxnum*times_frac))+"+"+str(addon)+"["+str(limit)+"]", 0, 0);
        elif isinstance(limit, list):
            roll = rollandprint("1d"+str(int(maxnum*times_frac))+"+"+str(addon)+"["+SIGNS[limit[0]]+str(limit[1])+"]", 0, 0);
        elif isinstance(limit, str) and limit == "low":
            roll = rollandprint("1d"+str(int(maxnum*times_frac))+"+"+str(addon)+"["+limit+"]", 0, 0);
        elif isinstance(reroll, int):
            roll = rollandprint("1d"+str(int(maxnum*times_frac))+"+"+str(addon)+"{"+reroll+"+"+"}", 0, 0);
        elif isinstance(reroll, list):
            roll = rollandprint("1d"+str(int(maxnum*times_frac))+"+"+str(addon)+"{"+SIGNS[reroll[0]]+str(reroll[1])+"}", 0, 0);
        else:
            roll = rollandprint("1d"+str(int(maxnum*times_frac))+"+"+str(addon), 0, 0);
        diceRolls.append(roll);
        total += roll;

    #check to see how many dice to rolls
    times = int(org_times);

    #roll the dice
    for r in range(times):
        roll = random.randint(1, maxnum);
        if reroll != None:
            if isinstance(reroll, int) and roll == reroll:
                roll = rollandprint("1d"+str(maxnum)+"{"+str(reroll)+"}", 0, 0);
            elif isinstance(reroll, list):
                if reroll[0] == LESS:
                    if roll < reroll[1]:
                        roll = rollandprint("1d"+str(maxnum)+"{"+SIGNS[LESS]+str(reroll[1])+"}", 0, 0);
                elif reroll[0] == GREATER:
                    if roll > reroll[1]:
                        roll = rollandprint("1d"+str(maxnum)+"{"+SIGNS[GREATER]+str(reroll[1])+"}", 0, 0);
                elif reroll[0] == LESSEQUAL:
                    if roll <= reroll[1]:
                        roll = rollandprint("1d"+str(maxnum)+"{"+SIGNS[LESSEQUAL]+str(reroll[1])+"}", 0, 0);
                elif reroll[0] == GREATEREQUAL:
                    if roll >= reroll[1]:
                        roll = rollandprint("1d"+str(maxnum)+"{"+SIGNS[GREATEREQUAL]+str(reroll[1])+"}", 0, 0);
        total += roll;
        diceRolls.append(roll);

    #if the limit was the lowest roll, take it out
    removeDice = [];
    if isinstance(limit, str) and limit == "low":
        lowest = maxnum;
        for n in diceRolls:
            if n < lowest:
                lowest = n;
        diceRolls.remove(lowest);
        total -= lowest;
        times -= 1;
        org_times -= 1;
    elif isinstance(limit, int):
        for n in diceRolls:
            if n == limit:
                removeDice.append(n);
##                diceRolls.remove(n);
                total -= n;
                times -= 1;
                org_times -= 1;
    elif isinstance(limit, list):
        for n in diceRolls:
            if limit[0] == LESS:
                if n < limit[1]:
                    removeDice.append(n);
##                    diceRolls.remove(n);
                    total -= n;
                    times -= 1;
                    org_times -= 1;
            elif limit[0] == GREATER:
                if n > limit[1]:
                    removeDice.append(n);
##                    diceRolls.remove(n);
                    total -= n;
                    times -= 1;
                    org_times -= 1;
            elif limit[0] == LESSEQUAL:
                if n <= limit[1]:
                    removeDice.append(n);
##                    diceRolls.remove(n);
                    total -= n;
                    times -= 1;
                    org_times -= 1;
            elif limit[0] == GREATEREQUAL:
                if n >= limit[1]:
                    removeDice.append(n);
##                    diceRolls.remove(n);
                    total -= n;
                    times -= 1;
                    org_times -= 1;

    if removeDice:
        for n in removeDice:
            diceRolls.remove(n);

    #if the function was called to print
    if printf:
        if count == None:
            if times_frac:

                if addon:
                    print(str(d)+" ("+str(times)+d[d.find("d"):]+", 1d"+str(int(maxnum*times_frac))+"+"+str(addon) + "):\t\tmax possible: "+str(int(org_times*maxnum)+addon));
                else:
                    print(str(d)+" ("+str(times)+d[d.find("d"):]+", 1d"+str(int(maxnum*times_frac))+"):\t\tmax possible: "+str(int(org_times*maxnum)+addon));
            else:
                if limit != None:
                    print(str(org_times)+"d"+str(maxnum)+":\t\tmax possible: "+str(int(org_times*maxnum)+addon));
                else:
                    print(str(d)+":\t\tmax possible:"+str(int(org_times*maxnum)+addon));
            print(diceRolls);
            print(str(total + addon)+"\n");
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
                    print(str(d)+" ("+str(times)+d[d.find("d"):]+", 1d"+str(int(maxnum*times_frac))+"+"+str(addon)+")");
                else:
                    print(str(d)+" ("+str(times)+d[d.find("d"):]+", 1d"+str(int(maxnum*times_frac))+")");
            else:
                print(str(org_d));
            print(diceRolls);
            print(count[2], '\n');
    elif listvals:
        return diceRolls;
    else:
        return total+addon;

def calculateandprint(d, printf=0):
##    if d.isalpha(): #***not sufficient enough, do full check
##        print "Invalid Format For Parsing";
##        return;

    if "." in d:
        temp = "";
        strs = d.split('.');
        if len(strs) > 1:
            for c in range(len(strs)):
                temp += strs[c];
                if len(strs[c]) < 1:
                    temp += "0.";
                elif c == len(strs)-1:
                    continue;
                elif (len(strs[c]) > 0 and strs[c][-1].isdigit()):
                    temp += ".";
                elif (len(strs[c]) > 0 and not strs[c][-1].isdigit()):
                    temp += "0.";
                else:
                    temp += ".";
            d = temp;
    elif "(" in d and ")" in d:
        temp = "";
        strs = d.split('(');
        if len(strs) > 1:
            for c in range(len(strs)):
                temp += strs[c];
                if c == len(strs)-1:
                    continue;
                elif len(temp) > 0 and temp[-1].isdigit():
                    temp += "*(";
                else:
                    temp += "(";
            d = temp;

        temp = "";
        strs = d.split(')');
        if len(strs) > 1:
            for c in range(len(strs)):
                temp += strs[c];
                if c == len(strs)-1:
                    continue;
                elif c < len(strs)-1 and len(strs[c+1]) > 0 and strs[c+1][0].isdigit():
                    temp += ")*";
                else:
                    temp += ")";
            d = temp;

    result = recursivedescentparser.eval_exp(d);
    if printf:
        if result != None:
            print(str(d)+" = "+str(result));
        else:
            if "=" in d:
                print(str(d)+" = "+str(recursivedescentparser.eval_exp(d[d.find("=")+1:])));
            else:
                print(d);
    else:
        return result;

def enchant(casterlevel):
    nums1 = rollandprint("20d20+"+str(casterlevel), 0, 1);
    nums2 = rollandprint("20d20+"+str(casterlevel), 0, 1);
    passes1 = 0;
    passes2 = 0;

    for i in range(len(nums1)):
        if nums1[i] >= 10:
            passes1 += 1;
        if nums2[i] >= 10:
            passes2 += 1;
    passes = (passes1 + passes2)/2;

    if passes < 10:
        print("enchant FAILED");
        return;

    useroll = rollandprint("1d8", 0, 0);
    for i in range(passes-10):
        if(useroll < 3):
            break;
        useroll = rollandprint("1d8", 0, 0);

    print("based on the spell and usage limit: "+str(useroll)+"and the average passes of: "+str(passes)+"...");
##    print "and the average passes of: "+str(passes)+"...";
    string = raw_input("pick an appriate dice combo ");
    result = (rollandprint(string, 0, 0));
    print("The results of the enchant are: ");
    print("20d20: "+str(passes1)+"\n20d20: "+str(passes2)+"\t"+str(passes));
    print("usage limits: "+str(useroll));
    print("dice combo: "+str(string)+": "+str(result)+"+"+str(passes-10));

#dice roll pre and post processing
def none(d):
    rollandprint(d, 1, 0);

#***add the capability that when you roll a certain number, it rolls another dice of the same type, kinda have with tenagain dicemodes
#***adjust the printed output when using removal syntax, 10d6[<=5]
#***count coin totals
#main program
if __name__ == "__main__":
    #This code is used to implement different dicemodes that can be read in, even when this is compiled into an exe
    #The source will be a python script but will not be executed directly
    #read in the MDR_dicemodes.py
    infile = openOrCreate("Multiple_Dice_roller_dicemodes.py", 'r', DEFAULT_DICEMODES, 1);
    if infile:
        temp = "".join(infile.readlines());
        infile.close();
    else:
        temp = DEFAULT_DICEMODES;
    #exec the text from MDR_dicemodes.py, defining all the functions from that module in this module
    exec(temp); #***optimize/safety
    #import the module to get the function names from it
    import Multiple_Dice_roller_dicemodes;
    flist = dir(Multiple_Dice_roller_dicemodes);
    del Multiple_Dice_roller_dicemodes;
    dicemodes = {"none":none,};
    for func in flist:
        if not func.startswith("__"):
            dicemodes[func] = globals()[func];  #add the names of the functions to the dicemode list
    #set the default dicemode
    dicemode = ("none", none);
    locked = False;
    passw = None;
    dice = "";
    Timerlist = [];
    recursivedescentparser = RDP();
    print("(If you dont know what your doing type help)");

    while True:
        dice = input("Enter the dice to roll: ").lower();
        if locked and dice == passw:
            locked = False;
            print("UNLOCKED");
            continue;
        elif locked:
            print("LOCKED");
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
            rollandprint("10d2{1}");
            rollandprint("4d6[low]");
            rollandprint("5d6[2]");
            rollandprint("10d6[<=5]");
            rollandprint("12d12>=6", 1, 0);
            rollandprint("12d20{>=10}", 1, 0);
            rollandprint("12d10{<3}", 1, 0);
            rollandprint("5.5d12", 1);
            calculateandprint("10+14", 1);
            calculateandprint("54-19", 1);
            calculateandprint("4*8", 1);
            calculateandprint("27/9", 1);
            calculateandprint("50%4", 1);
            calculateandprint("3*(2+7)", 1);
            calculateandprint("2^3", 1);
            calculateandprint("-43-17", 1);
            calculateandprint(".75+.5", 1);
            calculateandprint("(2*3.14)-3.14", 1);
            calculateandprint("75*(1+.5)/(1+.75)", 1);
            calculateandprint("7(1+1)", 1);
            calculateandprint("(2+4)6", 1);
            calculateandprint("a=32", 1);
            calculateandprint("a + 2", 1);
            calculateandprint("b = a ^ 2", 1);
            checkdice("1d6", "d6");
            checkdice("14d10+8", "d10");
            os.system("cls");
            print("Tests completed");
            continue;
        elif dice == "help":
            os.system("cls");
            def tab(n):
                return ("\t"*n)+'-';
            helpmsg = \
"""HELP:
    commands:
    exit, quit, stop(tab3)exit the Dice Roller
    cls(tab7)clear the output
    test(tab6)test the roller and calculator
    timer:6(tab6)set a timer for 6 seconds
    cmd:tsound(tab5)print the current timer sound
    cmd:tsound:filename(tab3)select a wav sound for all new timers
    cmd:tsound:default(tab3)select the default sound for timers
    cmd:tstop(tab5)stop all currently playing timer sounds
    cmd:lock:pass(tab4)lock the program with password: pass
    cmd:dicemode(tab4)print the current dicemode
    cmd:dicemode?(tab4)print all available dicemodes in MDR_dicemodes.py
    cmd:dicemode:default(tab2)reset the dicemode to normal
    cmd:dicemode:ndicemode(tab2)set the current dicemode to be ndicemode
    1d10(tab6)roll a dice normallly
    1d10+3(tab6)roll a dice and add to it
    1d10-4(tab6)roll a dice and subtract from it
    1d6, 1d8, 1d10(tab4)roll different dice at the same time
    2*2d6(tab6)same as 2d6, 2d6
    2*2d6+4(tab6)same as 2d6+4, 2d6+4
    1d10{4}(tab6)roll a dice and reroll any 4s
    1d20{<=5}(tab5)roll a dice and reroll any number that fits the conditional
    4d6[low](tab5)take out the lowest roll
    5d6[2](tab6)take out any 2s
    10d6[<=5](tab5)take out any number that fits the conditional
    2.5d6, 3.78d10(tab4)roll a dice with a fractional part
    10+14(tab6)add numbers
    54-19(tab6)subtract numbers
    4*8(tab7)multiply numbers
    27/9(tab6)divide numbers
    2^3(tab7)take a number to a power
    a = 23(tab6)store 23 to variable 'a'
    a * 3(tab6)use 'a' in a calculation
    PI = 3.141592654(tab3)store pi into PI""";
            print(helpmsg.replace("(tab1)", tab(1)).replace("(tab2)", tab(2)).replace("(tab3)", tab(3)).replace("(tab4)", tab(4)).replace("(tab5)", tab(5)).replace("(tab6)", tab(6)).replace("(tab7)", tab(7)));

            continue;

        dicelist = dice.split(',');

        for d in dicelist:
            d = d.strip();
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
                    print(nums);
                    break;
            elif d.startswith("timer:"):
                temptimer = NewTimer(int(d[6:]), TIMER_SOUND);
                Timerlist.append(temptimer);
            elif d.startswith("coin:"):
                dice = d[5:]+"d2";
                rolls = rollandprint(dice, 0, 1);
                print(d[5:]+" coins:");
                heads = 0;
                tails = 0;
                for r in rolls:
                    if r == 1:
                        heads += 1;
                    else:
                        tails += 1;
                print(heads, " heads and");
                print(tails, "tails ");
            elif d.startswith("cmd:"):  #list of commands
                cmd = d[4:];
                if cmd == "tsound":
                    print(TIMER_SOUND);
                elif cmd.startswith("tsound:"):
                    snd = cmd[7:];
                    if snd == "default":
                        TIMER_SOUND = "alarmclock";
                    else:
                        tempfile = open(snd);
                        if not tempfile:
                            print(snd+" is not a valid file. Please check the name and try again.");
                        else:
                            TIMER_SOUND = snd;
                        tempfile.close();
##                elif cmd.startswith("tsound:"):
##                    snd = cmd[7:];
##                    if snd == "default":
##                        snd = DEFAULT_TIMER_SOUND
##                    tmpfile = open(snd);
##                    if not (tmpfile):
##                        print snd+" is not a valid file. Please check the name and try again.";
##                    else:
##                        TIMER_SOUND = snd;
##                    tmpfile.close();
                elif cmd == "tstop":
                    winsound.PlaySound(None, winsound.SND_NOWAIT | winsound.SND_PURGE);
                elif cmd.startswith("lock:"):
                    passw = cmd[5:];
                    locked = True;
                    print("LOCKED");
                elif cmd == "dicemode":
                    print("dicemode is: "+str(dicemode));
                elif cmd == "dicemode?":
                    for dm in dicemodes:
                        print(dm);
                elif cmd.startswith("dicemode:"):
                    tempmode = cmd[9:];
                    if tempmode in dicemodes:
                        dicemode = (tempmode, dicemodes[tempmode]);
                    elif tempmode == "default":
                        dicemode = ("none", none);
                    else:
                        dicemode = ("none", none);
                        print(tempmode+" is not a valid mode. Resetting to none.");
            elif "d" in d:
                try:
                    dicemode[1](d);
                except DiceError:
                    try:
                        calculateandprint(d, 1);
                    except:
                        print("Malformed expression");
            else:
                calculateandprint(d, 1);
