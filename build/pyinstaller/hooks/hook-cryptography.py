# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller hook for cryptography

This hook ensures that cryptography's binary dependencies and backends
are properly bundled with the executable.

Requirements addressed: 8.3 - Bundle modules with data files
Related to: Requirements 4.11, 14.2 (encryption of sensitive values)

The cryptography package includes:
- Binary extensions for cryptographic operations
- Backend implementations (OpenSSL)
- hazmat (Hazardous Materials) primitives

This hook collects all necessary submodules and binaries.
"""

from PyInstaller.utils.hooks import collect_submodules, collect_dynamic_libs, collect_data_files

# Collect all cryptography submodules
hiddenimports = collect_submodules('cryptography')

# Collect binary libraries
binaries = collect_dynamic_libs('cryptography')

# Collect data files
datas = collect_data_files('cryptography')

# Ensure critical submodules are included
hiddenimports += [
    'cryptography.fernet',
    'cryptography.hazmat',
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.primitives.ciphers',
    'cryptography.hazmat.primitives.ciphers.algorithms',
    'cryptography.hazmat.primitives.ciphers.modes',
    'cryptography.hazmat.primitives.hashes',
    'cryptography.hazmat.primitives.kdf',
    'cryptography.hazmat.primitives.kdf.pbkdf2',
    'cryptography.hazmat.backends',
    'cryptography.hazmat.backends.openssl',
    'cryptography.hazmat.backends.openssl.backend',
]

# Include _cffi_backend which cryptography depends on
hiddenimports += [
    '_cffi_backend',
]
