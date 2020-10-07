#!/usr/bin/env python3

"""
Example pipeline which counts reads, sleeps and reports the reads count, file size and time slept
"""

from argparse import ArgumentParser
import os
import pypiper
import csv

parser = ArgumentParser(description="A pipeline to count the number of lines, file sizes and line lengts distribution.")
parser = pypiper.add_pypiper_args(parser, groups=["pypiper", "looper"])
parser.add_argument("-s", "--sleep", default=None, help="How long to sleep")
parser.add_argument("-i", "--input-file", help="Input file path")
parser.add_argument("-o", "--sample-output-dir", help="Parent output directory path")
args = parser.parse_args()

output_plot_png = os.path.join(args.sample_output_dir, "line_length_distr_plot.pdf.png")
output_plot = os.path.join(args.sample_output_dir, "line_length_distr_plot.pdf")
hist_plotter_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plotHist.R")
sleep_val = float(args.sleep) if args.sleep is not None else 0
distr_output = os.path.join(args.sample_output_dir, "line_lengths_distribution.txt")
pm = pypiper.PipelineManager(name="caravel_demo", outfolder=args.sample_output_dir, args=args)
pm.timestamp("### File size calculation: ")
file_size_cmd = f"wc -c {args.input_file} | awk '{{print $1}}'"
size_kb = int(pm.checkprint(file_size_cmd, shell=True))/1000
pm.report_result("File size", size_kb)

pm.timestamp("### Lines number calculation: ")
num_lines_cmd = f"wc -l {args.input_file} | sed -E 's/^[[:space:]]+//' | cut -f1 -d' '"
num_lines = pm.checkprint(num_lines_cmd, shell=True)
pm.report_result("Number of lines", num_lines)

pm.timestamp("### Saving CSV with lines count and file sizes")
outfile = os.path.join(args.sample_output_dir, 'results.csv')
with open(outfile, mode='w') as f:
    fwriter = csv.writer(f)
    fwriter.writerow(['lines count', str(num_lines)])
    fwriter.writerow(['file size', str(size_kb)])
pm.report_object("results CSV", os.path.basename(outfile), anchor_text="results CSV")

pm.timestamp(f"### Sleeping: {sleep_val}s")
pm.run("sleep " + str(sleep_val), shell=True, lock_name="test")
time_slept = sleep_val if args.sleep is not None else 0
pm.report_result("Time slept", sleep_val)

pm.timestamp("### Line lengths distribution calculation: ")
line_length_dist_cmd = f"awk '{{print length}}' {args.input_file} | uniq > {distr_output}"
pm.run(line_length_dist_cmd, target=distr_output)

pm.timestamp("### Line lengths distribution plotting: ")
plot_line_dist_cmd = f"Rscript {hist_plotter_path} {distr_output} {output_plot}"
pm.run(plot_line_dist_cmd, target=output_plot, shell=True)
pm.report_object("Line length distribution plot", output_plot, anchor_image=output_plot_png)

pm.stop_pipeline()