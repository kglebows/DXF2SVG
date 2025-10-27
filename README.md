# DXF2SVG - Interactive DXF to SVG Converter

![Python Version](https://img.shields.io/badge/python-3.13-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

A powerful Python application for converting AutoCAD DXF files to interactive SVG format with intelligent text-to-geometry assignment and modern GUI interface.

##  Features

###  **Multiple SVG Output Formats**
- **Basic SVG**: Simple conversion with geometric shapes only
- **Interactive SVG**: Click-to-assign interface for manual text assignment correction
- **Structured SVG**: Hierarchically organized output grouped by inverters with hover tooltips

###  **Modern GUI Interface**
- **Unified Configuration Tab**: Dynamic layout with automatic panel width adjustment
- **Interactive Assignment Editor**: Visual editing with left-click selection and right-click assignment
- **Real-time Preview**: Built-in SVG viewer with zoom/pan capabilities
- **Responsive Log Window**: Multi-threaded logging with automatic scrolling

###  **Intelligent Processing**
- **Automatic Text Assignment**: Distance-based algorithm assigns text labels to geometric segments
- **Duplicate Detection**: Identifies and removes duplicate segments automatically
- **Outlier Filtering**: Removes elements outside meaningful bounds for cleaner output
- **Adaptive ViewBox**: Dynamically calculated viewBox that accommodates elements with negative coordinates

###  **Advanced Capabilities**
- **Custom Text Parsing**: Configurable regex patterns for extracting station IDs and inverter numbers
- **Batch Processing**: Convert multiple DXF files with a single configuration
- **Interactive Tooltips**: Hover over elements in Structured SVG to view metadata (segment IDs, structural IDs)
- **Configuration Presets**: Save and load `.cfg` files for different DXF formats

##  Quick Start

### Prerequisites

- Python 3.13 or higher
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DXF2SVG.git
cd DXF2SVG
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

### Basic Usage

#### GUI Mode (Recommended)

Launch the interactive GUI:
```bash
python run_interactive_gui.py
```

Or use the batch script on Windows:
```bash
start_gui.bat
```

#### Command Line Mode

```python
from src.core.dxf2svg import DXF2SVG

# Load DXF file
dxf = DXF2SVG('input.dxf', 'config.cfg')

# Process and generate SVG
dxf.extract_texts()
dxf.extract_polylines()
dxf.assign_texts_to_strings()
dxf.generate_svg('output.svg')
```

##  User Guide

### Step 1: Launch Application
Run `run_interactive_gui.py` to start the GUI. The main window contains three tabs:
- **Configuration**: Set up layers, station IDs, and output formats
- **Assignment Editor**: Manually correct text assignments
- **SVG Viewer**: Preview generated SVG files

### Step 2: Configure DXF Settings
In the **Configuration Tab**:
1. Click **Select DXF File** to load your AutoCAD file
2. Configure layer names:
   - **Polyline Layer**: Layer containing geometric segments (e.g., `@IDE_STRING_1`)
   - **Text Layer**: Layer containing text labels (e.g., `@IDE_STRING_1_TXT`)
3. Set **Station ID** (e.g., `LES1`, `LES2`)

### Step 3: Configure Text Parsing
Define regex patterns for extracting metadata from text labels:
- **Station ID Pattern**: e.g., `([A-Z]+\d+)` to extract `LES1` from `LES1-INV01`
- **Inverter Pattern**: e.g., `INV(\d+)` to extract `01` from `LES1-INV01`

### Step 4: Set Output Format
Choose SVG generation mode:
- **Interactive**: Generates `interactive_assignment.svg` with assignment controls
- **Structured**: Creates hierarchically organized SVG grouped by inverters with tooltips

### Step 5: Process DXF
Click **Load and Process DXF** button:
1. Application extracts texts and polylines
2. Automatic assignment runs (distance-based algorithm)
3. Interactive SVG is generated
4. Progress bar shows conversion status

### Step 6: Refine Assignments (Optional)
Switch to **Assignment Editor** tab:
1. View the interactive SVG with colored elements:
   - **Green**: Assigned segments
   - **Red**: Unassigned texts
   - **Gray**: Unassigned segments
2. **Left-click** to select text or segment
3. **Right-click** on target element to assign
4. Use **Clear Assignment** button to remove incorrect assignments

### Step 7: Generate Final SVG
In **Configuration Tab**, click **Generate Structured SVG**:
- Outputs final SVG with:
  - Hierarchical grouping by inverters
  - Hover tooltips showing metadata
  - Clean viewBox encompassing all elements
  - Duplicate-free geometry

##  Configuration File Format

Configuration files use `.cfg` format with INI-style sections:

```ini
[Layers]
polyline_layer = @IDE_STRING_1
text_layer = @IDE_STRING_1_TXT

[Station]
station_id = LES1

[Format]
delimiter = -
remove_prefix = True

[Search]
search_string_regex = ([A-Z]+\d+)
search_inverter_regex = INV(\d+)
search_segment_regex = (\d+)

[Visual]
segment_height = 20
text_size = 3
spacing = 2

[Files]
output_dir = ./output
save_interactive = True
save_structured = True
```

### Configuration Sections

- **[Layers]**: DXF layer names for polylines and text
- **[Station]**: Station identifier for filtering texts
- **[Format]**: Text parsing rules (delimiter, prefix handling)
- **[Search]**: Regex patterns for extracting IDs
- **[Visual]**: SVG styling parameters
- **[Files]**: Output directory and generation flags

##  SVG Output Types

### Interactive SVG
- Purpose: Manual assignment correction interface
- Features:
  - Click-to-select elements
  - Right-click to assign text to segment
  - Color-coded status (green=assigned, red=unassigned text, gray=unassigned segment)
  - Embedded JavaScript for interactivity
- Use Case: Correcting automatic assignment errors

### Structured SVG
- Purpose: Final production output
- Features:
  - Hierarchical `<g>` groups by inverter ID
  - Custom data attributes: `data-structural-id`, `data-string-id`, `data-segment-id`
  - Hover tooltips showing element metadata
  - Adaptive viewBox for complete visibility
  - Clean, validated SVG structure
- Use Case: Documentation, web integration, archival

##  Troubleshooting

### DXF File Not Loading
- **Error**: "Cannot open DXF file"
- **Solution**: Verify file path and ensure DXF is not corrupted. Check DXF version compatibility (R12-R2018 supported).

### No Automatic Assignments
- **Error**: "0 texts assigned automatically"
- **Solution**: 
  - Check that station ID matches text content
  - Verify regex patterns in Configuration tab
  - Ensure polyline and text layers are correct

### Text Not Visible in SVG
- **Error**: Text labels missing in output
- **Solution**: 
  - Increase `text_size` parameter in configuration
  - Check text layer name is correct
  - Verify texts are on the correct layer in DXF

### Tooltips Not Working (Structured SVG)
- **Error**: No tooltip on hover
- **Solution**: 
  - Open SVG in modern browser (Chrome, Firefox, Edge)
  - Ensure JavaScript is enabled
  - Hover cursor must be directly over `rect` elements

### ViewBox Cuts Off Elements
- **Error**: Segments or texts clipped at edges
- **Solution**: Application automatically calculates adaptive viewBox. If issue persists:
  - Check for extremely large coordinate values in DXF
  - Verify outlier filtering isn't too aggressive (`outlier_threshold` in config)

### GUI Panel Too Narrow/Wide
- **Error**: Configuration cards not fully visible
- **Solution**: Panel width adjusts automatically based on content. If scrollbar overlaps:
  - Resize main window to trigger recalculation
  - Check `optimal_width = max_card_width + 30` in `unified_config_tab.py`

### Progress Bar Doesn't Stop
- **Error**: Progress bar continues after conversion completes
- **Solution**: Fixed in current version. Update to latest commit if issue persists.

### "Wyczyść Linię" Button Uses Wrong IDs
- **Error**: Clear line removes wrong assignments
- **Solution**: Fixed in current version. Segment ID lookup now uses correct data structure traversal.

### Application Crashes on Large DXF
- **Error**: Memory error or freeze
- **Solution**:
  - Reduce DXF file size by removing unnecessary layers
  - Increase Python heap size: `python -X opt -W ignore run_interactive_gui.py`
  - Check system RAM availability

### Log Window Not Scrolling
- **Error**: Log messages hidden
- **Solution**: Log window automatically scrolls to bottom. If issue persists:
  - Check for thread synchronization errors in console
  - Verify `ScrolledText` widget configuration

##  Advanced Usage

### Custom Text Parsing

Override default regex patterns for specialized DXF formats:

```python
from src.config.config_manager import ConfigManager

config = ConfigManager('custom.cfg')
config.set('Search', 'search_string_regex', r'CUSTOM-(\d{4})')
config.set('Search', 'search_inverter_regex', r'INV#(\d+)')
config.save()
```

### Batch Processing

Process multiple DXF files with a single configuration:

```python
import os
from src.core.dxf2svg import DXF2SVG

config_file = 'batch_config.cfg'
input_dir = './input_dxf/'
output_dir = './output_svg/'

for filename in os.listdir(input_dir):
    if filename.endswith('.dxf'):
        dxf_path = os.path.join(input_dir, filename)
        svg_path = os.path.join(output_dir, filename.replace('.dxf', '.svg'))
        
        dxf = DXF2SVG(dxf_path, config_file)
        dxf.process_all()  # Extract, assign, generate
        dxf.save_structured_svg(svg_path)
```

### Programmatic API

Use DXF2SVG as a library in your Python projects:

```python
from src.core.dxf2svg import DXF2SVG

# Initialize with DXF file and config
converter = DXF2SVG('plant_layout.dxf', 'config.cfg')

# Step-by-step processing
texts = converter.extract_texts()
polylines = converter.extract_polylines()
assignments = converter.assign_texts_to_strings()

# Access raw data
for inverter_id, strings in converter.inverter_data.items():
    for string_id, segments in strings.items():
        print(f"Inverter {inverter_id}, String {string_id}: {len(segments)} segments")

# Generate custom output
converter.generate_interactive_svg('custom_interactive.svg')
converter.generate_structured_svg('custom_structured.svg')
```

##  Project Structure

```
DXF2SVG/
 src/
    core/                # Core conversion logic
       dxf2svg.py       # Main DXF processor
       config.py        # Configuration dataclass
       geometry_utils.py # Geometric calculations
    svg/                 # SVG generation
       svg_generator.py # SVG writer with adaptive viewBox
    gui/                 # User interface
       interactive_gui_new.py # Main application window
       unified_config_tab.py  # Configuration panel
       enhanced_svg_viewer.py # Interactive SVG viewer
       simple_svg_viewer.py   # Basic SVG renderer
    interactive/         # Assignment editing
       interactive_editor.py  # Assignment editor tab
       assignment_manager.py  # Assignment logic
    config/              # Configuration management
       config_manager.py # Config file I/O
    utils/               # Utilities
        console_logger.py # Multi-threaded logging
 configs/                 # Sample configuration files
    Grabowo3.cfg
    ziec.cfg
 run_interactive_gui.py   # Main entry point
 start_gui.bat            # Windows launcher
 requirements.txt         # Python dependencies
 LICENSE                  # MIT License
 README.md                # This file
```

##  Requirements

### Minimum Requirements
- Python 3.13+
- 4 GB RAM
- Windows 10/11, macOS 10.14+, or Linux (Ubuntu 20.04+)

### Recommended
- Python 3.13.1
- 8 GB RAM
- 1920x1080 display resolution for optimal GUI experience

### Dependencies
- `ezdxf>=1.3.0` - DXF file parsing
- `svgwrite>=1.4.3` - SVG file generation
- `tkinter` - GUI framework (included with Python)

Install all dependencies with:
```bash
pip install -r requirements.txt
```

##  Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m 'feat: add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/yourusername/DXF2SVG.git
cd DXF2SVG
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints for function signatures
- Document complex logic with inline comments
- Write descriptive commit messages (conventional commits format)

##  Roadmap

- [ ] Export to PDF format
- [ ] Multi-language support (Polish, German, Spanish)
- [ ] Command-line batch processing tool
- [ ] DXF layer auto-detection
- [ ] Cloud-based conversion API
- [ ] Real-time collaboration for assignment editing

##  License

This project is licensed under the MIT License - see below for details:

```
MIT License

Copyright (c) 2024 DXF2SVG Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

##  Support

For questions, bug reports, or feature requests:
- **Issues**: [GitHub Issues](https://github.com/yourusername/DXF2SVG/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/DXF2SVG/discussions)
- **Email**: support@dxf2svg.com

##  Acknowledgments

- [ezdxf](https://github.com/mozman/ezdxf) - Excellent DXF parsing library
- [svgwrite](https://github.com/mozman/svgwrite) - Robust SVG generation
- Python Tkinter community for GUI best practices

---

**Made with  by the DXF2SVG Team**
