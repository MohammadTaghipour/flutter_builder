import sys
import asyncio

from android_rename_steps import AndroidRenameSteps
from ios_rename_steps import IosRenameSteps

class ChangeAppPackageName:
    @staticmethod
    async def start(arguments):
        if not arguments:
            print('New package name is missing. Please provide a package name.')
            return

        if len(arguments) == 1:
            # No platform-specific flag, rename both Android and iOS
            print('Renaming package for both Android and iOS.')
            await ChangeAppPackageName._rename_both(arguments[0])
        elif len(arguments) == 2:
            # Check for platform-specific flags
            platform = arguments[1].lower()
            if platform == '--android':
                print('Renaming package for Android only.')
                await AndroidRenameSteps(arguments[0]).process()
            elif platform == '--ios':
                print('Renaming package for iOS only.')
                await IosRenameSteps(arguments[0]).process()
            else:
                print('Invalid argument. Use "--android" or "--ios".')
        else:
            print('Too many arguments. This package accepts only the new package name and an optional platform flag.')

    @staticmethod
    async def _rename_both(new_package_name):
        await AndroidRenameSteps(new_package_name).process()
        await IosRenameSteps(new_package_name).process()

if __name__ == "__main__":
    # Run the ChangeAppPackageName process with command-line arguments
    asyncio.run(ChangeAppPackageName.start(sys.argv[1:]))
