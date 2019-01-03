#!/bin/bash
cp docs/usage_template.md usage.template
#looper --help > USAGE.temp 2>&1

for cmd in "--help"; do
	echo $cmd
	echo -e "\n\`caravel $cmd\`" > USAGE_header.temp
	echo -e '```' >> USAGE_header.temp
	caravel $cmd > USAGE.temp 2>&1
	# sed -i 's/^/\t/' USAGE.temp
	# sed -i '1s/^/\n.. code-block:: none\n\n/' USAGE.temp
	#sed -i -e "/\`looper $cmd\`/r USAGE.temp" -e '$G' usage.template  # for -in place inserts
	cat USAGE_header.temp USAGE.temp >> usage.template # to append to the end
	echo -e '```' >> usage.template
done
rm USAGE.temp
rm USAGE_header.temp
mv usage.template  docs/docs/usage.md
cat docs/docs/usage.md
#rm USAGE.temp
