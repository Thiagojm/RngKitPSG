import os
import glob
import pathlib
from contextlib import ExitStack

os.chdir(pathlib.Path(r"C:\Users\tjmpl\Documents\Projetos\RngKitPSG\1-SavedFiles"))

extension = 'csv'
all_filenames = [i for i in glob.glob('*.{}'.format(extension))]
print(all_filenames)

# for i in all_filenames:
#     print(i)

with ExitStack() as stack:
    files = [stack.enter_context(open(fname)) for fname in all_filenames]
    with open("concat_csv.csv", "a") as f:
        for file in files:
            for line in file:
                f.write(line)
                
