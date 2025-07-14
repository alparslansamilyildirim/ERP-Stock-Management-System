# ERP Stock Management System

A modern, desktop-based ERP stock management application built with Python and Tkinter. This application provides comprehensive inventory management capabilities with a clean, macOS-inspired interface.

## Features

### Core Functionality
- **Data Management**: Add, edit, and delete stock entries with real-time validation
- **Search & Filter**: Powerful search functionality across all columns
- **Sorting**: Click column headers to sort data by any field
- **Excel Export**: Export data to Excel format for reporting
- **File Upload**: Import data from Excel files with automatic mapping
- **Undo System**: Undo recent add and update operations

### Advanced Features
- **KOD Mapping System**: Create mappings between alternative values and standard KODs
- **Quantity Multiplier**: Apply quantity multipliers during file uploads
- **Automatic Comparison**: Compare uploaded files with existing database using mappings
- **User Feedback**: Comprehensive error handling and user notifications
- **Keyboard Shortcuts**: Full keyboard navigation and shortcuts

### User Interface
- **Modern Design**: Clean, Aqua-inspired interface that works on all platforms
- **Responsive Layout**: Automatically adjusts to window size
- **Fullscreen Support**: Toggle fullscreen mode with F11 or Ctrl+Cmd+F
- **In-place Editing**: Double-click cells to edit values directly
- **Real-time Validation**: Input validation with helpful error messages

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ERP
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Usage

### Main Interface
- **Search Bar**: Type to filter rows in real-time
- **Data Table**: View and manage all stock entries
- **Action Buttons**: Access main functions (Add Row, Export, Upload, Mappings)

### Adding Data
1. Click "Add Row" button
2. Fill in the required fields
3. Data is automatically validated before saving
4. Use "Undo" (Ctrl+Z) to reverse recent changes

### File Upload
1. Click "Upload a File" button
2. Select an Excel file (.xlsx format)
3. Choose quantity multiplier if needed
4. File is automatically compared with database
5. Create mappings for unmatched values if prompted

### KOD Mappings
1. Click "Manage KOD Mappings" button
2. View existing mappings in the first tab
3. Create new mappings in the second tab
4. Mappings help match alternative values to standard KODs

### Keyboard Shortcuts
- **F11** or **Ctrl+Cmd+F**: Toggle fullscreen
- **Ctrl+Z** or **Cmd+Z**: Undo last action
- **F5** or **Ctrl+R** or **Cmd+R**: Reload data
- **Double-click**: Edit cell in-place
- **Enter**: Save cell edit
- **Escape**: Cancel cell edit

## Project Structure

```
ERP/
├── main.py              # Application entry point
├── gui.py               # Main GUI implementation
├── database.py          # Database operations and CRUD functions
├── utils.py             # Utility functions and helpers
├── shortcuts.py         # Keyboard shortcut bindings
├── mapping_gui.py       # KOD mapping management dialogs
├── theme.py             # UI theme configuration
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── DB-Stok.db          # SQLite database (created automatically)
```

## Database Schema

The application uses SQLite with the following main tables:

### DB-Stok (Main Table)
- Contains all stock entries
- Schema is flexible and adapts to uploaded data
- Primary key: rowid (auto-increment)

### kod_mappings
- Maps alternative values to standard KODs
- Fields: id, original_kod, alternative_value, created_date

### actions_log
- Logs all user actions for audit trail
- Fields: id, timestamp, level, message

## Technical Details

### Dependencies
- **pandas**: Data manipulation and Excel file handling
- **openpyxl**: Excel file reading/writing
- **tkinter**: GUI framework (included with Python)
- **sqlite3**: Database engine (included with Python)

### Architecture
- **MVC Pattern**: Separation of data (database.py), view (gui.py), and logic
- **Modular Design**: Each module has a specific responsibility
- **Error Handling**: Comprehensive error handling with user feedback
- **Logging**: All operations are logged for debugging and audit

### Platform Support
- **Windows**: Full support with Aqua-like theme
- **macOS**: Native appearance with system integration
- **Linux**: Compatible with modern desktop environments

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or feature requests, please open an issue on the GitHub repository.

## Changelog

### Version
- Complete UI redesign with Aqua-like theme
- Enhanced KOD mapping system
- Improved error handling and user feedback
- Added keyboard shortcuts
- Optimized database operations
- Comprehensive input validation 