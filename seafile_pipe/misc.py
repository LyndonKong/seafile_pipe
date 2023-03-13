import os


def get_ignore_lst(file: str = "./.gitignore") -> str:
    ignore_lst = []
    if os.path.exists(file):
        with open(file, "r") as f:
            lines = f.readlines()
            for line in lines:
                if (not line.startswith("#")) and (not line.startswith("\n")):
                    ignore_lst.append(line.strip())
    return ignore_lst
