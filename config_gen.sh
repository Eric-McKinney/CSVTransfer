#!/usr/bin/env bash

PROMPT_COLOR="\e[34m"
COLOR_END="\e[0m"

print_help() {
    cat <<-HEREDOC
	usage: ${0##*/} [--help] [FILE_NAME]

	Generate a configuration file for csvtransfer.py through a series of interactive
	prompts. Optionally provide a FILE_NAME via command line to skip the first prompt.
	HEREDOC
}

err() {
    local msg="$1"
    >&2 echo "error: $msg"
    [[ "$2" == "--fatal" ]] && exit 1
}

write_config() {
    cat > "$outfile" <<-HEREDOC
	[defaults]
	header_row_num = 0
	separator = ,

	[sources]
	$(printf "$sources_section")

	$(printf "$individual_source_sections")

	$(printf "$column_remapping_sections")

	[output]
	dialect = $dialect

	$(printf "$output_filters")
	HEREDOC
}

fancy_read() {
    local prompt="$1"
    local -n response="$2"

    local colored_prompt="$(printf "${PROMPT_COLOR}%s${COLOR_END}" "$prompt")"
    read -ep "$colored_prompt" response
}

array_to_comma_sep_list() {
    local -n arr="$1"
    local comma_sep_list=""

    comma_sep_list="${arr[0]}"

    local item
    for item in "${arr[@]:1}"
    do
        comma_sep_list+=",$item"
    done

    echo "$comma_sep_list"
}

read_target_cols() {
    local -n tcols="$1"
    local -n remappings="$2"

    local i=0
    local col=""
    local outcol=""

    while :
    do
        fancy_read "target column $((i+1)) (leave blank to move on): " col
        [[ "$col" == "" ]] && break
        fancy_read "rename column $col for output data (leave blank to keep the same): " outcol

        tcols[$i]="$col"
        [[ "$outcol" != "" ]] && remappings+="$col = $outcol\n"
        ((i++))
    done
}

choose_join_by_cols() {
    local -n tcols="$1"
    local -n join_by_cols="$2"

    echo "choose target columns to join data together by (leave blank if none):"
    local i
    for ((i = 1; i <= ${#tcols[@]}; i++))
    do
        printf "$PROMPT_COLOR[%d]$COLOR_END %s\n" "$i" "${tcols[$((i-1))]}"
    done

    local choices
    fancy_read "pick numbers from above (separate with spaces): " choices
    for choice in $choices
    do
        join_by_cols+="${tcols[$((choice - 1))]},"
    done
    
    join_by_cols="${join_by_cols%,}"
}

if [[ "$1" == "--help" ]]
then
    print_help
    exit 0
fi

if [[ $# -gt 1 ]]
then
    err "too many arguments"
    print_help
    exit 1
fi

outfile=""
if [[ $# -eq 1 ]]
then
    outfile="$1"
else
    fancy_read "config file name: " outfile
fi

fancy_read "number of data sources (csv files): " num_sources
[[ "$num_sources" =~ ^[[:digit:]]+$ ]] || err --fatal "must be a digit"

sources_section=""
individual_source_sections=""
column_remapping_sections=""
for ((i = 1; i <= num_sources; i++))
do
    fancy_read "source $i name: " sname
    fancy_read "source $i csv file: " sfile
    sources_section+="$sname = $sfile\n"

    individual_source_sections+="[$sname]\n"

    fancy_read "line number (starting from 0) of headers/column names: " sheader_rownum
    [[ "$sheader_rownum" =~ ^[[:digit:]]+$ ]] || err --fatal "must be a digit"
    [[ "$sheader_rownum" -ne 0 ]] \
        && individual_source_sections+="header_row_num = $sheader_rownum\n"

    fancy_read "separator used in csv file: " ssep
    [[ "$ssep" != "," ]] && individual_source_sections+="separator = $ssep\n"

    declare -a starget_cols=()
    sremappings="[${sname}_column_remapping]\n"
    read_target_cols starget_cols sremappings

    sjoin_by_cols=""
    choose_join_by_cols starget_cols sjoin_by_cols

    individual_source_sections+="target_columns = $(array_to_comma_sep_list starget_cols)\n"
    [[ "$sjoin_by_cols" != "" ]] && \
        individual_source_sections+="join_by_columns = $sjoin_by_cols\n"
    individual_source_sections+="\n"

    [[ "$sremappings" != "[${sname}_column_remapping]\n" ]] && \
        column_remapping_sections+="$sremappings\n"
done

dialects=("csv" "excel")
echo "choose an output dialect"
printf "$PROMPT_COLOR[1]$END_COLOR csv\n"
printf "$PROMPT_COLOR[2]$END_COLOR excel\n"
fancy_read "pick a number from above: " dialect_choice
[[ "$dialect_choice" =~ ^1|2$ ]] || dialect_choice=1
dialect="${dialects[$((dialect_choice-1))]}"

output_filters="[output_filters]\n"
echo "optionally provide regex to validate data by column (flag data that doesn't match)"
while :
do
    fancy_read "column name as it would appear in the output (leave blank to skip): " ofcname
    [[ "$ofcname" == "" ]] && break
    fancy_read "regex for column $ofcname: " ofregex

    output_filters+="$ofcname = $ofregex\n"
done

write_config
