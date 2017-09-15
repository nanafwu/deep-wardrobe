import csv


def write_tsv(rows, file_path):
    print('Writing to TSV ', file_path)
    with open(file_path, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        for row in rows:
            writer.writerow(row)
            f.flush()
