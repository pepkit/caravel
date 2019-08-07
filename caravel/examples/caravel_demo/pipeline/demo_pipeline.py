#!/usr/bin/env python3

"""
Example pipepline which counts reads, sleeps and reports the reads count, file size and time slept
"""

from argparse import ArgumentParser
import os
import pypiper
import csv

parser = ArgumentParser(description="A pipeline to count the number of lines, file sizes and line lengts distribution.")
parser = pypiper.add_pypiper_args(parser, groups=["pypiper", "common", "looper"], args=["output-parent", "config"],
                                  required=['sample-name'])
parser.add_argument("--sleep", dest="sleep", default=None, help="How long to sleep")
args = parser.parse_args()
if not args.input or not args.output_parent:
    parser.print_help()
    raise SystemExit

outfolder = os.path.abspath(os.path.join(args.output_parent, args.sample_name))

input_file = args.input[0]
output_plot = os.path.join(outfolder, "line_length_distr_plot.png")
hist_plotter = "plotHist.R"
hist_plotter_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), hist_plotter)
sleep_val = 60*float(args.sleep) if args.sleep is not None else 0

distr_output = os.path.join(outfolder, "line_lengths_distribution.txt")
pm = pypiper.PipelineManager(name="caravel_demo", outfolder=outfolder, args=args)

pm.timestamp("### File size calculation: ")
file_size_cmd = "wc -c {} | awk '{{print $1}}'".format(input_file)
size_kb = int(pm.checkprint(file_size_cmd, shell=True))/1000
pm.report_result("File size", size_kb)

pm.timestamp("### Lines number calculation: ")
num_lines_cmd = "wc -l {input} | sed -E 's/^[[:space:]]+//' | cut -f1 -d' '".format(input=input_file)
num_lines = pm.checkprint(num_lines_cmd, shell=True)
pm.report_result("Number of lines", num_lines)

pm.timestamp("### Saving CSV with lines count and file sizes")
outfile = os.path.join(outfolder, args.sample_name + '_results.csv')
with open(outfile, mode='w') as f:
    fwriter = csv.writer(f)
    fwriter.writerow(['lines count', str(num_lines)])
    fwriter.writerow(['file size', str(size_kb)])
pm.report_object("results CSV", os.path.basename(outfile), anchor_text="results CSV")

pm.timestamp("### Sleeping: {}s".format(sleep_val))
pm.run("sleep " + str(sleep_val), shell=True, lock_name="test")
time_slept = sleep_val if args.sleep is not None else 0
pm.report_result("Time slept", sleep_val)

pm.timestamp("### Line lengths distribution calculation: ")
line_length_dist_cmd = "awk '{{print length}}' {input} | uniq > {distr_output}".format(input=input_file,
                                                                                     distr_output=distr_output)
pm.run(line_length_dist_cmd, target=distr_output)

pm.timestamp("### Line lengths distribution plotting: ")
plot_line_dist_cmd = "Rscript {rscript} {distr_output} {plot_path}".format(rscript=hist_plotter_path, distr_output=distr_output, plot_path=output_plot)
pm.run(plot_line_dist_cmd, target=output_plot, shell=True)
pm.report_object("Line length distribution plot", output_plot, anchor_image=output_plot)

pm.stop_pipeline()