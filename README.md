<h1 align="center">CSVTransfer</h1>

CSVTransfer enables the transfer, filtering, and consolidation of data from an
arbitrary number of csv files into a single csv file.

## Setup

Download `csvtransfer.py`, `config_template.ini`, and optionally this `README.md` for
future reference. Next, make sure you have python 3 installed. Finally, you
need to fill out the config template as described further down in this README.
Alternatively, download and run the script `config_gen.sh` from this repo to
interactively create a config file without worrying too much about the syntax.

## Usage

Run the script by passing the path to your configuration file as the only argument.

```bash
python3 csvtransfer.py [OPTION...] CONFIG_FILE
```

> [!NOTE]
> If you are on windows, you might have to use `py` to invoke python instead

### Options

**-h**, **--help**
> Prints help message and terminates

**--debug**
> Enables diagnostic print statements

**-o, --outfile OUTPUT_FILE**
> Specify a name for the output file instead of the default output.csv or
> output.xlsx (depending on output dialect in config file)

## Config File

This script requires a configuration file to run. At minimum, the configuration
file specifies each data source and what columns to transfer from those sources
as well as the output file name and dialect. The config file fields are
[described below](#config-file-sections). The config file should follow the ini
format. To see exactly what is supported, see the [configparser
library](https://docs.python.org/3/library/configparser.html#supported-ini-file-structure)
which this script uses to parse the config file.

## Config File Generator

To make creating config files quicker and more intuitive, use the [config file
generator script](config_gen.sh) available in this repo. It will fill out the
config file for you through a series of interactive prompts.

## Config File Sections

The config file is organized into sections. Each section is described below. If
a section is optional, the section marker in square brackets does not need to
appear in the file at all. The order in which sections appear in the config
file does not matter. Order doesn't matter for keys within a section either.

### defaults section (optional)

Any key-value pairs put in this section (if included) will be put into every
source's section unless they already exist in that section.

```ini
[defaults]
header_row_num = 0
```

Above is the defaults section included in the config template. It sets the
default value of 0 for the header_row_num in each source's section. For most
sources, the headers (column names) are in the first line/row of the file (line
0), so it makes a lot of sense as a default value. The header_row_num key is
required for each source's section, but since it is given a default value it
does not have to appear in any source's section unless of course the value
needs to be overridden.

### sources section (required)

The sources section specifies the names of each data source as well as the
corresponding path to the file containing the data in key-value pairs as shown
below. Each source named in this section must have its own section in the
config file by the same name given in this section. The name of the source will
also be how it is referred to in the output data and diagnostic messages.

```ini
# keys are source names and values are paths to data
[sources]
source1_name = ./dataset/data1.csv
source2 name = data2.csv
```

The order in which the sources are listed is the order in which they are read
in and tranferred to the output. This is largely irrelevant, but is reflected
in the order of diagnostic messages when using `--debug` and select few other
places.

### source section(s) (required)

Each source named in the [sources section](#sources-section-required) must
have its own section by the same name given in the sources section exactly as
it appears there. This section has the following fields:


**header_row_num** (required)
> The number of the row (starting at 0) which contains the headers (column
> names) to use

**target_columns** (required)
> A comma separated list of the headers to pull data from

**join_by_columns** (optional)
> A comma separated list of headers from target_columns to merge/join data by.
> See [how data is joined together](#how-data-is-joined-together) for more info

**ignore_rows** (optional)
> A comma separated list of row numbers to ignore (skip during data transfer).
> Row numbers start at 0 from the top of the csv file

```ini
[source1_name]
header_row_num = 1
target_columns = id,name,email
join_by_columns = id,email
ignore_rows = 4,7

[source2 name]
# if a required field is given a value in defaults section, don't have to include it here
target_columns = employee id,first name,last name
join_by_columns = employee id
```

### source column remapping section(s) (optional)

Each source named in the [sources section](#sources-section-required) may
optionally have a section to remap column names from that source to the output.
The section name is the source name with _column_remapping appended to it. Each
key-value pair is a mapping where the key is a column name from the source and
the value is the name it should take on in the output data.

```ini
[source1_name_column_remapping]
name = first name

[source2 name_column_remapping]
employee id = id
```

### output section (required)

The output section only determines the dialect that the results should be
written in. The only options are csv and excel. If the output file name does
not have a file extension that matches the dialect, it will be added to the end
of the name given.


**dialect** (required)
> Either csv or excel

### output_filters section (optional)

If included, the output_filters section contains regular expressions to
validate data. Each key in this section should correspond to a header (column
name) in the output. The value for each key should be a regular expression
which encompasses valid data for that row. If this section is present in the
config file, a column will be added to the output which says if each row passed
every filter or not.

```ini
[output_filters]
email = ^[a-zA-Z0-9]+@[a-zA-Z0-9]+\.(com|net|org)$
id = ^[0-9]{6,}$
```

## How data is joined together

Data is joined together source by source in the order the sources are listed in
the [sources section](#sources-section-required). First, any columns that
need to be renamed according to the source's column [remapping
section](#source-column-remapping-sections-optional) are renamed. All
target_columns from the source being merged are added to the output data (empty
for now), except for the join_by_columns. If there are any columns already in
the output data by the same name as one of the target_columns, then the source
name is appended to the duplicate column name. Then for each row, one of the
following happens:


1. If there are no join_by_columns or any of the data from join_by_columns
   doesn't find a match, the row is simply appended to the output data
1. If all of the data from join_by_columns find a (single) matching row, the
   data from the other target_columns are filled in for that row

### Example Config File

[config_example.ini](example_files/config_example.ini) (more in
[example_files/](example_files))
```ini
[defaults]
header_row_num = 0

[sources]
source1 = example_files/example.csv
source3 = example_files/example3.csv

[source1]
target_columns = Favorite Color,Social Security Number,Date of birth,Employment Status
join_by_columns = Social Security Number

[source1_column_remapping]
Favorite Color = favorite color
Social Security Number = ssn
Date of birth = d.o.b
Employment Status = employed

[source3]
target_columns = social security,favorite color,d.o.b,employment status
join_by_columns = social security
header_row_num = 1
ignored_rows = 0,3

[source3_column_remapping]
social security = ssn
employment status = employed

[output]
dialect = csv
```

# License

This project is licensed under the GNU GPLv3 license which can be found in the
GitHub repo in [LICENSE.txt](LICENSE.txt).

# Feedback

Feel free to give me feedback at ericmckinney.md@gmail.com or through GitHub.
