import yaml
from pathlib import Path
import re
import sys
import time
import os
import asyncio
from android_rename_steps import AndroidRenameSteps
from ios_rename_steps import IosRenameSteps
import subprocess

async def is_folder_path(path):
    return Path(path).is_dir()

async def is_flutter_project(folder_path):
    path = Path(folder_path)
    return (
        (path / "pubspec.yaml").is_file() and
        (path / "lib").is_dir()
    )

async def print_progress_bar(iteration, total, length=40):
    percent = (iteration / total)
    filled_length = int(length * percent)
    bar = '█' * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r|{bar}| {percent:.2%}')
    sys.stdout.flush()
    if iteration == total:
        print('\n')

async def print_project_info(path):
    try:
        path = Path(path)
        pubspec_path = path / "pubspec.yaml"
        android_build_path = path / "android/app/build.gradle"

        if not pubspec_path.is_file():
            print("This folder is not a Flutter project.")
            return

        with open(pubspec_path, "r") as file:
            try:
                pubspec_data = yaml.safe_load(file)
            except yaml.YAMLError as e:
                print("Error parsing pubspec.yaml:", e)
                return

        project_name = pubspec_data.get("name", "Unknown")
        project_description = pubspec_data.get("description", "No description provided.")
        project_version = pubspec_data.get("version", "No version specified.")
    
        total = 100
        for i in range(total + 1):
            await print_progress_bar(i, total)
            time.sleep(0.02)
        
        print(f"Project Name: {project_name}")
        print(f"Description: {project_description}")
        print(f"Version: {project_version}")
        if android_build_path.is_file():
            with open(android_build_path, "r") as file:
                content = file.read()
                name_space = re.search(r'namespace\s*=\s*"([^"]+)"', content)
                package_name_match = re.search(r'applicationId\s*=\s*"([^"]+)"', content)
                if name_space:
                    print(f"Package name: {name_space.group(1)}")
                elif package_name_match:
                    print(f"Package name: {package_name_match.group(1)}")
        return project_version
    except Exception:
        print("An Error occurred when getting project info!")

async def find_file_in_directory(directory, filename):
    path = Path(directory)
    for file in path.rglob(filename):
        return str(file)
    return None


async def change_app_version(app_version, target_os, target_android_device, project_location):
    pattern = r"^\d+(\.\d+){0,2}([-+][a-zA-Z0-9]+)?$"
    if app_version == None:
        print('version name did not change')
        return
    if len(app_version.strip()) == 0:
        print('version name did not change')
        return    
    app_build_version = await find_file_in_directory(project_location, 'app_build_setting.dart')
    yaml_version = await find_file_in_directory(project_location, 'pubspec.yaml')
    if app_build_version == None and yaml_version == None:
        print('Version did not change! (File not found)')
        return
    if app_build_version is not None:
        with open(app_build_version, 'r') as file:
            content = file.read()
        pattern = r"(const\s+String\s+version\s+=\s+)'([^']+)'(\s*;)"
        if target_os.lower() == 'android':
            replacement = 'const String version = \'{}+{}\';'.format(app_version, target_android_device)
        else:
            replacement = 'const String version = \'{}\';'.format(app_version)
        new_content = re.sub(pattern, replacement, content)
        with open(app_build_version, 'w') as file:
            file.write(new_content)
    if yaml_version is not None:
        with open(yaml_version, 'r') as file:
            content = file.read()
        pattern = r"(version:\s*.*)" 
        replacement = 'version: {}'.format(app_version)
        new_content = content = re.sub(pattern,  replacement, content)
        with open(yaml_version, 'w') as file:
            file.write(new_content)
    print('version changed to: ' + app_version)
    

async def change_app_package_name(package_name, project_location):
    if package_name == None:
        print('package name did not change')
        return
    if len(package_name.strip()) == 0:
        print('package name did not change')
        return
    await AndroidRenameSteps(package_name, project_location).process()
    await IosRenameSteps(package_name, project_location).process()

def show_owner_info():
    os.system("mode con: cols=100 lines=50")
    logo = """
  ____                                _   _           
 |  _ \ _____      _____ _ __ ___  __| | | |__  _   _ 
 | |_) / _ \ \ /\ / / _ \ '__/ _ \/ _` | | '_ \| | | |
 |  __/ (_) \ V  V /  __/ | |  __/ (_| | | |_) | |_| |
 |_|___\___/ \_/\_/ \___|_|  \___|\__,_| |_.__/ \__, |
 |_   _|_ _  __ _| |__ (_)_ __   ___  _   _ _ __|___/ 
   | |/ _` |/ _` | '_ \| | '_ \ / _ \| | | | '__|     
   | | (_| | (_| | | | | | |_) | (_) | |_| | |        
   |_|\__,_|\__, |_| |_|_| .__/ \___/ \__,_|_|        
            |___/        |_|                          
"""
    print(logo)


async def get_supported_android_devices(project_location):
    app_build_version = await find_file_in_directory(project_location, 'app_build_setting.dart')
    if app_build_version == None:
        return ['Mobile']
    else:
        return ['Mobile, ', 'POS']


async def get_supported_plaltforms(project_location):
    path = Path(project_location)
    supported_platforms = []
    os_name = os.name
    if os_name == 'nt':
        os_name = 'Windows'
    elif os_name == 'posix':
        if os.uname().sysname == 'Darwin':
            os_name = 'macOS'
        else:
            os_name = 'Linux'
    else:
        print(f"Your os is not supported")
        return
    if (path / "android").is_dir():
        supported_platforms.append("Android")
    if (path / "ios").is_dir() and os_name == 'macOS':
        supported_platforms.append("iOS")
    if (path / "web").is_dir():
        supported_platforms.append("Web")
    if (path / "windows").is_dir():
        supported_platforms.append("Windows")
    if (path / "macos").is_dir() and os_name == 'macOS':
        supported_platforms.append("MacOS")
    if (path / "linux").is_dir() and os_name == 'Linux':
        supported_platforms.append("Linux")
    return supported_platforms

async def build_app(target_os, project_location):
    if target_os == None:
        print('release cancelled')
        return
    if len(target_os.strip()) == 0:
        print('release cancelled')
        return
    target_os = target_os.lower()
    if 'android' in target_os:
        release_type = 'apk'
    elif 'ios' in target_os:
        release_type = 'ios'
    elif 'web' in target_os:
        release_type = 'web'
    elif 'windows' in target_os:
        release_type = 'windows'
    elif 'mac' in target_os:
        release_type = 'macos'
    elif 'linux' in target_os:
        release_type = 'linux'
    else:
        print('release cancelled')
        print('target os is not supported')
        return
    os.chdir(project_location)
    subprocess.run(["powershell", "flutter build -v {} --release".format(release_type)], shell=True)

async def loading_animation():
    loading_text = "Loading"
    dots = 3
    now = time.time()
    enabled = True
    while enabled:
        for i in range(dots + 1):
            sys.stdout.write("\r" + loading_text + "." * i + " " * (dots - i))
            sys.stdout.flush()
            time.sleep(0.2)
        enabled = ((time.time() - now) < 2)

async def main():
    try:
        show_owner_info()
        project_location = input('Enter path/to/your/project: ')
        if await is_folder_path(project_location):
            if await is_flutter_project(project_location):
                await loading_animation()
                current_version = await print_project_info(project_location)
                print('-'*50)
                print('Enter values for release')
                print('--- Press Enter for skip ---')
                version_name = input('New version (eg. 1.0.0+1): ')
                version_name = current_version if version_name is None else version_name
                package_name = input('New package name: ')
                supported_platforms = await get_supported_plaltforms(project_location)
                supported_devices = await get_supported_android_devices(project_location)
                supported_platforms = [item if index == len(supported_platforms) -1 else  item + ', ' for index,item in enumerate(supported_platforms)]
                target_os = input('Choose release os ({}): '.format(''.join(supported_platforms)))
                target_android_device = 'Mobile'
                if target_os.lower() == 'android' and len(supported_devices) > 1:
                    target_android_device = input('Choose target device ({}): '.format(''.join(supported_devices)))
                print('-'*50)
                await change_app_version(version_name, target_os, target_android_device, project_location)
                await change_app_package_name(package_name, project_location)
                await build_app(target_os, project_location)
                print('-'*50)
                print('Proccess finised')
                print('Press enter to exit')
                ex = input()
                exit()
            else:
                print('Not a Flutter project!')
        else:
            print('Not a valid path!')
            exit()
    except Exception:
        print("An Error occurred")
        
if __name__ == "__main__":
    asyncio.run(main())
