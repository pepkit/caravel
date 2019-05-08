#!/usr/bin/env python

"""
Counts reads.
"""

__author__ = "Nathan Sheffield"
__email__ = "nathan@code.databio.org"
__license__ = "GPL3"
__version__ = "0.1"

from argparse import ArgumentParser
import os
import pypiper
import csv
from time import sleep

parser = ArgumentParser(description="A pipeline to count the number of reads and file size. Accepts BAM, fastq, "
                                    "or fastq.gz files.")
parser = pypiper.add_pypiper_args(parser, groups=["pypiper", "common", "ngs", "looper"],
                                    args=["output-parent", "config"],
                                    required=['sample-name', 'output-parent'])
parser.add_argument("--sleep", dest="sleep", default=None, help="How long to sleep")
args = parser.parse_args()
if not args.input or not args.output_parent:
    parser.print_help()
    raise SystemExit

if args.single_or_paired == "paired":
    args.paired_end = True
else:
    args.paired_end = False

outfolder = os.path.abspath(os.path.join(args.output_parent, args.sample_name))

pm = pypiper.PipelineManager(name="count", outfolder=outfolder, args=args)
ngstk = pypiper.NGSTk(pm=pm)
raw_folder = os.path.join(outfolder, "raw/")
fastq_folder = os.path.join(outfolder, "fastq/")
pm.timestamp("### Merge/link and fastq conversion: ")
local_input_files = ngstk.merge_or_link([args.input, args.input2], raw_folder, args.sample_name)
cmd, out_fastq_pre, unaligned_fastq = ngstk.input_to_fastq(local_input_files, args.sample_name, args.paired_end,
                                                           fastq_folder)
size_mb = ngstk.get_file_size(local_input_files)
pm.report_result("File_mb", size_mb)
if args.sleep is not None:
    sleep_val = 60*float(args.sleep)
    pm.timestamp("### Sleeping: {}s".format(sleep_val))
    sleep(sleep_val)
n_input_files = len(list(filter(bool, local_input_files)))
raw_reads = sum([int(ngstk.count_reads(input_file, args.paired_end)) for input_file in local_input_files])/n_input_files
pm.report_result("Raw_reads", str(raw_reads))
pm.timestamp("### Saving result")
outfile = os.path.join(outfolder, args.sample_name + '_results.csv')
with open(outfile, mode='w') as f:
    fwriter = csv.writer(f)
    fwriter.writerow(['raw reads', str(raw_reads)])
    fwriter.writerow(['file size', str(size_mb)])
pm.report_object("results CSV", os.path.basename(outfile), anchor_text="results CSV")
pm.stop_pipeline()
