#!/usr/bin/env python
#
# Copyright (c) 2012 tero.saarni@gmail.com
# 
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import sys
import re
import argparse
import subprocess
import thread


class style: NORMAL = '0'; BOLD = '1'; UNDERLINE = '4'; NEGATIVE = '7';
class fg:    BLACK = '30'; RED = '31'; GREEN = '32'; YELLOW = '33'; BLUE = '34'; MAGENTA = '35'; CYAN = '36'; WHITE = '37'; RESET = '39';
class bg:    BLACK = '40'; RED = '41'; GREEN = '42'; YELLOW = '43'; BLUE = '44'; MAGENTA = '45'; CYAN = '46'; WHITE = '47'; RESET = '49';


def by_group(*functions):
    def closure(match):
        result = []
        for i, f in enumerate(functions):
            result.append(f(match.group(i + 1)))
        return ''.join(result)
    return closure


current_col_position = 0;

def align_column(match):
    global current_col_position
    txt = match.group(1)
    l = len(txt)
    current_col_position = max(current_col_position, l)
    return txt + (current_col_position - l) * ' '
    
def ansi(*args):
    def closure(text):
        return '\033[%sm%s\033[0m' % (';'.join(args), text)
    return closure


HOUR = ansi(style.NORMAL, fg.RED, bg.BLACK)
TIME = ansi(fg.GREEN)
PASS = lambda x: x


# EDIT THESE 
patterns = [
    (r'^(.+?: )', align_column),
    (r'(\d\d)(:)(\d\d)(:)(\d\d)', by_group(HOUR, PASS, TIME, PASS, TIME)),
    (r'(\[)(\d+)(\])', by_group(PASS, ansi(fg.WHITE, style.BOLD), PASS)),
    ]



class Highlighter:

    def __init__(self, patterns, log_prefix):
        self.log_prefix = log_prefix
        self.compiled_patterns = []
        for pattern, action in patterns:
            self.compiled_patterns.append((re.compile(pattern), action))

            
    def substituter(self, line):
        for pattern, action in self.compiled_patterns:
            line = pattern.sub(action, line)
        return line
        

    def process_file(self, infile, outfile):
        while True:
            line = infile.readline()
            if line == '':
                break
            outfile.write(self.log_prefix + self.substituter(line))
            

def start_filtering(pats, infile, outfile, log_prefix=''):
    h = Highlighter(pats, log_prefix)
    h.process_file(infile, outfile)

            
def main(argv):

    p = argparse.ArgumentParser()
    p.add_argument('-f', '--follow', action="store_true", default=False, help='output appended data as file grows, same as tail -f')
    p.add_argument('files', nargs=argparse.REMAINDER)
    args = p.parse_args()

    if len(args.files) == 0:
        start_filtering(patterns, sys.stdin, sys.stdout)
    elif len(args.files) > 0:
        
        if args.follow == True:
            processes = []
            for fname in args.files:
                p = subprocess.Popen(['tail', '-f', fname], stdout=subprocess.PIPE, bufsize=0)
                thread.start_new_thread(start_filtering, (patterns, p.stdout, sys.stdout, fname + ': '))
                processes.append(p)
            for p in processes:
                p.wait()
        else:
            for fname in args.files:
                start_filtering(patterns, file(fname), sys.stdout)
        

if __name__ == '__main__':
    main(sys.argv)

