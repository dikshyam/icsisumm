import re, traceback, sys
from lxml import etree
import treenode

# based on ~dilek/GALE-DIST/DISTILL-2008/LDC2008E39/scripts/english-preprocessing/text-cleanup.pl (from Wen)
def cleanup(text):
  text = " " + text.replace(",", "") + " "

  # negative number
  text = re.sub(r' -([0-9])', r' minus \1', text)

  # decimal point
  text = re.sub(r' ([0-9]*)[.]([0-9][0-9]*) ', r' \1 point \2 ', text)

  # height
  text = re.sub(r"(\d)'(\d)",r"\1 \2", text)

  # time
  text = re.sub(r"(\d)\s*am ",r"\1 a. m. ", text)
  text = re.sub(r"(\d)\s*pm ",r"\1 p. m. ", text)
  text = re.sub(r"(\d)'o",r"\1 oh ", text)
  text = re.sub(r"(\d?\d):00",r"\1 ", text)
  text = re.sub(r"(\d?\d):(\d\d)",r"\1 \2", text)

  # Dates
  #
  text = re.sub(r" (\d{1,2})(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)(\d{2,4}) ",r" \1 \2 \3 ", text)

  text = re.sub(r" ufo's",r" u. f. o.'s ", text)
  text = re.sub(r" www's",r" w. w. w.'s ", text)
  text = re.sub(r" cnnfn's",r" c. n. n. f. n.'s", text)
  text = re.sub(r" cnn's",r" c. n. n.'s", text)
  text = re.sub(r" abc's",r" a. b. c.'s", text)
  text = re.sub(r" nbc's",r" n. b. c.'s", text)
  text = re.sub(r" voa's",r" v. o. a.'s", text)
  text = re.sub(r" pri's",r" p. r. i.'s", text)
  text = re.sub(r" msnbc's",r" m. s. n. b. c.'s", text)
  text = re.sub(r" msn's",r" m. s. n.'s", text)
  text = re.sub(r" fbi's",r" f. b. i.'s", text)
  text = re.sub(r" usa's",r" u. s. a.'s", text)
  text = re.sub(r" cia's",r" c. i. a.'s", text)
  text = re.sub(r" nhl's",r" n. h. l.'s", text)
  text = re.sub(r" ftc's",r" f. t. c.'s", text)
  text = re.sub(r" fcc's",r" f. c. c.'s", text)
  text = re.sub(r" 3com's ",r" three com's ", text)
  text = re.sub(r" aka's ",r" a. k. a.'s ", text)
  text = re.sub(r" ceo's ",r" c. e. o.'s ", text)

  text = re.sub(r" ufo ",r" u. f. o. ", text)
  text = re.sub(r" www",r" w. w. w. ", text)
  text = re.sub(r" cnnfn",r" c. n. n. f. n. ", text)
  text = re.sub(r" cnn",r" c. n. n. ", text)
  text = re.sub(r" abc ",r" a. b. c. ", text)
  text = re.sub(r" nbc",r" n. b. c. ", text)
  text = re.sub(r" voa ",r" v. o. a. ", text)
  text = re.sub(r" pri ",r" p. r. i. ", text)
  text = re.sub(r" msnbc",r" m. s. n. b. c. ", text)
  text = re.sub(r" msn",r" m. s. n. ", text)
  text = re.sub(r" fbi",r" f. b. i. ", text)
  text = re.sub(r" usa ",r" u. s. a. ", text)
  text = re.sub(r" cia ",r" c. i. a. ", text)
  text = re.sub(r" nhl",r" n. h. l. ", text)
  text = re.sub(r" ftc",r" f. t. c. ", text)
  text = re.sub(r" fcc",r" f. c. c. ", text)
  text = re.sub(r" 3com ",r" three com ", text)
  text = re.sub(r" aka ",r" a. k. a. ", text)
  text = re.sub(r" ceo ",r" c. e. o. ", text)
  text = re.sub(r" sec ",r" s. e. c. ", text)

  text = re.sub(r" 401k",r" four oh one k. ", text)
  text = re.sub(r" 403b",r" four oh three b. ", text)
  text = re.sub(r" 1040 ",r" ten forty ", text)
  text = re.sub(r" 1040ez ",r" ten forty e. z. ", text)
  text = re.sub(r" 1040nr ",r" ten forty n. r. ", text)
  text = re.sub(r" 1040nrez ",r" ten forty n. r. e. z. ", text)
  text = re.sub(r"([0-9])khz - ",r"\1 kilo hertz to ", text)
  text = re.sub(r"([0-9])hz - ",r"\1 hertz to ", text)
  text = re.sub(r"([0-9])khz ",r"\1 kilo hertz ", text)
  text = re.sub(r"([0-9])hz ",r"\1 kilo hertz ", text)

  # Split hyphenated words
  #
  text = re.sub(r"([^ ])-([^ ])",r"\1 \2", text)

  # Separate letter sequences
  #
  text = re.sub(r" ([a-z])[.]([a-z])[.]",r" \1. \2. ", text)
  text = re.sub(r" ([a-z])[.]([a-z])[.]",r" \1. \2. ", text)

  # Handle some special abbrevs
  #
  text = re.sub(r" jr[.]? ",r" junior ", text)
  text = re.sub(r" sr[.]? ",r" senior ", text)
  text = re.sub(r" no[.] ",r" text ", text)
  text = re.sub(r" nr[.]",r" text ", text)
  text = re.sub(r" vs[.]? ",r" versus ", text)
  text = re.sub(r" mt[.]? ",r" mount ", text)
  text = re.sub(r" sgt[.]? ",r" sargent ", text)
  text = re.sub(r" hz[.]? ",r" hertz ", text)
  text = re.sub(r" khz[.]? ",r" kilo hertz ", text)
  text = re.sub(r" pt[.]? ",r" part ", text)
  text = re.sub(r" op[.] ",r" opus ", text)
  text = re.sub(r" sec[.] ",r" section ", text)
  text = re.sub(r" no ([0-9]+)",r" text \1 ", text)

  # Preserve letter/abbrev markers and decimal points, delete other periods.
  #
  text = re.sub(r" ([a-z])[.]'s ",r" \1~'s ", text)
  text = re.sub(r" ([a-z])[.]",r" \1~ ", text)
  text = re.sub(r" mr[.] ",r" mr~ ", text)
  text = re.sub(r" mrs[.] ",r" mrs~ ", text)
  text = re.sub(r" ms[.] ",r" ms~ ", text)
  text = re.sub(r" messrs[.] ",r" messrs~ ", text)

  text = re.sub(r"[.]",r" ", text)

  text = re.sub(r" ([a-z])~",r" \1.", text)
  text = re.sub(r" mr~ ",r" mr. ", text)
  text = re.sub(r" mrs~ ",r" mrs. ", text)
  text = re.sub(r" ms~ ",r" ms. ", text)
  text = re.sub(r" messrs~ ",r" messrs. ", text)

  # Preserve fragment markers and remove other hyphens
  #
  text = re.sub(r" -([a-z]+)",r" ~\1", text)
  text = re.sub(r"([a-z]+)- ",r"\1~ ", text)
  text = re.sub(r"-+",r" ", text)
  text = re.sub(r" ~([a-z]+)",r" -\1", text)
  text = re.sub(r"([a-z]+)~ ",r"\1- ", text)
  text = re.sub("\s+", " ", text)
  return text.strip()

def number_to_words(text):
  text = " " + text + " "

  # Get rid of empty fractions
  #
  text = re.sub(r"\s([0-9]+)[.]\s",r" \1 ", text)

  # Other fractionals
  #
  text = re.sub(r" ([0-9])*[.]([0-9][0-9]*)((nd|rd|st|th|s|\'s|s\')?) ",r" \1 point \2\3 ", text)

  # Phone numbers
  #
  text = re.sub("1-(\d)00-(\d)(\d)(\d)-(\d)(\d)(\d)(\d)", r"one \1 hundred \2 \3 \4 \5 \6 \7 \8 ", text)
  text = re.sub("1-(\d)(\d)(\d)-(\d)(\d)(\d)-(\d)(\d)(\d)(\d)", r"one \1 \2 \3 \4 \5 \6 \7 \8 \9 \10", text)
  text = re.sub("(\d)(\d)(\d)-(\d)(\d)(\d)-(\d)(\d)(\d)(\d)", r"\1 \2 \3 \4 \5 \6 \7 \8 \9 \10", text)
  text = re.sub("(\d)(\d)(\d)-(\d)(\d)(\d)(\d)", r"\1 \2 \3 \4 \5 \6 \7", text)

  # Sports scores.
  #
  text = re.sub(r" ([0-9]+)-([0-9]+) ",r" \1 \2 ", text)

  # Wordize years.  This needs doing up front, before we convert, say, 1872 into
  # one thousand eight hundred and seventy two.
  #
  text = re.sub(r" '(0[0-9])((s|\'s|s\')?) ",r" o. \1\2 ", text)
  text = re.sub(r" '([1-9][0-9])((s|\'s|s\')?) ",r" \1\2 ", text)
  text = re.sub(r" (1[1-9])00((s|\'s|s\')?) ",r" \1 hundred\2 ", text)
  text = re.sub(r" 19([0-9][0-9])((s|\'s|s\')?) ",r" nineteen \1\2 ", text)
  text = re.sub(r" 18([0-9][0-9])((s|\'s|s\')?) ",r" eighteen \1\2 ", text)
  text = re.sub(r" 17([0-9][0-9])((s|\'s|s\')?) ",r" seventeen \1\2 ", text)
  text = re.sub(r" 16([0-9][0-9])((s|\'s|s\')?) ",r" sixteen \1\2 ", text)
  text = re.sub(r" 15([0-9][0-9])((s|\'s|s\')?) ",r" fifteen \1\2 ", text)
  text = re.sub(r" 14([0-9][0-9])((s|\'s|s\')?) ",r" fourteen \1\2 ", text)
  text = re.sub(r" 13([0-9][0-9])((s|\'s|s\')?) ",r" thirteen \1\2 ", text)
  text = re.sub(r" 12([0-9][0-9])((s|\'s|s\')?) ",r" twelve \1\2 ", text)
  text = re.sub(r" 11([0-9][0-9])((s|\'s|s\')?) ",r" eleven \1\2 ", text)

  # Mils
  #
  text = re.sub(r" ([1-9][0-9][0-9])000000((th|s|\'s|s\')?) ",r" \1 million\2 ", text)
  text = re.sub(r" ([1-9][0-9])000000((th|s|\'s|s\')?) ",r" \1 million\2 ", text)
  text = re.sub(r" ([1-9])000000((th|s|\'s|s\')?) ",r" \1 million\2 ", text)

#       1    2    3      4    5    6    7    8    9
  text = re.sub(r" ([1-9][0-9][0-9])([0-9][0-9][0-9][0-9][0-9][0-9])((nd|rd|st|th|s|\'s|s\')?) ",r" \1 million and \2\3 ", text)
  text = re.sub(r" ([1-9][0-9])([0-9][0-9][0-9][0-9][0-9][0-9])((nd|rd|st|th|s|\'s|s\')?) ",r" \1 million and \2\3 ", text)
  text = re.sub(r" ([1-9])([0-9][0-9][0-9][0-9][0-9][0-9])((nd|rd|st|th|s|\'s|s\')?) ",r" \1 million and \2\3 ", text)

  # Thousands
  #
  text = re.sub(r" ([1-9][0-9][0-9])000((th|s|\'s|s\')?) ",r" \1 thousand\2 ", text)
  text = re.sub(r" ([0-9][0-9])000((th|s|\'s|s\')?) ",r" \1 thousand\2 ", text)
  text = re.sub(r" ([1-9])000((th|s|\'s|s\')?) ",r" \1 thousand\2 ", text)
  text = re.sub(r" ([1-9][0-9][0-9])([0-9][0-9][0-9])((nd|rd|th|s|\'s|s\')?) ",r" \1 thousand and \2\3 ", text)
  text = re.sub(r" ([0-9][0-9])([0-9][0-9][0-9])((nd|rd|th|s|\'s|s\')?) ",r" \1 thousand and \2\3 ", text)
  text = re.sub(r" ([1-9])([0-9][0-9][0-9])((st|nd|rd|th|s|\'s|s\')?) ",r" \1 thousand and \2\3 ", text)

  # Hundreds
  #
  text = re.sub(r" 0?([0-9][0-9])((th|st|rd|nd|s|\'s|s\')?) ",r" \1\2 ", text)
  text = re.sub(r" 0?([0-9])((th|st|rd|nd|s|\'s|s\')?) ",r" \1\2 ", text)
  text = re.sub(r" ([1-9])00((th|s|\'s|s\')?) ",r" \1 hundred\2 ", text)
  text = re.sub(r" ([1-9])([0-9][0-9])((th|st|rd|nd|s|\'s|s\')?) ",r" \1 hundred and \2\3 ", text)

  # Tens
  #
  text = re.sub(r" 10((th|\'s|s\'|s)?) ",r" ten\1 ", text)
  text = re.sub(r" 11((th|\'s|s\'|s)?) ",r" eleven\1 ", text)
  text = re.sub(r" 12th ",r" twelfth ", text)
  text = re.sub(r" 12((\'s|s\')?) ",r" twelve\1 ", text)
  text = re.sub(r" 12s ",r" twelves ", text)
  text = re.sub(r" 13((th|\'s|s\'|s)?) ",r" thirteen\1 ", text)
  text = re.sub(r" 14((th|\'s|s\'|s)?) ",r" fourteen\1 ", text)
  text = re.sub(r" 15((th|\'s|s\'|s)?) ",r" fifteen\1 ", text)
  text = re.sub(r" 16((th|\'s|s\'|s)?) ",r" sixteen\1 ", text)
  text = re.sub(r" 17((th|\'s|s\'|s)?) ",r" seventeen\1 ", text)
  text = re.sub(r" 18((th|\'s|s\'|s)?) ",r" eighteen\1 ", text)
  text = re.sub(r" 19((th|\'s|s\'|s)?) ",r" nineteen\1 ", text)
  text = re.sub(r" 20(th|s) ",r" twentie\1 ", text)
  text = re.sub(r" 30(th|s) ",r" thirtie\1 ", text)
  text = re.sub(r" 40(th|s) ",r" fortie\1 ", text)
  text = re.sub(r" 50(th|s) ",r" fiftie\1 ", text)
  text = re.sub(r" 60(th|s) ",r" sixtie\1 ", text)
  text = re.sub(r" 70(th|s) ",r" seventie\1 ", text)
  text = re.sub(r" 80(th|s) ",r" eightie\1 ", text)
  text = re.sub(r" 90(th|s) ",r" ninetie\1 ", text)
  text = re.sub(r" 20((\'s)?) ",r" twenty\1 ", text)
  text = re.sub(r" 30((\'s)?) ",r" thirty\1 ", text)
  text = re.sub(r" 40((\'s)?) ",r" forty\1 ", text)
  text = re.sub(r" 50((\'s)?) ",r" fifty\1 ", text)
  text = re.sub(r" 60((\'s)?) ",r" sixty\1 ", text)
  text = re.sub(r" 70((\'s)?) ",r" seventy\1 ", text)
  text = re.sub(r" 80((\'s)?) ",r" eighty\1 ", text)
  text = re.sub(r" 90((\'s)?) ",r" ninety\1 ", text)

  text = re.sub(r" 2([1-9])((er)?)((nd|rd|st|th|s|\'s|s\')?) ",r" twenty \1\2\4 ", text)
  text = re.sub(r" 3([1-9])((er)?)((nd|rd|st|th|s|\'s|s\')?) ",r" thirty \1\2\4 ", text)
  text = re.sub(r" 4([1-9])((er)?)((nd|rd|st|th|s|\'s|s\')?) ",r" forty \1\2\4 ", text)
  text = re.sub(r" 5([1-9])((er)?)((nd|rd|st|th|s|\'s|s\')?) ",r" fifty \1\2\4 ", text)
  text = re.sub(r" 6([1-9])((er)?)((nd|rd|st|th|s|\'s|s\')?) ",r" sixty \1\2\4 ", text)
  text = re.sub(r" 7([1-9])((er)?)((nd|rd|st|th|s|\'s|s\')?) ",r" seventy \1\2\4 ", text)
  text = re.sub(r" 8([1-9])((er)?)((nd|rd|st|th|s|\'s|s\')?) ",r" eighty \1\2\4 ", text)
  text = re.sub(r" 9([1-9])((er)?)((nd|rd|st|th|s|\'s|s\')?) ",r" ninety \1\2\4 ", text)

  text = re.sub(r" 1er((s|s\'|\'s)?) ",r" oner\1 ", text)
  text = re.sub(r" 2er((s|s\'|\'s)?) ",r" twoer\1 ", text)
  text = re.sub(r" 3er((s|s\'|\'s)?) ",r" threeer\1 ", text)
  text = re.sub(r" 4er((s|s\'|\'s)?) ",r" fourer\1 ", text)
  text = re.sub(r" 5er((s|s\'|\'s)?) ",r" fiver\1 ", text)
  text = re.sub(r" 6er((s|s\'|\'s)?) ",r" sixer\1 ", text)
  text = re.sub(r" 7er((s|s\'|\'s)?) ",r" sevener\1 ", text)
  text = re.sub(r" 8er((s|s\'|\'s)?) ",r" eighter\1 ", text)
  text = re.sub(r" 9er((s|s\'|\'s)?) ",r" niner\1 ", text)

  text = re.sub(r" 0*1st ",r" first ", text)
  text = re.sub(r" 0*2nd ",r" second ", text)
  text = re.sub(r" 0*3rd ",r" third ", text)
  text = re.sub(r" 0*4th ",r" fourth ", text)
  text = re.sub(r" 0*5th ",r" fifth ", text)
  text = re.sub(r" 0*6th ",r" sixth ", text)
  text = re.sub(r" 0*7th ",r" seventh ", text)
  text = re.sub(r" 0*8th ",r" eighth ", text)
  text = re.sub(r" 0*9th ",r" ninth ", text)

  text = re.sub(r" 0*0s ",r" zeroes ", text)
  text = re.sub(r" 0*0((\'s|s\')?) ",r" zero\1 ", text)
  text = re.sub(r" 0*1((\'s|s\'|s)?) ",r" one\1 ", text)
  text = re.sub(r" 0*2((\'s|s\'|s)?) ",r" two\1 ", text)
  text = re.sub(r" 0*3((\'s|s\'|s)?) ",r" three\1 ", text)
  text = re.sub(r" 0*4((\'s|s\'|s)?) ",r" four\1 ", text)
  text = re.sub(r" 0*5((\'s|s\'|s)?) ",r" five\1 ", text)
  text = re.sub(r" 0*6 ",r" six ", text)
  text = re.sub(r" 0*6s ",r" sixes ", text)
  text = re.sub(r" 0*6(s\'|\'s) ",r" six\1 ", text)
  text = re.sub(r" 0*7((\'s|s\'|s)?) ",r" seven\1 ", text)
  text = re.sub(r" 0*8((\'s|s\'|s)?) ",r" eight\1 ", text)
  text = re.sub(r" 0*9((\'s|s\'|s)?) ",r" nine\1 ", text)

  # Common fractions
  #
  text = re.sub(r" 1/4 ",r" a quarter ", text)
  text = re.sub(r" 1/2 ",r" a half ", text)
  text = re.sub(r" 3/4 ",r" three quarters ", text)

  text = re.sub(r" 000([0-9]) ",r" \1 ", text)
  text = re.sub(r" 00([0-9]) ",r" \1 ", text)
  text = re.sub(r" 0([0-9]) ",r" \1 ", text)

  # Handle cases like 1234 processed by above.
  #
  text = re.sub(r" million and ([^ ][^ ]*) thousand and ",r" million \1 thousand and ", text)
  text = re.sub(r" thousand and ([^ ][^ ]*) hundred and ",r" thousand \1 hundred and ", text)

  # Corrections of some introduced errors
  #
  text = re.sub(r" one (hundreds|thousands|millions) ",r" \1 ", text)

  # Condense and trim
  #
  text = re.sub(r"  *",r" ", text)
  text = text.strip()
  return text

def asrify(root):
    for node in root:
        if not re.search("[a-zA-Z]", node.label) or node.label == "CODE" or node.label == "-NONE-" or node.label == "META":
            node.cut()
        if node.isLeaf() and not re.search("[a-zA-Z0-9]", node.text):
            node.cut()
        if node.label.startswith("-") and node.label.endswith("-"):
            node.cut()
        if not node.label.endswith('-'):
            node.label = re.sub(r'[-=].*', '', node.label)
        if node.label == "TOP":
            node.label = ""
    for leaf in root.leaves:
        leaf.text = leaf.text.upper()
    for node in root.leaves:
        if node.isLeaf():
            # split A.B.C. in A. B. C.
            found = re.search('^([A-Z](\.[A-Z])+\.?)', node.text)
            if found:
                parent = node.parent
                index = node.index
                for letter in ['(%s %s.)' % (node.label, x) for x in found.groups(0)[0].split(".") if len(x) > 0]:
                    parent.grow(letter, index)
                    index += 1
                node.cut()
                continue
            # paste 'S 'LL N'T to the previous word
            if (re.search("^'[A-Z]", node.text) or node.text == "N'T" or (node.text == "NA" and node.label == "TO")) and node.previousLeaf != None:
                node.previousLeaf.text += node.text
                #node.previousLeaf.label += "-" + node.label
                node.cut()
                continue
            node.text = cleanup(node.text.lower()).upper()
            node.text = cleanup(node.text.lower()).upper()
            # convert numbers to words
            if re.search('[0-9]', node.text):
                node.text = number_to_words(node.text.lower()).upper()
                if re.search(node.text, '[^A-Z ]'):
                    sys.stderr.write('WARNING: %s %s\n' % (str(node), str(tree)))
            if " " in node.text:
                parent = node.parent
                index = node.index
                for word in node.text.split():
                    parent.grow("(%s %s)" % (node.label, word), index)
                    index += 1
                node.cut()

#def asrify(tree):
#    for node in tree:
#        if not re.search("[a-zA-Z]", node.label) or node.label == "CODE" or node.label == "-NONE-" or node.label == "META":
#            node.cut()
#        if node.text != "" and not re.search("[a-zA-Z0-9]", node.text):
#            node.cut()
#        if node.label.startswith("-") and node.label.endswith("-"):
#            node.cut()
#        if not node.label.endswith('-'):
#            node.label = re.sub(r'[-=].*', '', node.label)
#        if node.label == "TOP":
#            node.label = ""
#    for leaf in tree.leaves:
#        leaf.text = leaf.text.upper()

def _add_appos_annot(element, parse_tree, word_id):
    text_start = word_id
    if element.text:
        word_id += len(element.text.strip().split())
    for child in element:
        word_id += _add_appos_annot(child, parse_tree, word_id)
    text_end = word_id
    if element.tag == 'COREF' and 'TYPE' in element.attrib and element.attrib["TYPE"] == "APPOS":
        found = 0
        node = parse_tree.leaves[text_start]
        while node.parent:
            if node.leaves[0].leaf_index < text_start or node.leaves[-1].leaf_index >= text_end - 1:
                found = 1
                node.appos_label = element.attrib['SUBTYPE']
                if node.appos_label.endswith('ATTRIB'):
                    node.appos_label = node.appos_label.replace('ATTRIB', 'ATTRIBUTE')
                break
            node = node.parent
        if found == 0:
            sys.stderr.write('WARNING: not found [%s] in %s\n' % (" ".join([x.text for x in parse_tree.leaves[text_start:text_end]]), parse_tree) )
            raise Exception()
    if element.tail:
        word_id += len(element.tail.strip().split())
    return word_id - text_start


def annotate_tree_with_appos(tree, line):
    for node in tree:
        node.appos_label = "O"
    line = line.replace("&", "&amp;")
    try:
        root = etree.XML("<ROOT>%s</ROOT>" % line)
        word_id = 0
        if root.text:
            word_id += len(root.text.strip().split())
        for element in root:
            word_id += _add_appos_annot(element, tree, word_id)
    except:
        traceback.print_exc()
        return False
    return True

name_mapping = {
    'LOCATION':'LOC',
    'ORGANIZATION':'ORG',
    'ORGANISATION':'ORG',
    }
name_allowed = ['PERSON', 'ORG', 'ORGANISATION', 'ORGANIZATION', 'GPE', 'TIME', 'DATE', 'LOC', 'LOCATION']

def _add_name_annot(element, parse_tree, word_id):
    text_start = word_id
    if element.text:
        word_id += len(element.text.strip().split())
    for child in element:
        word_id += _add_name_annot(child, parse_tree, word_id)
    text_end = word_id
    if element.tag == "ENAMEX" and 'TYPE' in element.attrib and element.attrib['TYPE'] in name_allowed:
        found = 0
        node = parse_tree.leaves[text_start]
        while node.parent:
            if node.leaves[0].leaf_index < text_start or node.leaves[-1].leaf_index >= text_end - 1:
                found = 1
                if element.attrib['TYPE'] in name_mapping:
                    node.name_label = name_mapping[element.attrib['TYPE']]
                else:
                    node.name_label = element.attrib['TYPE']
                break
            node = node.parent
        if found == 0:
            sys.stderr.write('WARNING: not found [%s] in %s\n' % (" ".join([x.text for x in parse_tree.leaves[text_start:text_end]]), parse_tree) )
            raise Exception()
    if element.tail:
        word_id += len(element.tail.strip().split())
    return word_id - text_start

def annotate_tree_with_names(tree, line):
    for node in tree:
        node.name_label = "O"
    line = line.replace("&", "&amp;")
    try:
        root = etree.XML("<ROOT>%s</ROOT>" % line)
        word_id = 0
        if root.text:
            word_id += len(root.text.strip().split())
        for element in root:
            word_id += _add_name_annot(element, tree, word_id)
    except:
        traceback.print_exc()
        return False
    return True

def set_bio_label(node, attribute):
    label = getattr(node, attribute)
    if label != "O":
        setattr(node.leaves[0], attribute, "B-" + label)
        for leaf in node.leaves[1:]:
            setattr(leaf, attribute, "I-" + label)

def read_bio_labels(input, id_column, bio_column):
    output = {}
    last_label = "I-O"
    begin_tokens = []

    for line in input.xreadlines():
        tokens = line.strip().split()
        if len(tokens) < max(bio_column, id_column) + 1:
            continue
        if last_label != 'I-O' and tokens[bio_column] != last_label:
            id = ":".join(begin_tokens[id_column].split(":")[:2])
            if id not in output:
                output[id] = []
            begin_id = int(begin_tokens[id_column].split(":")[2])
            end_id = int(end_tokens[id_column].split(":")[2])
            label = last_label[2:]
            output[id].append((begin_id, end_id + 1, label))
        if tokens[bio_column].startswith('B-'):
            begin_tokens = tokens
        last_label = 'I-' + tokens[bio_column].split('-')[-1]
        end_tokens = tokens
    if last_label != 'I-O':
        id = ":".join(begin_tokens[id_column].split(":")[:2])
        if id not in output:
            output[id] = []
        begin_id = int(begin_tokens[id_column].split(":")[2])
        end_id = int(end_tokens[id_column].split(":")[2])
        label = last_label[2:]
        output[id].append((begin_id, end_id + 1, label))
    return output
