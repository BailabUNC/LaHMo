import gzip
import argparse
import os

def parse_args():
    parser = argparse.ArgumentParser(description='Convert txt file to gz file.')
    parser.add_argument('-c', '--category',
                        help='The category of the file.')
    parser.add_argument('-d', '--date',
                        help='Date of the test')
    parser.add_argument('-l', '--label',
                        help='The label of the file to convert.')
    parser.add_argument('-ds', '--downsamp',
                        default=10,
                        help='Downsample ratio, default 10',
                        type=int)
    parser.add_argument('-sr', '--skiprows',
                        default=6,
                        help='Lines of data to skip from the beginning of file.',
                        type=int)
    return parser.parse_args()

def compress_gz(category, date, filename, downsamp, skiprows):
    path = os.path.join('dataset', category, date, filename)

    # sample one data point in *downsamp* consecutive data points to control gzip file size
    with open(path+'.txt', 'rb') as f_in, gzip.open(path+'.gz', 'wb') as f_out:
        lines = f_in.readlines()
        # f_out.write('\t'.join(['downsample ratio', str(downsamp)]).encode()) # NOTE: write downsample ratio to the head of output file
        for i in range(skiprows):
            f_out.write(lines[i])
        if downsamp > 1:
            for i in range(skiprows, len(lines)):
                if i % downsamp == skiprows:
                    f_out.write(lines[i])
        elif downsamp == 1:
            for i in range(skiprows, len(lines)):
                f_out.write(lines[i])
                    

def main():
    args = parse_args()
    category = args.category
    date = args.date
    label = args.label
    downsamp = args.downsamp
    skiprows = args.skiprows
    compress_gz(category, date, label, downsamp, skiprows)
    
if __name__ == '__main__':
    main()