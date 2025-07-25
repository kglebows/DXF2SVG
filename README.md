# DXF2SVG - Interactive DXF to SVG Converter

An advanced Python application for converting DXF files to SVG format with interactive assignment capabilities and configurable parameters.

## Features

- **DXF to SVG Conversion**: Convert DXF files to scalable SVG format
- **Interactive GUI**: User-friendly interface for managing conversions and assignments
- **Multiple SVG Formats**: 
  - Basic SVG (simple lines)
  - Interactive SVG (with clickable elements)
  - Structured SVG (with rectangles and grouping)
- **Automatic Assignment**: Intelligent text-to-string assignment based on proximity
- **Manual Assignment**: Interactive editor for fine-tuning assignments
- **Configurable Parameters**: Customizable settings via configuration files
- **Real-time Preview**: Built-in SVG viewer for immediate results

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DXF2SVG.git
cd DXF2SVG
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### GUI Mode (Recommended)
```bash
python start_gui.py
```
or
```bash
python run_interactive_gui.py
```

### Command Line Mode
```bash
python -m src.core.dxf2svg input.dxf
```

## Project Structure

```
DXF2SVG/
├── src/                     # Source code
│   ├── core/               # Core functionality
│   │   ├── config.py       # Configuration and text parsing
│   │   ├── dxf2svg.py      # Main conversion logic
│   │   └── geometry_utils.py # Geometric calculations
│   ├── gui/                # User interface
│   │   ├── interactive_gui_new.py # Main GUI application
│   │   └── simple_svg_viewer.py   # SVG preview component
│   ├── svg/                # SVG generation
│   │   └── svg_generator.py # SVG output formatting
│   ├── interactive/        # Interactive editing
│   │   ├── interactive_editor.py # Manual assignment tools
│   │   └── assignment_manager.py # Assignment management
│   ├── config/            # Configuration management
│   │   └── config_manager.py # Config file handling
│   └── utils/             # Utilities
│       └── console_logger.py # Logging and console output
├── tests/                 # Test files
├── docs/                  # Documentation
├── examples/              # Example files
├── logs/                  # Log files
└── temp/                  # Temporary files
```

## Configuration

The application uses configuration files (`.cfg`) to customize behavior:

- **MPTT_HEIGHT**: Line thickness in generated SVG
- **STATION_ID**: Station identifier for text filtering
- **TEXT_FORMATS**: Supported text format patterns
- **Colors and styling**: Customizable appearance settings

Configuration can be modified through the GUI's Config tab or by editing `.cfg` files directly.

## Supported File Formats

- **Input**: DXF (Drawing Exchange Format)
- **Output**: SVG (Scalable Vector Graphics)
- **Configuration**: CFG (Configuration files)

## Key Components

### Core Engine (`src/core/`)
- **dxf2svg.py**: Main conversion logic and workflow orchestration
- **config.py**: Configuration management and text parsing utilities
- **geometry_utils.py**: Geometric calculations and spatial analysis

### User Interface (`src/gui/`)
- **interactive_gui_new.py**: Main GUI application with tabbed interface
- **simple_svg_viewer.py**: Embedded SVG preview component

### SVG Generation (`src/svg/`)
- **svg_generator.py**: Multiple SVG format generation with configurable styling

### Interactive Tools (`src/interactive/`)
- **interactive_editor.py**: Manual assignment and editing tools
- **assignment_manager.py**: Assignment state management

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Requirements

- Python 3.7+
- tkinter (usually included with Python)
- ezdxf (for DXF file processing)
- Other dependencies listed in `requirements.txt`

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed via `pip install -r requirements.txt`
2. **DXF Loading Issues**: Verify DXF file is valid and not corrupted
3. **GUI Not Starting**: Check Python version (3.7+ required) and tkinter availability

### Debug Mode

Enable debug logging by setting the logging level in the configuration or running with verbose output.

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Style
The project follows PEP 8 guidelines. Use tools like `flake8` or `black` for code formatting.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.
