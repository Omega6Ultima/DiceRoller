#utility functions
import math;

def round(num, places):
    temp = (num * (10**places));
    frac = math.modf(temp)[0];
    if(frac >= .5):
        temp += 1;
    temp -= frac;
    return (temp / (10**places));

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

def openOrCreate(fname, mode, createData, tries=1):
    numTries = 0;
    infile = None;
    while numTries < tries:
        try:
            infile = open(fname, mode);
            break;
        except IOError:
            infile = None;
            numTries += 1;
        if numTries >= tries:
            infile = open(fname, 'w');
            infile.write(createData);
            infile.close();
            infile = open(fname, mode);
            break;
    return infile;
