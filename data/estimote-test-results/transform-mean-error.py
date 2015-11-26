"""Transform.
Transform data from Estimote tests.

Usage:
  transform-mean-error.py --output=DIR --max-duration=SECONDS --xpos=X --ypos=Y [--mean-error] [--skip-header] (--input=DIR | <file>)
  transform-mean-error.py --help
  transform-mean-error.py --version

Options:
  -h --help                              Show this screen.
  --version                              Show version.
  -i DIR, --input=DIR                    Directory to read files to transform from.
  -o DIR, --output=DIR                   Directory to write output to.
  --max-duration=TIME                    Maximum duration of test in seconds. Only the first log entries that fit within the specified duration are considered.
  -x X, --xpos=X                         Real X position.
  -y Y, --ypos=Y                         Real Y position.
  --mean-error                           Outputs a single average mean error.
  --skip-header                          Set option if there is a header that must be skipped.
"""
from docopt import docopt
from schema import Schema, Use, And, Or
from decimal import Decimal
from collections import defaultdict
import os
import csv
import datetime
import operator
import math

class LogEntry:
  """An entry defined from a log consisting of date and a position expressed as a XY-coordinate"""
  def __init__(self, raw):
    self.date = datetime.datetime.strptime(raw[0], '%Y-%m-%d %H.%M.%S')
    self._coordinate = Coordinate(Decimal(raw[1]), Decimal(raw[2]))

  @property
  def coordinate(self):
    return Coordinate(
      self._coordinate.x,
      self._coordinate.y)

  @coordinate.setter
  def x(self, value):
    self._coordinate = value
    
  def date_to_str(self):
    return datetime.datetime.strftime(self.date, '%Y-%m-%d %H.%M.%S')

class Coordinate:
  """A coordinate consisting of X and Y values"""
  def __init__(self, x, y):
    self.x = x
    self.y = y

  def __eq__(self, other):
    return (isinstance(other, self.__class__) and
            self.x == other.x and
            self.y == other.y)

  def __ne__(self, other):
    return not self.__eq__(other)

  def __lt__(self, other):
    if self.x > other.x:
      return False
    elif self.x < other.x:
      return True    
    return self.y < other.y

  def __hash__(self):
    return hash(self.x) ^ hash(self.y)

  def distance_from(self, other):
    return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

def transform_all(input_dir, output_dir, max_duration, real_pos, mean_error = False, skip_header = False):
  files = [ f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f)) and os.path.splitext(f)[-1] == '.csv' ]
  for file in files:
    open_and_transform(os.path.join(input_dir, file), output_dir, max_duration, real_pos, mean_error, skip_header)

def open_and_transform(in_path, output_dir, max_duration, real_pos, mean_error = False, skip_header = False):
  with open(in_path, 'r') as infile:
    transform(infile, output_dir, max_duration, real_pos, mean_error, skip_header)
  
def transform(infile, output_dir, max_duration, real_pos, mean_error = False, skip_header = False):
  log_entries = parse_log_entries(infile, skip_header)
  filtered = filter_log_entries(log_entries, max_duration)  
  rows = [ csv_row_from_log_entry(i, e, real_pos) for i, e in enumerate(filtered) ]
  if mean_error:
    total = sum([ e.coordinate.distance_from(real_pos) for i, e in enumerate(filtered) ])
    average = total / len(filtered)
    rows = [ [average] ]
  write_csv(rows, os.path.join(output_dir, os.path.basename(infile.name)))

def csv_row_from_log_entry(idx, log_entry, real_pos):
  return [ log_entry.coordinate.distance_from(real_pos) ]
  
def write_csv(rows, out_path):
  with open(out_path, 'w') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(rows)
    
def filter_log_entries(log_entries, max_duration):
  if len(log_entries) == 0: return []
  start_date = log_entries[0].date
  end_date = start_date + datetime.timedelta(seconds=max_duration)
  return [ e for e in log_entries if e.date <= end_date ]

def parse_log_entries(infile, skip_header = False):
  reader = csv.reader(infile)
  if skip_header: next(reader)
  return [ LogEntry(e) for e in reader ]

if __name__ == '__main__':
  args = docopt(__doc__, version='Transform 1.0')
  s = Schema({
    '--help': bool,
    '--version': bool,
    '<file>': Or(Use(lambda f: open(f, 'r')), None, error='Input file not found.'),
    '--input': Or(os.path.exists, None, error='Input directory does not exist.'),
    '--output': And(os.path.exists, Use(lambda o: o), error='Output directory does not exist.'),
    '--max-duration': Use(int, error='Max duration must be an integer.'),
    '--xpos': Or(Use(Decimal), None, error='Value for X must be an integer.'),
    '--ypos': Or(Use(Decimal), None, error='Value for Y must be an integer.'),
    '--mean-error': bool,
    '--skip-header': bool    
  })  
  args = s.validate(args)

  real_pos = Coordinate(args['--xpos'], args['--ypos'])
  
  if args['<file>'] != None:
    transform(args['<file>'], args['--output'], args['--max-duration'], real_pos, args['--mean-error'], args['--skip-header'])
    args['<file>'].close()
  elif args['--input'] != None:
    transform_all(args['--input'], args['--output'], real_pos, args['--mean-error'], args['--skip-header'])
