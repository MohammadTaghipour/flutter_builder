import os
import re
from pathlib import Path

class AndroidRenameSteps:
    PATH_BUILD_GRADLE = 'android/app/build.gradle'
    PATH_MANIFEST = 'android/app/src/main/AndroidManifest.xml'
    PATH_MANIFEST_DEBUG = 'android/app/src/debug/AndroidManifest.xml'
    PATH_MANIFEST_PROFILE = 'android/app/src/profile/AndroidManifest.xml'
    PATH_ACTIVITY = 'android/app/src/main/'

    def __init__(self, new_package_name, project_location):
        self.new_package_name = new_package_name
        self.project_location = project_location
        self.old_package_name = None
        self.PATH_BUILD_GRADLE = project_location +'/'+ self.PATH_BUILD_GRADLE
        self.PATH_MANIFEST = project_location +'/'+ self.PATH_MANIFEST
        self.PATH_MANIFEST_DEBUG = project_location +'/'+ self.PATH_MANIFEST_DEBUG
        self.PATH_MANIFEST_PROFILE = project_location +'/'+ self.PATH_MANIFEST_PROFILE
        self.PATH_ACTIVITY = project_location +'/'+ self.PATH_ACTIVITY

    async def process(self):
        print("Running for android")
        if not Path(self.PATH_BUILD_GRADLE).exists():
            print('ERROR:: build.gradle file not found, Check if you have a correct android directory present in your project'
                  '\n\nrun " flutter create . " to regenerate missing files.')
            return

        contents = await self.read_file_as_string(self.PATH_BUILD_GRADLE)

        match = re.search(r'applicationId\s*=?\s*"(.*)"', contents)
        if match is None:
            print('ERROR:: applicationId not found in build.gradle file, Please file an issue on github with {} file attached.'.format(self.PATH_BUILD_GRADLE))
            return

        self.old_package_name = match.group(1)
        print("Old Package Name:", self.old_package_name)

        print('Updating build.gradle File')
        await self._replace(self.PATH_BUILD_GRADLE)

        m_text = f'package="{self.new_package_name}">'
        m_regex = r'(package=.*)'

        print('Updating Main Manifest file')
        await self.replace_in_file_regex(self.PATH_MANIFEST, m_regex, m_text)

        print('Updating Debug Manifest file')
        await self.replace_in_file_regex(self.PATH_MANIFEST_DEBUG, m_regex, m_text)

        print('Updating Profile Manifest file')
        await self.replace_in_file_regex(self.PATH_MANIFEST_PROFILE, m_regex, m_text)

        await self.update_main_activity()
        print('Finished updating android package name')

    async def update_main_activity(self):
        path = await self.find_main_activity(type='java')
        if path:
            await self.process_main_activity(path, 'java')

        path = await self.find_main_activity(type='kotlin')
        if path:
            await self.process_main_activity(path, 'kotlin')

    async def process_main_activity(self, path, type):
        extension = 'java' if type == 'java' else 'kt'
        print(f'Project is using {type}')
        print(f'Updating MainActivity.{extension}')
        await self.replace_in_file_regex(path, r'^(package (?:\.|\w)+)', f"package {self.new_package_name}")

        new_package_path = self.new_package_name.replace('.', '/')
        new_path = os.path.join(self.PATH_ACTIVITY, type, new_package_path)

        print('Creating New Directory Structure')
        os.makedirs(new_path, exist_ok=True)
        new_activity_path = os.path.join(new_path, f'MainActivity.{extension}')
        os.rename(path, new_activity_path)

        print('Deleting old directories')
        await self.delete_empty_dirs(type)

    async def _replace(self, path):
        await self.replace_in_file(path, self.old_package_name, self.new_package_name)

    async def delete_empty_dirs(self, type):
        dirs = await self.dir_contents(Path(self.PATH_ACTIVITY + type))
        for dir in reversed(dirs):
            if dir.is_dir() and not list(dir.iterdir()):
                dir.rmdir()

    async def find_main_activity(self, type='java'):
        files = await self.dir_contents(Path(self.PATH_ACTIVITY + type))
        extension = 'java' if type == 'java' else 'kt'
        for item in files:
            if item.is_file() and item.name == f'MainActivity.{extension}':
                return item
        return None

    async def dir_contents(self, dir):
        if not dir.exists():
            return []
        return [f for f in dir.glob('**/*')]

    async def read_file_as_string(self, path):
        with open(path, 'r') as file:
            return file.read()

    async def replace_in_file(self, path, old, new):
        with open(path, 'r') as file:
            content = file.read()
        content = content.replace(old, new)
        with open(path, 'w') as file:
            file.write(content)

    async def replace_in_file_regex(self, path, pattern, replacement):
        with open(path, 'r') as file:
            content = file.read()
        content = re.sub(pattern, replacement, content)
        with open(path, 'w') as file:
            file.write(content)

