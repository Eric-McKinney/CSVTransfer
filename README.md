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
names and the target column(s) and the column to match by for the source file 
and target file. All fields names shown in the template should be present even
if empty otherwise a `KeyError` will occur. In the command prompt or shell 
(in the same directory as main.py) do `py main.py`.

### Options
Currently, the only options are `-h`, `--help`, and `--debug`.

**-h**, **--help**
> Prints help message and terminates.

**--debug**
> Enables debug print statements.

## Config File
You should have downloaded the `config_template.ini` file. By default, the
script uses this file for configuration. If you want to use a config file by
a different name, open `main.py` and change the `CONFIG_FILE_NAME` variable 
accordingly. `config_template.ini` has a few things filled in for you, but 
the rest is up to you to put in what you want. If you don't, you'll be 
prompted when you run `main.py` for the variables that are necessary for 
the script to do what it needs to do, and they will be taken via stdin. Values
taken this way will not be written to the config file.

The config file has three sections: default, source, and target. The default
section contains general settings and default values for other sections. These
are filled out for you in the template. The other sections are to fine tune how 
the source file and target file are handled. The only fields that are necessary 
for the script are the "file_name", "target_column(s)", and "match_by" fields. 
Fill these in otherwise you will have to provide them via stdin.

### Config File Fields

**header_row_num**
> The number of the row (starting at 0) which contains the headers you want to
use.

**ignored_rows**
> A comma separated list of numbers of rows to ignore while parsing, 
transferring data, and putting data in the output file. Any negative value or
out of bounds value effectively means nothing. The order of the numbers does
not matter.

**output_file_name**
> As the name suggests, it is the name of the output file. If this collides with
a file in the same directory as the script, you will be prompted with a choice of
whether you want to overwrite said file.

**output_dialect**
> The dialect to write the output csv file in. Valid dialects include unix,
excel, and excel_tab. The default and the one you probably want is excel. The
dialect only determines things like what to quote, line terminator, etc. More
info can be found [here](https://docs.python.org/3/library/csv.html#csv.excel).

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

### Example Config File
[config_example.ini](example_files/config_example.ini)
```ini
[DEFAULT]
header_row_num = 0
ignored_rows = -1
output_file_name = output.csv
# valid dialects: unix, excel, excel_tab
output_dialect = excel

[source]
file_name = example_files/example.csv
header_row_num =
ignored_rows =
target_column(s) = Favorite Color
match_by = Social Security Number

[target]
file_name = example_files/example3.csv
header_row_num = 1
ignored_rows = 0,5
target_column(s) = favorite color
match_by = social security
```