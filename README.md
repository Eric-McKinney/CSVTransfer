# CSVTransfer

## Project Description
The purpose of this project is to enable the transfer of large amounts of 
data from one csv to another. Specifically, any number of columns can be
chosen to be moved, but just as many columns need to be chosen to be the
destination of the data. The transfer is done according to another column
from each file to "match by" so that data can be associated with other data.
For example, you have two csvs which contain data about your personal data from
two different music streaming services. The csvs are formatted differently,
have different fields, different amounts of data, and different data in general.
Say that one of the csvs has very thorough listening duration data that you want
to move to the other file. In this case you would match the data by song name
since it would be in both files in the same format, and it would be less likely
to contain duplicate entries. Then you would transfer the listening duration 
column. If this column didn't exist in the destination file, then it should be
created before running the script.

## Setup
Download `main.py`, `config_template.ini`, and optionally this `README.md` for 
future reference (I don't have anything fancy set up you have to do it 
through GitHub lol). Once you've done that, make sure you have python 
installed. After that you should be good to go.

## Usage
For this script to be able to see and read the csv files they must be in the
same directory as this script or in a subdirectory. Once you have your csvs
where you want them, fill out the config file with at bare minimum the file
names (or relative path if they're in a subdirectory), the target column(s), 
and the column to match by for the source file and target file. All fields 
names shown in the template should be present even if empty otherwise a 
`KeyError` will occur. In the command prompt or shell (in the same directory 
as main.py) do `py main.py` or `python3 main.py`.

### Options
Currently, the only options are `-h`, `--help`, and `--debug`.

**-h**, **--help**
> Prints help message and terminates.

**--debug**
> Enables debug print statements.

## Config File
By default, the script uses `config_template.ini` for configuration. If you 
want to use a config file by a different name, open `main.py` and change 
the `CONFIG_FILE_NAME` variable accordingly. The `config_template.ini` file 
has a few bits filled out already. Fill in the rest. If you don't, you'll be 
prompted when you run `main.py` for the variables that are necessary for 
the script to do what it needs to do, and they will be taken via stdin. Values
taken this way will not be written to the config file.

The config file has five sections: defaults, source, target, output, and fields. 
The defaults section contains default values for the source and target sections. 
These are filled out for you in the template. The source and target sections are
to further specify information about the two csv files that will be a part of the
data transfer. Everything in these sections need values except the things that
appear in the defaults section. The output section is mostly just to name the
output file, but you can also change the dialect to write output csvs in. Excel
is the default and is what I would recommend. More about dialects below. You can
also optionally give the name for a file to dump data that could not be matched.
Finally, the fields section is a place where you can specify formats for data to
be validated against via regex. This is entirely optional. Data that does not
match the given regex for a given header will not be transferred and counts
towards the unmatched data.

## Config File Fields

### defaults section
**header_row_num**
> The number of the row (starting at 0) which contains the headers you want to
use.

**ignored_rows**
> A comma separated list of numbers of rows to ignore while parsing, 
transferring data, and putting data in the output file. Any negative value or
out of bounds value effectively means nothing. In the template this value is
defaulted to -1 (which is a filler value), so no rows are ignored. The order 
of the numbers does not matter. Data ignored this way does not contribute to 
the unmatched data.

### source & target sections
**file_name**
> Name of the file to use. Can be a relative path to a file in a subdirectory.

**target_column(s)**
> A comma separated list of the headers whose columns should be used in the data
transfer. The number of headers given should be the same between source and 
target. The order matters as the first header from the source will be matched to
the first header for the target, and the same goes for the second, third, etc.

**match_by**
> The header of the column to use for matching data during the transfer. The data
in this column should be shared between the two files or at least match to some
degree. Only data that can be matched to an item from this column in both files
will be transferred. The data in this column should also ideally be unique. For
example, a column of serial numbers would be good because serial numbers don't
change in format like names do, and there likely won't be duplicates.

**header_row_num**
> Same as in the defaults section, but if a value is provided here it will
override the value given in defaults.

**ignored_rows**
> See above.

### output section
**file_name**
> The name of the output file. If this collides with a file in the same 
directory as the script, you will be prompted with a choice of whether you 
want to overwrite said file.

**unmatched_file_name**
> If given a value, all unmatched data will be dumped into the file by the given
name. If left blank, no unmatched data is dumped.

**dialect**
> The dialect to write the output csv file in. Valid dialects include unix,
excel, and excel_tab. The default and the one you probably want is excel. The
dialect only determines things like what to quote, line terminator, etc. More
info can be found [here](https://docs.python.org/3/library/csv.html#csv.excel).

### fields section
> Optionally put regex to match fields by. To see what types of regex syntax
are supported, see the
[python regex library documentation](https://docs.python.org/3/library/re.html).

Example:
```ini
[fields]
IPv4 address = ^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$
```

### Example Config File
[config_example.ini](example_files/config_example.ini) (more in
[example_files/](example_files))
```ini
[defaults]
header_row_num = 0
ignored_rows = -1

[source]
file_name = example_files/example.csv
target_column(s) = Favorite Color
match_by = Social Security Number
header_row_num =
ignored_rows =

[target]
file_name = example_files/example3.csv
target_column(s) = favorite color
match_by = social security
header_row_num = 1
ignored_rows = 0,5

[output]
file_name = output.csv
unmatched_file_name =
# valid dialects: unix, excel, excel_tab
dialect = excel

[fields]
```