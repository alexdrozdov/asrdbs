#!/bin/bash

worddb_file=$1
build_dir=$2
output_dir=$3
limit=$4

if [ -z "${output_dir}" ] ; then
    echo "<worddb file> <build_dir> <output_dir> required" 1>&2
    exit 1
fi

if [[ -n $limit  ]] ; then
    limit="limit ${limit}"
fi

parts_of_speech="noun adjective verb participal union particle numeral pronoun adverb preposition inp"

out_pattern="primaries_"
tmp_dump_file="${build_dir}/primaries.dmp"

echo "Exporting primaries dump to ${tmp_dump_file}..."
sqlite3 -csv ${worddb_file} "select * from primaries ${limit};" > ${tmp_dump_file}
echo "Dump complete, counting lines..."
total_line_count=$(wc -l ${tmp_dump_file} | cut -f 1 -d' ')
echo "Found ${total_line_count} lines"

if [ ! -e ${output_dir} ] ; then
    echo "Creating dir ${output_dir}..."
    mkdir -p ${output_dir}
fi

for pos in $parts_of_speech
do
    dst_file="${output_dir}/${out_pattern}${pos}"
    echo "Select and sort ${pos} from dump to ${dst_file}..."
    cat ${tmp_dump_file} | grep ",${pos}," | sort -nr -t, -k4 > $dst_file 
done

exit 0

