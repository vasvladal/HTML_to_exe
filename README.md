# HTML to EXE Converter

## Introduction
The HTML to EXE Converter is a Python application that allows users to convert a website (comprising HTML, CSS, JavaScript, and media files) into a standalone executable file. This application utilizes the PyQt5 library for a user-friendly graphical interface and employs PyInstaller for packaging the website into an executable format. IF you have any website use on dailybasis just use this and it will make it as a software in .exe extension which will open in default web browser on system. It also generates a Mozila Public License version 2.0. You can also set the expiry of the exe in GUI program. 

## Features
- **User-Friendly GUI**: Built with PyQt5, providing an intuitive interface for users.
- **File Processing**: Automatically merges and minifies CSS and JavaScript files.
- **HTML Modification**: Updates HTML files to link to the minified resources.
- **Media File Support**: Copies media files (e.g., `.mp3`) to the output directory.
- **Executable Creation**: Packages the website into a single executable file using PyInstaller.
- **License Generation**: Automatically generates a license file based on the Mozilla Public License Version 2.0.
- **Expiry Options**: Allows users to set an expiration time for the executable.

## Key Functionalities
- **ConversionThread Class**: Handles the conversion process in a separate thread to keep the GUI responsive.
- **File Processing**: Merges, minifies, and processes CSS, JavaScript, and HTML files.
- **Executable Creation**: Uses PyInstaller to create a standalone executable with optional icon support.
- **Progress Tracking**: Provides real-time progress updates during the conversion process.

## How to Use
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/html-to-exe-converter.git
   cd html-to-exe-converter
   ```

2. **Install Dependencies**:
   Make sure you have Python installed, then install the required packages:
   ```bash
   pip install PyQt5 beautifulsoup4 csscompressor jsmin pyinstaller
   ```

3. **Run the Application**:
   Execute the script:
   ```bash
   python html_to_exe.py
   ```

4. **Select Input Directory**:
   Click on the "Select Website Folder to convert" button to choose the directory containing your website files.

5. **Set Expiry**:
   Choose the desired expiry time for the executable from the dropdown menu.

6. **Start Conversion**:
   Click the "Convert" button to begin the conversion process. The progress bar will indicate the status of the conversion.

7. **Output**:
   Once the conversion is complete, the output directory will be displayed, containing the generated executable and other processed files.

## Screenshots
*(Add screenshots of the application interface here)*

## License
This project is licensed under the Mozilla Public License Version 2.0. See the [LICENSE](LICENSE) file for details.

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## Acknowledgments
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro) for the GUI framework.
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) for HTML parsing.
- [csscompressor](https://github.com/yui/yuicompressor) and [jsmin](https://github.com/douglascrockford/JSMin) for minifying CSS and JavaScript files.
- [PyInstaller](https://www.pyinstaller.org/) for creating standalone executables.
