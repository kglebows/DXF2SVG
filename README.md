# DXF2SVG - Interactive DXF to SVG Converter

A professional Python application for converting DXF (AutoCAD) files to SVG format with interactive GUI, automatic element assignment, and advanced configuration capabilities.

## ✨ Features

- **🔧 DXF to SVG Conversion**: Convert CAD files to modern vector format
- **🖥️ Interactive GUI**: User-friendly interface with live preview
- **🤖 Smart Assignment**: Intelligent text-to-geometry linking based on proximity
- **⚙️ Configurable Parameters**: Full control over conversion settings (line thickness, station ID, layer names)
- **📊 Multiple Output Formats**: 
  - Basic SVG (simple lines)
  - Interactive SVG (with clickable elements) 
  - Structured SVG (with rectangles and grouping)
- **🔍 Manual Editor**: Precise control over element assignments
- **📋 Configuration Management**: Save/load different project configurations

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- tkinter (usually included with Python)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/kglebows/DXF2SVG.git
cd DXF2SVG
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python start_gui.py
```

## 📖 Step-by-Step Usage Guide

### Step 1: Prepare Your Files
1. **Copy your DXF file** to the main project folder (same directory as `start_gui.py`)
2. **Launch the application**: Run `python start_gui.py`

### Step 2: Create Configuration
1. **Go to Configuration Tab** in the GUI
2. **Configure the following settings**:
   - **Station ID**: Enter your station identifier (e.g., "G3", "A1")
   - **Line Layer Name**: Name of the DXF layer containing lines/polylines (e.g., "STRINGS")
   - **Text Layer Name**: Name of the DXF layer containing text labels (e.g., "STRINGLABELS")
   - **DXF Filename**: Name of your input DXF file (e.g., "myproject.dxf")
   - **SVG Filename**: Desired output SVG filename (e.g., "output.svg")
   - **Text Format**: Configure how string labels should be formatted/parsed
   - **MPTT Height**: Line thickness in the output SVG (default: 1)

3. **Save Configuration**: Click "Save Config" and give it a name (e.g., "MyProject")

### Step 3: Load Configuration and Convert
1. **Go to Files Tab**
2. **Select your saved configuration** from the dropdown
3. **Click "Load Configuration"** - this will apply all your settings
4. **Click "Start Conversion"** - the app will process your DXF file

### Step 4: Review and Edit (Optional) 
1. **Automatic Assignment**: The system will automatically assign text labels to line segments based on proximity
2. **Switch to Interactive Mode**: If you need to make manual adjustments
3. **Use the Assignment Editor**: 
   - Review unassigned elements
   - Manually assign texts to specific line segments
   - Undo/redo changes as needed
4. **Generate Final SVG**: Once satisfied with assignments, generate the final output

### Step 5: Export Results
- **Basic SVG**: Simple line drawing
- **Interactive SVG**: Clickable elements with labels
- **Structured SVG**: Organized with rectangles and grouping

## 📁 Project Structure

```
DXF2SVG/
├── 🚀 start_gui.py          # Main application launcher
├── 🚀 run_interactive_gui.py # Alternative launcher
├── 📄 requirements.txt      # Python dependencies
├── 📄 README.md            # This file
├── 📄 LICENSE              # MIT License
│
├── 📂 src/                 # Source code
│   ├── 📂 core/           # Core conversion logic
│   ├── 📂 gui/            # User interface
│   ├── 📂 svg/            # SVG generation
│   ├── 📂 interactive/    # Assignment editor
│   ├── 📂 config/         # Configuration management
│   └── 📂 utils/          # Utilities and logging
│
├── 📂 configs/            # Configuration files (.cfg)
├── 📂 docs/               # Documentation
├── 📂 tests/              # Test files
└── 📂 examples/           # Example files
```

## 🛠️ Configuration Options

The application uses `.cfg` files to store project settings. Each configuration includes:

- **MPTT_HEIGHT**: Line thickness in generated SVG (1-10)
- **STATION_ID**: Station identifier for text filtering  
- **LAYER_LINE**: DXF layer name containing polylines/strings
- **LAYER_TEXT**: DXF layer name containing text labels
- **TEXT_FORMATS**: Supported text parsing patterns
- **DXF_FILE**: Input DXF filename
- **SVG_FILE**: Output SVG filename

## 🎯 Supported File Formats

- **Input**: `.dxf` (Drawing Exchange Format) 
- **Output**: `.svg` (Scalable Vector Graphics)
- **Config**: `.cfg` (Configuration files)

## 🤝 Contributing

Found a bug or want to contribute? We welcome contributions!

1. **Report Issues**: [Create an issue](https://github.com/kglebows/DXF2SVG/issues) describing:
   - What you were trying to do
   - What happened vs. what you expected
   - Steps to reproduce the problem
   - Your DXF file characteristics (if relevant)

2. **Submit Pull Requests**:
   - Fork the repository
   - Create a feature branch (`git checkout -b feature/amazing-feature`)
   - Commit your changes (`git commit -m 'Add some amazing feature'`)
   - Push to the branch (`git push origin feature/amazing-feature`)
   - Open a Pull Request

## 📋 Requirements

- **Python 3.7+**
- **tkinter** (usually included with Python)
- **ezdxf** (for DXF file processing)

Install all dependencies: `pip install -r requirements.txt`

## 🔧 Troubleshooting

### Common Issues

**Import Errors**
- Ensure all dependencies are installed: `pip install -r requirements.txt`

**DXF Loading Problems**  
- Verify your DXF file is valid and not corrupted
- Check that layer names in config match your DXF file
- Ensure DXF file is in the main project directory

**GUI Won't Start**
- Check Python version: `python --version` (3.7+ required)
- Verify tkinter is available: `python -c "import tkinter"`

**Conversion Issues**
- Verify Station ID matches text labels in your DXF
- Check that line and text layers exist in your DXF file
- Review configuration settings for typos

### Getting Help

If you encounter issues:

1. **Check the logs** - The application creates detailed logs
2. **Review your configuration** - Verify all settings match your DXF file
3. **Create an issue** on GitHub with:
   - Error message (if any)
   - Your configuration file
   - Description of your DXF file structure

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Copyright (c) 2025 Konrad Glebowski**

## 🌟 Acknowledgments

- Built with Python and tkinter
- Uses ezdxf library for DXF processing
- Designed for engineering and CAD professionals

---

**⭐ If this project helped you, please give it a star on GitHub!**
