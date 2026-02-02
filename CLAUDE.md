# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

kbImport is a personal media import and archival script used to import pictures, audio files, and video from cameras, SD cards, scanners, and other devices. It organizes all files under a uniform filing system based on date and job name, independent of the hardware used. The tool supports various RAW formats, AVCHD, and can convert some file types (e.g., RW2 to DNG).

## Commands

### Running the Main Script

```bash
# Basic usage - imports media from auto-detected sources
python3 kbImport3.py JobName

# Test mode - list files but don't copy
python3 kbImport3.py JobName -t

# Rename mode - reorganize files on the same disk (fast, no copying)
python3 kbImport3.py JobName -r

# Verbose output
python3 kbImport3.py JobName -v

# Pictures only
python3 kbImport3.py JobName -x

# Specify source volume
python3 kbImport3.py JobName -s /path/to/source

# Local archive only (skip network drives)
python3 kbImport3.py JobName -l

# Use Synology if available
python3 kbImport3.py JobName -S

# Unit testing mode (uses mockdata)
python3 kbImport3.py JobName -U
```

### Running Tests

```bash
# Run the basic unit tests
python3 test_kbImport.py
```

### Linting

```bash
# Run pylint with project configuration
pylint kbImport3.py
pylint classes/*.py
```

## Architecture

### Class Hierarchy

The main class structure follows this hierarchy:

```
Volumes()                    # Main coordinator (in classes/Volumes.py)
├─ Drives()                  # Platform-specific drive detection (in classes/Drives.py)
├─ Store()                   # Storage operations and directory creation (in classes/Store.py)
├─ ImgInfo()[]               # Per-file archive information (in classes/ImgInfo.py)
│  └─ DNGConverter()         # RAW to DNG conversion (in classes/DNGConverter.py)
├─ Avchd()                   # AVCHD video handling (in classes/Avchd.py)
├─ Video()                   # General video handling (in classes/Video.py)
└─ PerfMon()                 # Performance monitoring (in classes/PerfMon.py)
```

### Key Components

**AppOptions (classes/AppOptions.py)**: Configuration object that handles command-line arguments and platform detection. Supports Platform enum with values: MAC, WINDOWS, LINUX, CROSTINI, WSL, UBUNTU, ALPINE.

**Volumes (classes/Volumes.py)**: Main orchestrator that coordinates the import/archive process. The `archive()` method is the main entry point that:
1. Checks if media is ready (`media_are_ready()`)
2. Finds source image media
3. Archives images and video
4. Archives audio
5. Generates a report

**Drives (classes/Drives.py)**: Handles OS-specific drive detection and archive location configuration. Contains hardcoded lists of preferred archive drives (`preferredArchiveDrives`) that may need customization per installation. Key concept: distinguishes between `ExternalArchives` (network/external disks) and `LocalArchiveLocations` (fallback locations), and maintains `ForbiddenSources` to prevent importing from archive drives.

**ImgInfo (classes/ImgInfo.py)**: Represents a single file to be archived. Each instance tracks source and destination paths, handles DNG conversion decisions, and implements the doppelganger detection system (checks if files already exist in neighboring date directories to avoid duplicates). Uses class-level dictionaries (`doppelFiles`, `doppelPaths`) to cache duplicate detection results.

**Store (classes/Store.py)**: Manages directory creation with recursive `safe_mkdir()` functionality and tracks created directories for reporting. Handles date-based subdirectory structure (Year/Month/Day_JobName).

### Archive Directory Structure

Files are organized by media type and date:

```
Archive_Drive/
├─ Pix/
│  └─ YYYY/
│     └─ YYYY-MM-Mon/
│        └─ YYYY_MM_DD_JobName/
│           ├─ prefix_JobName_filename.JPG
│           └─ rw2s/              # RAW files moved here if converted to DNG
│              └─ P2357652.RW2
├─ Vid/
│  └─ YYYY/
│     └─ YYYY-MM-Mon/
│        └─ YYYY_MM_DD_JobName/
│           ├─ filename.MOV
│           └─ AVCHD/             # AVCHD directory structure preserved
└─ Audio/
   └─ YYYY/
      └─ YYYY-MM-Mon/
         └─ YYYY_MM_DD_JobName/
            └─ R09_0003.MP3
```

### Platform-Specific Code

Platform detection is handled in `AppOptions.identify_platform()`. Platform-specific behaviors are primarily in:
- `Drives` class for archive location detection
- `DNGConverter` (DNG conversion currently only active on Windows)
- Mount point handling varies by platform

### Testing Infrastructure

- **test_kbImport.py**: Basic unit tests (older, may need updating)
- **mockdata/**: Contains test data for unit testing
  - `mockdata/Pix/`: Mock archive structure
  - `mockdata/mocksrc/`: Mock source files
- Use `-U` or `--unit_test` flag to run against mock data instead of real drives

### Important Implementation Details

**Doppelganger Detection**: The system checks for duplicate files by scanning neighboring date directories in the archive. This prevents re-importing already archived files, even if they were archived with different job names on the same day. The check uses filename matching via regex `regexPic`.

**File Operations**: Supports both copy mode (default) and rename mode (`-r` flag). Rename mode is much faster for reorganizing files already on the target disk.

**Performance Monitoring**: `PerfMon` class tracks transfer rates. Historical performance data for various hardware configurations is documented in README.md.

**Drive Size Filtering**: `Drives.largestSource` (130GB default) prevents scanning large hard drives as potential source media, assuming source media are SD cards or similar removable media.

**Indentation**: Uses 2-space indentation (see pylintrc).

## Current Development Branch

Working on branch: `doppeling`

Main branch for PRs: `master`
