import os, re, sys

def clean(s):

    if len(s.split()) <= 8: return s

    ## days of the week
    s = re.sub(re.compile(r'(^| |, )(on|last|this|next|late) (monday|tuesday|wednesday|thursday|friday|saturday|sunday)( morning| afternoon| evening| night| alone)?($| |,|\.)', re.I), r'\5', s)
    s = re.sub(re.compile(r'^, (\w)'), r'\1', s)      # now fix sentence beginnings
    s = re.sub(re.compile(r'\s+'), r' ', s)           # clear extra spaces

    ## final ___ said clause
    if len(s.split()) > 10:
        s = re.sub(re.compile(r', [^,"]*? (said|reported)\.$', re.I), r'.', s)

    ## connector words
    s = re.sub(re.compile(r'^(however|still|so|nonetheless), ', re.I), r'', s)
    s = re.sub(re.compile(r'^(and|but),? ', re.I), r'', s)
    s = re.sub(re.compile(r', (however|though|meanwhile),'), r'', s)
    
    ## clean up
    s = s.strip()
    if s[0] == '"': s = s[0] + s[1].upper() + s[2:]
    else: s = s[0].upper() + s[1:]
    return s


def clean_aggressive(s):
    
    s = clean(s)

    ## final ___ said clause
    if s.split()[0].lower() not in ['as', 'if', 'since', 'asked']:
        last_clause = s.split(',')[-1].strip()
        if not last_clause: return s
        if last_clause.split()[0].lower() in ['and', 'but', 'although', 'or']: return s
        if len(last_clause.split()) >=  len(' '.join(s.split(',')[:-1]).split()): return s
        s = re.sub(re.compile(r',[^,."]*? (said|reported|told|announced|according to)[^,]*?\.$', re.I), r'.', s)
    
    return s


if __name__ == '__main__':
    
    input = sys.argv[1]
    output = sys.argv[2]
    
    if output == '-':
        out_fh = sys.stdout
    else:
        out_fh = open(output, 'w')
    lines = open(input).read().splitlines()
    for line in lines:
        
        ## skip sentences that start with a lowercase letter
        if line[0] == line[0].lower(): continue
        
        cleaned = clean(line)
        if line == cleaned: continue
        print line
        print cleaned
        print '---'    
        #out_fh.write(sent + '\n')
    
    out_fh.close()
