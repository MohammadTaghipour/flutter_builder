import re
from pathlib import Path

class IosRenameSteps:
    PATH_PROJECT_FILE = 'ios/Runner.xcodeproj/project.pbxproj'

    def __init__(self, new_package_name, project_location):
        self.new_package_name = new_package_name
        self.old_package_name = None
        self.PATH_PROJECT_FILE = project_location + '/' +  self.PATH_PROJECT_FILE

    async def process(self):
        print("Running for ios")
        
        if not Path(self.PATH_PROJECT_FILE).exists():
            print(
                'ERROR:: project.pbxproj file not found. Check if you have a correct ios directory present in your project'
                '\n\nrun "flutter create ." to regenerate missing files.'
            )
            return
        
        contents = await self.read_file_as_string(self.PATH_PROJECT_FILE)

        match = re.search(r'PRODUCT_BUNDLE_IDENTIFIER\s*=\s*(.*);', contents)
        if match is None:
            print(
                f'ERROR:: Bundle Identifier not found in {self.PATH_PROJECT_FILE}, '
                'please file an issue on GitHub with the file attached.'
            )
            return
        
        self.old_package_name = match.group(1).strip()

        print("Old Package Name:", self.old_package_name)

        print('Updating project.pbxproj File')
        await self._replace(self.PATH_PROJECT_FILE)
        print('Finished updating ios bundle identifier')

    async def _replace(self, path):
        await self.replace_in_file(path, self.old_package_name, self.new_package_name)

    async def read_file_as_string(self, path):
        with open(path, 'r') as file:
            return file.read()

    async def replace_in_file(self, path, old, new):
        with open(path, 'r') as file:
            content = file.read()
        content = content.replace(old, new)
        with open(path, 'w') as file:
            file.write(content)
