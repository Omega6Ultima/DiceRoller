#Sample structure
#def func_name(d):
#   if not checkdice(d, limited_dice_type):
#       print(Warning message);
#       return;
#   do any pre-processing
#   roll the dice
#   do any post-processing
#   print(results in desired format)

#function explanations
#   checkdice(dice, "d12") -checks to be sure dice is using d12s
#   rollandprint(dice, print_flag, list_flag) -roll the dice, printing if print_flag is true, else return the list of dice rolls if list_flag is true

def tenagain(d):
    if not checkdice(d, "d10"):
        print("Using non-d10s for tenagain mode");
        return;
    rolls = rollandprint(d, 0, 1);
    successes = 0;
    for r in rolls:
        if r == 10:
            rolls += rollandprint("1d10", 0, 1);
        if r >= 8:
            successes += 1;
    print(rolls);
    print(successes, " successes");

def nineagain(d):
    if not checkdice(d, "d10"):
        print("Using non-d10s for nineagain mode");
        return;
    rolls = rollandprint(d, 0, 1);
    successes = 0;
    for r in rolls:
        if r >= 9:
            rolls += rollandprint("1d10", 0, 1);
        if r >= 8:
            successes += 1;
    print(rolls);
    print(successes, " successes");

def normdmg(d):
    if not checkdice(d, "d6"):
        print("Using non-d6s for normdmg mode");
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
    print(rolls);
    print("stun damage: ", stun);
    print("body damage: ", body);

def killdmg(d):
    if not checkdice(d, "d6"):
        print("Using non-d6s for killdmg mode");
        return;
    rolls = rollandprint(d, 0, 1);
    body = 0;
    stun_mult = rollandprint("1d3", 0, 0);
    for r in rolls:
        body += r;
    print(rolls);
    print("stun multiplier: ", stun_mult);
    print("stun damage: ", stun_mult*body);
    print("body damage: ", body);