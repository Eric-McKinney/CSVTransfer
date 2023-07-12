# CSVTransfer

## Project Description

This purpose of this project is to enable the transfer of select data from an 
arbitrary number of csv files into a new file. Data can be used to "match by" 
effectively merging data which shares at least one match_by field with other 
data. Regex filters can be applied to csv fields/columns. The data that does 
not match these filters and other data considered unmatched can be output to 
a file.

## Setup
Download `main.py`, `config_template.ini`, and optionally this `README.md` for 
future reference (I don't have anything fancy set up you have to do it 
through GitHub lol). Once you've done that, make sure you have python 
installed. After that you should be good to go.

## Usage
For this script to be able to see and read the csv files they must be in the
same directory this script is invoked in or in a subdirectory. Once you have 
your csvs where you want them, fill out the config file (more on that below).
In the command prompt or shell (in the same directory as main.py) do 
`py main.py` or `python3 main.py` depending on your environment. Of course if
you want to you can use the absolute path of the script to execute it elsewhere
like so `python3 /absolute/path/to/main.py` or the same thing using `py` which
depends on your system.

### Options
Currently, the only options are `-h`, `--help`, `--debug`, and `--strict`.

**-h**, **--help**
> Prints help message and terminates.

**--debug**
> Enables debug print statements.

**--strict**
> If data after the first source does not match at least one of the match_by
fields then the data is considered unmatched as opposed to being appended to the
output in its own row.

## Config File
By default, the script uses `config_template.ini` for configuration. If you 
want to use a config file by a different name, open `main.py` and change 
the `CONFIG_FILE_NAME` variable accordingly. The `config_template.ini` file 
has a few bits filled out already. Fill in the rest as described below. 

## Config File Sections

The config file is organized into sections: defaults, sources, output, 
source_rules, and field_rules as well as some you will have to add.

### defaults section

The defaults section contains default values 
for the sections you will add for each source. These are filled out for you 
in the template. You can add more, but you will need to make sure to add them
to the section for each source (with or without a value assigned to it).

### sources section

The sources section is where you list the various csv files to draw data from.
Put the name of the source (whatever you want to call it) and assign it the
path to the csv file (the path can be relative). The order in which you list
sources determines their priority where the first source you put is the highest
priority and the last source is the lowest priority. Sources are parsed and
transferred in order of their priority. If data between sources collides (two
sources have different values for the same row, column), then the higher priority
source's data is put in the output. This is because sources whose data is matched
to an existing row in the output will only fill in empty fields, so the first
value used for a cell in the output will not be replaced. Once you have listed
all sources you plan to use as well as the paths to the csv files, you need to
make a section for each source by the same name you gave in this section.

### source section(s)

Each source you plan to use and have listed in the sources section need a
section to specify how they should be handled. The section name should be the
same as the name you put in the sources section. In this section there needs
to be the following fields: target_column(s), column_name(s), match_by,
match_by_name(s), header_row_num, and ignored_row(s). Descriptions for what each
of these fields entails can be found below in 
[Config File Fields](#config-file-fields). All of these fields need
values unless they appear in (and have values in) the defaults section.

### output section

The output section is mostly just to name the output file, but you can also 
change the dialect to write output csvs in. Excel is the default and is what 
I would recommend. More about dialects below. You can also optionally give 
the name for a file to dump data that could not be matched. Unmatched data will
only be dumped to that file if you give it a name.

### source rules section(s)

For each source you may add a section to declare rules specific to that source
to be processed after data transfer. A source's rule section must be named the
same as the source name followed by _rules. For example, for a source named
rock_data the rules section would be named rock_data_rules. In this section you
may declare up to one rule per header in the output to apply to data under said 
header. Rules are regex patterns for data to be validated by. If data does not 
match the regex provided, it will be documented in the "Source rule(s) broken" 
column. If data matches the regex, "None" will be put in this column instead.

### field_rules section

The field_rules section is a place where you can specify formats for data to be 
validated against using regex. This is entirely optional. Data that does not 
match the given regex for a given header will not be transferred and counts 
towards the unmatched data.

### source rules vs field_rules

You may notice that the source rules section bears a lot of similarities to the 
field_rules section. The key differences between the two are that field_rules 
are applied before data is transferred, field_rules do not discriminate between 
sources, and data that does not match field_rules is not transferred. Source
rules are applied after data is transferred, source rules are specific to one
source, and data that does not match source rules stays in the output. In this 
way, source rules function much more as a check to make sure that data has the 
right format or that certain fields contain words or phrases. Meanwhile, 
field_rules functions more as a filter applied to data being transferred to get
rid of bad data.

## Config File Fields

### defaults section
**header_row_num**
> The number of the row (starting at 0) which contains the headers you want to
use.

**ignored_row(s)**
> A comma separated list of numbers of rows to ignore while parsing, 
transferring data, and putting data in the output file. Any negative value or
out of bounds value effectively means nothing. In the template this value is
defaulted to -1 (which is a filler value), so no rows are ignored. The order 
of the numbers does not matter. Data ignored this way does not contribute to 
the unmatched data.

---
### section for each source

**target_column(s)**
> A comma separated list of the headers whose columns should be used in the data
transfer.

**column_name(s)**
> A comma separated list of the headers to be used in the output. The headers
from the target_column(s) section are matched to these names based on the order
they appear. If there are less column_name(s) than target_column(s) then the
extra target_column(s) assume the same name in the output. Extra column_name(s)
are not used.

**match_by**
> Functions in the same way that target_column(s) does, but headers listed here
are also used to match data by when transferring. A match is attempted among data
in the output at the time of transfer (data already transferred not including the
current source). If a match is found, then data being transferred will only fill
in empty fields in that row. If a match is not found, then data will be appended
to the output unless `--strict` is used, in which case the data is considered
unmatched. Headers listed in both target_column(s) and here are only put in the
output once, but it's best to avoid doing this.

**match_by_name(s)**
> Functions in the same way as column_name(s), but for headers in match_by

**header_row_num**
> Same as in the defaults section, but if a value is provided here it will
override the value given in defaults.

**ignored_row(s)**
> See above.

---
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
info can be found in the
[python csv library](https://docs.python.org/3/library/csv.html#csv.excel).

---
### source rules section(s)
> Optionally provide regex to match fields from individual sources by. To see 
what types of regex syntax are supported, see the
[python regex library documentation](https://docs.python.org/3/library/re.html).
To create a rule, put a header that will appear in the output and assign it
the regex you want data under that header to match.

Example:
```ini
[example_source_name_rules]
# Rule states that goldfish names in the output from example_source_name should 
# not be (or contain) Jerry or jerry
goldfish names = ^((?![Jj]erry).)*$

# Rule states that water quality in the output from example_source_name should
# be in the range 1/10 to 10/10 (inclusive)
water quality = ^([1-9]|10)\/10$

# Rule states that fish bowl serial numbers in the output from this source should
# contain the number 4
fish bowl serial number = 4
```

---
### field_rules section
> Optionally put regex to filter fields by. To create a rule, put the header that 
will appear in the output and assign it the regex you want data to match. Data 
that does not match this regex will not be transferred and will count towards 
the unmatched data.

Example:
```ini
[field_rules]
# The following rule defines the format for data in the IPv4 address column
IPv4 address = ^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$
```

---
### Example Config File
[config_example.ini](example_files/config_example.ini) (more in
[example_files/](example_files))
```ini
[defaults]
header_row_num = 0
ignored_row(s) = -1

[sources]
source1 = example_files/example.csv
source3 = example_files/example3.csv

[source1]
target_column(s) = Favorite Color
column_name(s) = favorite color
match_by = Social Security Number
match_by_name(s) = social security
header_row_num =
ignored_row(s) =

[source1_rules]
social security = 5

[source3]
target_column(s) = favorite color
column_name(s) =
match_by = social security
match_by_name(s) =
header_row_num = 1
ignored_row(s) = 0,5

[source3_rules]
favorite color = a

[output]
file_name = test_outputs/output.csv
unmatched_file_name =
# valid dialects: unix, excel, excel_tab
dialect = excel

[field_rules]
```

# Feedback

Feel free to give me feedback at ericmckinney@gmail.com or through GitHub.
I'm always looking to improve and learn new things.