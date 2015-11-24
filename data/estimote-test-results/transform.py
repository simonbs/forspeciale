"""Transform.
Transform data from Estimote tests.

Usage:
  transform.py --output=DIR --max-duration=SECONDS  [--skip-header] (--input=DIR | <file>)
  transform.py --output=DIR --max-duration=SECONDS --resolution=RESOLUTION [--group] [--skip-header] (--input=DIR | <file>)
  transform.py --output=DIR --max-duration=SECONDS --resolution=RESOLUTION --group [--skip-header] --xmax=X --ymax=Y (--input=DIR | <file>)
  transform.py (-h | --help)
  transform.py --version

Options:
  -h --help                              Show this screen.
  --version                              Show version.
  -i DIR, --input=DIR                    Directory to read files to transform from.
  -o DIR, --output=DIR                   Directory to write output to.
  --max-duration=TIME                    Maximum duration of test in seconds. Only the first log entries that fit within the specified duration are considered.
  -r RESOLUTION, --resolution=RESOLUTION Resolution to group coordinates by.
  -g, --group                            Groups values and adds count to result. Only applicable if a resolution is specified.
  -x X, --xmax=X                         Maximum value of X. Creates intermediate values from 0 to X using resolution as interval.
  -y y, --ymax=Y                         Maximum value of Y. Creates intermediate values from 0 to Y using resolution as interval.
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

class LogEntry:
  """An entry defined from a log consisting of date and a position expressed as a XY-coordinate"""
  def __init__(self, raw, resolution = None):
    self.date = datetime.datetime.strptime(raw[0], '%Y-%m-%d %H.%M.%S')
    self._coordinate = Coordinate(Decimal(raw[1]), Decimal(raw[2]))
    self.resolution = resolution

  @property
  def coordinate(self):
    return Coordinate(
      self._adjust_for_resolution(self._coordinate.x),
      self._adjust_for_resolution(self._coordinate.y))

  @coordinate.setter
  def x(self, value):
    self._coordinate = value
    
  def date_to_str(self):
    return datetime.datetime.strftime(self.date, '%Y-%m-%d %H.%M.%S')

  def _adjust_for_resolution(self, value):
    return Decimal(round(value / self.resolution)) * self.resolution if self.resolution != None else value

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

def transform_all(input_dir, output_dir, max_duration, resolution = None, group = False, max_coord = None, skip_header = False):
  files = [ f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f)) and os.path.splitext(f)[-1] == '.csv' ]
  for file in files:
    open_and_transform(os.path.join(input_dir, file), output_dir, max_duration, resolution, group, max_coord, skip_header)

def open_and_transform(in_path, output_dir, max_duration, resolution = None, group = False, max_coord = None, skip_header = False):
  with open(in_path, 'r') as infile:
    transform(infile, output_dir, max_duration, resolution, group, max_coord, skip_header)
  
def transform(infile, output_dir, max_duration, resolution = None, group = False, max_coord = None, skip_header = False):
  log_entries = parse_log_entries(infile, resolution, skip_header)
  filtered = filter_log_entries(log_entries, max_duration)  
  if group and resolution:
    chunk_size = int(float(max(max_coord.x, max_coord.y)) / float(resolution)) + 1 # Take zero into account
    groups = group_log_entries(filtered, resolution, max_coord)
    keys = sorted(groups.keys())
    rows = [ csv_row_from_groups(i, c, groups[c]) for i, c in enumerate(keys) ]
    rows = spaced_rows_from_groups(rows, chunk_size)
  else:
    rows = [ csv_row_from_log_entry(i, e) for i, e in enumerate(filtered) ]
  write_csv(rows, os.path.join(output_dir, os.path.basename(infile.name)))
  
def write_csv(rows, out_path):
  with open(out_path, 'w') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(rows)

def spaced_rows_from_groups(groups, chunk_size):
  rows_chunks = chunks(groups, chunk_size)
  rows = []
  for chunk in rows_chunks:
    rows += chunk
    rows.append([])
  return rows

def group_log_entries(log_entries, resolution = 1, max_coord = None):
  res = defaultdict(list)
  if max_coord != None:
    for x in frange(0, max_coord.x, resolution):
      for y in frange(0, max_coord.y, resolution):
        res[Coordinate(x, y)] = []
  for e in log_entries: res[e.coordinate].append(e)
  return res

def csv_row_from_groups(idx, coord, groups):
  return [ coord.x, coord.y, len(groups) ]

def csv_row_from_log_entry(idx, log_entry):
  return [ log_entry.coordinate.x, log_entry.coordinate.y ]

def filter_log_entries(log_entries, max_duration):
  if len(log_entries) == 0: return []
  start_date = log_entries[0].date
  end_date = start_date + datetime.timedelta(seconds=max_duration)
  return [ e for e in log_entries if e.date <= end_date ]

def parse_log_entries(infile, resolution = None, skip_header = False):
  reader = csv.reader(infile)
  if skip_header: next(reader)
  return [ LogEntry(e, resolution) for e in reader ]

def create_range(strval):
  vals = [ int(x) for x in strval.split(',') ]
  return range(vals[0], vals[1])

def frange(start, end, step):
  n = start
  while n <= end:
    yield n
    n += step

def chunks(l, n):
  for i in xrange(0, len(l), n):
    yield l[i:i+n]

if __name__ == '__main__':
  args = docopt(__doc__, version='Transform 1.0')
  s = Schema({
    '--help': bool,
    '--version': bool,
    '<file>': Or(Use(lambda f: open(f, 'r')), None, error='Input file not found.'),
    '--input': Or(os.path.exists, None, error='Input directory does not exist.'),
    '--output': And(os.path.exists, Use(lambda o: o), error='Output directory does not exist.'),
    '--max-duration': Use(int, error='Max duration must be an integer.'),
    '--resolution': Or(Use(Decimal), None, error='Resolution must be a floating point number.'),
    '--xmax': Or(Use(int), None, error='Value for X must be an integer.'),
    '--ymax': Or(Use(int), None, error='Value for Y must be an integer.'),
    '--group': Or(Use(bool), None),
    '--skip-header': bool    
  })  
  args = s.validate(args)

  coord = Coordinate(args['--xmax'], args['--ymax']) if args['--xmax'] and args['--ymax'] else None
  
  if args['<file>'] != None:
    transform(args['<file>'], args['--output'], args['--max-duration'], args['--resolution'], args['--group'], coord, args['--skip-header'])
    args['<file>'].close()
  elif args['--input'] != None:
    transform_all(args['--input'], args['--output'], args['--max-duration'], args['--resolution'], args['--group'], coord, args['--skip-header'])
