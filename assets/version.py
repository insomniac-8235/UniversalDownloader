# UTF-8
import os
import re
from PyInstaller.utils.win32.versioninfo import (
    VSVersionInfo, FixedFileInfo, StringFileInfo, StringStruct,
    VarFileInfo, VarStruct
)

# Read version from environment variable set in GitHub Actions
VERSION_RAW = os.environ.get('VERSION', 'v0.1.0')  # e.g., v0.1.0-beta

# Remove leading 'v'
VERSION_CLEAN = VERSION_RAW.lstrip('v')

# Windows numeric version must be 4 integers: MAJOR, MINOR, PATCH, BUILD
# Letters are not allowed, so we strip non-digits and treat pre-releases as build=0
match = re.match(r'^(\d+)\.(\d+)\.(\d+)', VERSION_CLEAN)
if match:
    major, minor, patch = map(int, match.groups())
else:
    major = minor = patch = 0
build = 0

VS_VERSION = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(major, minor, patch, build),
        prodvers=(major, minor, patch, build),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo([
            StringStruct(u'CompanyName', u'David Opasik'),
            StringStruct(u'FileDescription', u'Universal Downloader'),
            StringStruct(u'FileVersion', VERSION_CLEAN),
            StringStruct(u'InternalName', u'UniversalDownloader'),
            StringStruct(u'LegalCopyright', u'© 2026 David Opasik. All Rights Reserved.'),
            StringStruct(u'OriginalFilename', u'UniversalDownloader.exe'),
            StringStruct(u'ProductName', u'Universal Downloader'),
            StringStruct(u'ProductVersion', VERSION_CLEAN),
        ])
    ],
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
)