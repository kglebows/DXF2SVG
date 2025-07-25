# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Interactive GUI for DXF to SVG conversion
- Multiple SVG output formats (basic, interactive, structured)
- Automatic text-to-string assignment based on proximity
- Manual assignment editor with real-time preview
- Configurable parameters system
- Built-in SVG viewer
- Configuration management interface
- Comprehensive logging system
- Assignment management with undo/redo functionality

### Changed
- Reorganized codebase into modular structure
- Improved error handling and user feedback
- Enhanced configuration system with GUI interface

### Fixed
- MPTT_HEIGHT configuration parameter now properly affects SVG line widths
- Static import issues that prevented dynamic configuration updates
- Rectangle heights in structured SVG now use configurable parameters

## [1.0.0] - 2024-XX-XX

### Added
- Initial release of DXF2SVG converter
- Core DXF file processing capabilities
- Basic SVG generation
- Command-line interface
- Configuration file support
