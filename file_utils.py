import os
import re
from pathlib import Path

async def replace_in_file(path, old_package, new_package):
    contents = await read_file_as_string(path)
    if contents is None:
        print(f'ERROR:: file at {path} not found')
        return
    contents = contents.replace(old_package, new_package)
    await write_file_from_string(path, contents)

async def replace_in_file_regex(path, regex, replacement):
    contents = await read_file_as_string(path)
    if contents is None:
        print(f'ERROR:: file at {path} not found')
        return
    contents = re.sub(regex, replacement, contents)
    await write_file_from_string(path, contents)

async def read_file_as_string(path):
    file_path = Path(path)
    if file_path.exists():
        contents = await file_path.read_text()
        return contents
    return None

async def write_file_from_string(path, contents):
    file_path = Path(path)
    await file_path.write_text(contents)

async def delete_old_directories(lang, old_package, base_path):
    dir_list = old_package.split('.')
    reversed_dirs = dir_list[::-1]  # Reverse the list

    for i in range(len(reversed_dirs)):
        path = f'{base_path}/{lang}/' + '/'.join(dir_list)

        if Path(path).exists() and not any(Path(path).iterdir()):  # Check if the directory is empty
            os.rmdir(path)  # Remove empty directory
        dir_list.pop()  # Remove the last element to move up the directory tree
