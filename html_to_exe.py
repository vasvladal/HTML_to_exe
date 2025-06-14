import codecs  # Add this import at the top of the file
import sys
import os
import shutil
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QLabel, QProgressBar, QMessageBox, QComboBox # type: ignore
from PyQt5.QtCore import Qt, QThread, pyqtSignal # type: ignore
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QMessageBox
from bs4 import BeautifulSoup
import csscompressor
import jsmin
# With this more explicit import:
try:
    import PyInstaller.__main__ as pyi_main
except ImportError:
    print("PyInstaller not found. Please install it with: pip install pyinstaller")
    sys.exit(1)
from PyQt5.QtGui import QIcon 
import time

# Global variables
input_path = None
output_path = None
temp_dir = None
conversion_thread = None

# Set the icon path and script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
default_icon_path = os.path.join(script_dir, 'icon.ico')

class ConversionThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, expiry_selection):
        super().__init__()
        self.expiry_selection = expiry_selection

    def run(self):
        try:
            self.progress.emit(10)
            process_files()
            self.progress.emit(50)
            create_executable(self.expiry_selection)
            self.progress.emit(90)
            cleanup()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

def process_files():
    global temp_dir
    os.makedirs(temp_dir, exist_ok=True)
    
    # Merge and minify CSS
    css_content = ""
    for root, _, files in os.walk(input_path):
        for file in files:
            if file.endswith('.css'):
                with codecs.open(os.path.join(root, file), 'r', 'utf-8', errors='ignore') as f:
                    css_content += f.read() + "\n"
    minified_css = csscompressor.compress(css_content)
    with codecs.open(os.path.join(temp_dir, 'styles.min.css'), 'w', 'utf-8') as f:
        f.write(minified_css)

    # Merge and minify JavaScript
    js_content = ""
    for root, _, files in os.walk(input_path):
        for file in files:
            if file.endswith('.js'):
                with codecs.open(os.path.join(root, file), 'r', 'utf-8', errors='ignore') as f:
                    js_content += f.read() + "\n"
    minified_js = jsmin.jsmin(js_content)
    with codecs.open(os.path.join(temp_dir, 'scripts.min.js'), 'w', 'utf-8') as f:
        f.write(minified_js)

    # Process HTML files
    for root, _, files in os.walk(input_path):
        for file in files:
            if file.endswith('.html'):
                with codecs.open(os.path.join(root, file), 'r', 'utf-8', errors='ignore') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                
                # Update CSS links
                for css_link in soup.find_all('link', rel='stylesheet'):
                    css_link['href'] = 'styles.min.css'
                
                # Update JS scripts
                for script in soup.find_all('script', src=True):
                    script['src'] = 'scripts.min.js'
                
                with codecs.open(os.path.join(temp_dir, file), 'w', 'utf-8') as f:
                    f.write(str(soup))

            # Copy .mp3 files to temp directory
            elif file.endswith('.mp3'):
                shutil.copy(os.path.join(root, file), os.path.join(temp_dir, file))
                print(f"Copied .mp3 file: {file}")

    # Copy other asset files (images, fonts, etc.)
    for root, _, files in os.walk(input_path):
        for file in files:
            if not file.endswith(('.html', '.css', '.js', '.mp3')):
                # Preserve directory structure for assets
                rel_path = os.path.relpath(os.path.join(root, file), input_path)
                dest_path = os.path.join(temp_dir, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy(os.path.join(root, file), dest_path)
                print(f"Copied asset file: {file}")

    # Generate license file
    generate_license()

def create_executable(expiry_selection):
    global temp_dir, output_path
    main_script = create_main_script()
    
    # Use the default icon path if it exists, otherwise use None
    icon_to_use = default_icon_path if os.path.exists(default_icon_path) else None
    
    icon_param = ['--icon', icon_to_use] if icon_to_use else []
    
    # Ensure the icon file is copied to the temp directory if it exists
    if icon_to_use:
        shutil.copy(icon_to_use, os.path.join(temp_dir, 'icon.ico'))
    
    # Copy the license file to the temp directory
    shutil.copy(os.path.join(output_path, 'LICENSE'), os.path.join(temp_dir, 'LICENSE'))
    
    """ PyInstaller.__main__.run([
        '--name=WebApp',
        '--onefile',
        '--windowed',
        f'--add-data={temp_dir}{os.pathsep}.',  # Use os.pathsep for cross-platform compatibility
        '--distpath=%s' % output_path,  # Specify the output directory
        *icon_param,
        main_script
    ]) """

    pyi_main.run([
        '--name=WebApp',
        '--onefile',
        '--windowed',
        f'--add-data={temp_dir}{os.pathsep}.',
        '--distpath=%s' % output_path,
        *icon_param,
        main_script
    ])

    os.remove(main_script)

def create_main_script():
    expiry_selection = expiry_combo.currentText()
    expiry_seconds = expiry_options[expiry_selection]
    
    script_content = """
import sys
import os
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def check_expiry():
    creation_time = {creation_time}
    expiry_seconds = {expiry_seconds}
    if expiry_seconds is not None:
        current_time = time.time()
        if current_time > creation_time + expiry_seconds:
            QMessageBox.critical(None, "Expired", "This application has expired.")
            sys.exit(1)

class WebAppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Web Application')
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create web view
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        
        # Load the HTML file
        index_path = resource_path('index.html')
        if os.path.exists(index_path):
            file_url = QUrl.fromLocalFile(os.path.abspath(index_path))
            self.web_view.load(file_url)
        else:
            self.web_view.setHtml("<h1>Error: index.html not found</h1>")

if __name__ == '__main__':
    check_expiry()
    app = QApplication(sys.argv)
    window = WebAppWindow()
    window.show()
    
    sys.exit(app.exec_())
""".format(
    creation_time=time.time(),
    expiry_seconds="None" if expiry_seconds is None else str(expiry_seconds)
)

    script_path = os.path.join(temp_dir, 'main_script.py')
    with open(script_path, 'w') as f:
        f.write(script_content)
    return script_path

def generate_license():
    license_content = """
This software is provided "as is" without warranty of any kind, express or implied.
Unauthorized distribution or modification is prohibited.


Mozilla Public License Version 2.0
==================================

1. Definitions
--------------

1.1. "Contributor"
    means each individual or legal entity that creates, contributes to
    the creation of, or owns Covered Software.

1.2. "Contributor Version"
    means the combination of the Contributions of others (if any) used
    by a Contributor and that particular Contributor's Contribution.

1.3. "Contribution"
    means Covered Software of a particular Contributor.

1.4. "Covered Software"
    means Source Code Form to which the initial Contributor has attached
    the notice in Exhibit A, the Executable Form of such Source Code
    Form, and Modifications of such Source Code Form, in each case
    including portions thereof.

1.5. "Incompatible With Secondary Licenses"
    means

    (a) that the initial Contributor has attached the notice described
        in Exhibit B to the Covered Software; or

    (b) that the Covered Software was made available under the terms of
        version 1.1 or earlier of the License, but not also under the
        terms of a Secondary License.

1.6. "Executable Form"
    means any form of the work other than Source Code Form.

1.7. "Larger Work"
    means a work that combines Covered Software with other material, in
    a separate file or files, that is not Covered Software.

1.8. "License"
    means this document.

1.9. "Licensable"
    means having the right to grant, to the maximum extent possible,
    whether at the time of the initial grant or subsequently, any and
    all of the rights conveyed by this License.

1.10. "Modifications"
    means any of the following:

    (a) any file in Source Code Form that results from an addition to,
        deletion from, or modification of the contents of Covered
        Software; or

    (b) any new file in Source Code Form that contains any Covered
        Software.

1.11. "Patent Claims" of a Contributor
    means any patent claim(s), including without limitation, method,
    process, and apparatus claims, in any patent Licensable by such
    Contributor that would be infringed, but for the grant of the
    License, by the making, using, selling, offering for sale, having
    made, import, or transfer of either its Contributions or its
    Contributor Version.

1.12. "Secondary License"
    means either the GNU General Public License, Version 2.0, the GNU
    Lesser General Public License, Version 2.1, the GNU Affero General
    Public License, Version 3.0, or any later versions of those
    licenses.

1.13. "Source Code Form"
    means the form of the work preferred for making modifications.

1.14. "You" (or "Your")
    means an individual or a legal entity exercising rights under this
    License. For legal entities, "You" includes any entity that
    controls, is controlled by, or is under common control with You. For
    purposes of this definition, "control" means (a) the power, direct
    or indirect, to cause the direction or management of such entity,
    whether by contract or otherwise, or (b) ownership of more than
    fifty percent (50%) of the outstanding shares or beneficial
    ownership of such entity.

2. License Grants and Conditions
--------------------------------

2.1. Grants

Each Contributor hereby grants You a world-wide, royalty-free,
non-exclusive license:

(a) under intellectual property rights (other than patent or trademark)
    Licensable by such Contributor to use, reproduce, make available,
    modify, display, perform, distribute, and otherwise exploit its
    Contributions, either on an unmodified basis, with Modifications, or
    as part of a Larger Work; and

(b) under Patent Claims of such Contributor to make, use, sell, offer
    for sale, have made, import, and otherwise transfer either its
    Contributions or its Contributor Version.

2.2. Effective Date

The licenses granted in Section 2.1 with respect to any Contribution
become effective for each Contribution on the date the Contributor first
distributes such Contribution.

2.3. Limitations on Grant Scope

The licenses granted in this Section 2 are the only rights granted under
this License. No additional rights or licenses will be implied from the
distribution or licensing of Covered Software under this License.
Notwithstanding Section 2.1(b) above, no patent license is granted by a
Contributor:

(a) for any code that a Contributor has removed from Covered Software;
    or

(b) for infringements caused by: (i) Your and any other third party's
    modifications of Covered Software, or (ii) the combination of its
    Contributions with other software (except as part of its Contributor
    Version); or

(c) under Patent Claims infringed by Covered Software in the absence of
    its Contributions.

This License does not grant any rights in the trademarks, service marks,
or logos of any Contributor (except as may be necessary to comply with
the notice requirements in Section 3.4).

2.4. Subsequent Licenses

No Contributor makes additional grants as a result of Your choice to
distribute the Covered Software under a subsequent version of this
License (see Section 10.2) or under the terms of a Secondary License (if
permitted under the terms of Section 3.3).

2.5. Representation

Each Contributor represents that the Contributor believes its
Contributions are its original creation(s) or it has sufficient rights
to grant the rights to its Contributions conveyed by this License.

2.6. Fair Use

This License is not intended to limit any rights You have under
applicable copyright doctrines of fair use, fair dealing, or other
equivalents.

2.7. Conditions

Sections 3.1, 3.2, 3.3, and 3.4 are conditions of the licenses granted
in Section 2.1.

3. Responsibilities
-------------------

3.1. Distribution of Source Form

All distribution of Covered Software in Source Code Form, including any
Modifications that You create or to which You contribute, must be under
the terms of this License. You must inform recipients that the Source
Code Form of the Covered Software is governed by the terms of this
License, and how they can obtain a copy of this License. You may not
attempt to alter or restrict the recipients' rights in the Source Code
Form.

3.2. Distribution of Executable Form

If You distribute Covered Software in Executable Form then:

(a) such Covered Software must also be made available in Source Code
    Form, as described in Section 3.1, and You must inform recipients of
    the Executable Form how they can obtain a copy of such Source Code
    Form by reasonable means in a timely manner, at a charge no more
    than the cost of distribution to the recipient; and

(b) You may distribute such Executable Form under the terms of this
    License, or sublicense it under different terms, provided that the
    license for the Executable Form does not attempt to limit or alter
    the recipients' rights in the Source Code Form under this License.

3.3. Distribution of a Larger Work

You may create and distribute a Larger Work under terms of Your choice,
provided that You also comply with the requirements of this License for
the Covered Software. If the Larger Work is a combination of Covered
Software with a work governed by one or more Secondary Licenses, and the
Covered Software is not Incompatible With Secondary Licenses, this
License permits You to additionally distribute such Covered Software
under the terms of such Secondary License(s), so that the recipient of
the Larger Work may, at their option, further distribute the Covered
Software under the terms of either this License or such Secondary
License(s).

3.4. Notices

You may not remove or alter the substance of any license notices
(including copyright notices, patent notices, disclaimers of warranty,
or limitations of liability) contained within the Source Code Form of
the Covered Software, except that You may alter any license notices to
the extent required to remedy known factual inaccuracies.

3.5. Application of Additional Terms

You may choose to offer, and to charge a fee for, warranty, support,
indemnity or liability obligations to one or more recipients of Covered
Software. However, You may do so only on Your own behalf, and not on
behalf of any Contributor. You must make it absolutely clear that any
such warranty, support, indemnity, or liability obligation is offered by
You alone, and You hereby agree to indemnify every Contributor for any
liability incurred by such Contributor as a result of warranty, support,
indemnity or liability terms You offer. You may include additional
disclaimers of warranty and limitations of liability specific to any
jurisdiction.

4. Inability to Comply Due to Statute or Regulation
---------------------------------------------------

If it is impossible for You to comply with any of the terms of this
License with respect to some or all of the Covered Software due to
statute, judicial order, or regulation then You must: (a) comply with
the terms of this License to the maximum extent possible; and (b)
describe the limitations and the code they affect. Such description must
be placed in a text file included with all distributions of the Covered
Software under this License. Except to the extent prohibited by statute
or regulation, such description must be sufficiently detailed for a
recipient of ordinary skill to be able to understand it.

5. Termination
--------------

5.1. The rights granted under this License will terminate automatically
if You fail to comply with any of its terms. However, if You become
compliant, then the rights granted under this License from a particular
Contributor are reinstated (a) provisionally, unless and until such
Contributor explicitly and finally terminates Your grants, and (b) on an
ongoing basis, if such Contributor fails to notify You of the
non-compliance by some reasonable means prior to 60 days after You have
come back into compliance. Moreover, Your grants from a particular
Contributor are reinstated on an ongoing basis if such Contributor
notifies You of the non-compliance by some reasonable means, this is the
first time You have received notice of non-compliance with this License
from such Contributor, and You become compliant prior to 30 days after
Your receipt of the notice.

5.2. If You initiate litigation against any entity by asserting a patent
infringement claim (excluding declaratory judgment actions,
counter-claims, and cross-claims) alleging that a Contributor Version
directly or indirectly infringes any patent, then the rights granted to
You by any and all Contributors for the Covered Software under Section
2.1 of this License shall terminate.

5.3. In the event of termination under Sections 5.1 or 5.2 above, all
end user license agreements (excluding distributors and resellers) which
have been validly granted by You or Your distributors under this License
prior to termination shall survive termination.

************************************************************************
*                                                                      *
*  6. Disclaimer of Warranty                                           *
*  -------------------------                                           *
*                                                                      *
*  Covered Software is provided under this License on an "as is"       *
*  basis, without warranty of any kind, either expressed, implied, or  *
*  statutory, including, without limitation, warranties that the       *
*  Covered Software is free of defects, merchantable, fit for a        *
*  particular purpose or non-infringing. The entire risk as to the     *
*  quality and performance of the Covered Software is with You.        *
*  Should any Covered Software prove defective in any respect, You     *
*  (not any Contributor) assume the cost of any necessary servicing,   *
*  repair, or correction. This disclaimer of warranty constitutes an   *
*  essential part of this License. No use of any Covered Software is   *
*  authorized under this License except under this disclaimer.         *
*                                                                      *
************************************************************************

************************************************************************
*                                                                      *
*  7. Limitation of Liability                                          *
*  --------------------------                                          *
*                                                                      *
*  Under no circumstances and under no legal theory, whether tort      *
*  (including negligence), contract, or otherwise, shall any           *
*  Contributor, or anyone who distributes Covered Software as          *
*  permitted above, be liable to You for any direct, indirect,         *
*  special, incidental, or consequential damages of any character      *
*  including, without limitation, damages for lost profits, loss of    *
*  goodwill, work stoppage, computer failure or malfunction, or any    *
*  and all other commercial damages or losses, even if such party      *
*  shall have been informed of the possibility of such damages. This   *
*  limitation of liability shall not apply to liability for death or   *
*  personal injury resulting from such party's negligence to the       *
*  extent applicable law prohibits such limitation. Some               *
*  jurisdictions do not allow the exclusion or limitation of           *
*  incidental or consequential damages, so this exclusion and          *
*  limitation may not apply to You.                                    *
*                                                                      *
************************************************************************

8. Litigation
-------------

Any litigation relating to this License may be brought only in the
courts of a jurisdiction where the defendant maintains its principal
place of business and such litigation shall be governed by laws of that
jurisdiction, without reference to its conflict-of-law provisions.
Nothing in this Section shall prevent a party's ability to bring
cross-claims or counter-claims.

9. Miscellaneous
----------------

This License represents the complete agreement concerning the subject
matter hereof. If any provision of this License is held to be
unenforceable, such provision shall be reformed only to the extent
necessary to make it enforceable. Any law or regulation which provides
that the language of a contract shall be construed against the drafter
shall not be used to construe this License against a Contributor.

10. Versions of the License
---------------------------

10.1. New Versions

Mozilla Foundation is the license steward. Except as provided in Section
10.3, no one other than the license steward has the right to modify or
publish new versions of this License. Each version will be given a
distinguishing version number.

10.2. Effect of New Versions

You may distribute the Covered Software under the terms of the version
of the License under which You originally received the Covered Software,
or under the terms of any subsequent version published by the license
steward.

10.3. Modified Versions

If you create software not governed by this License, and you want to
create a new license for such software, you may create and use a
modified version of this License if you rename the license and remove
any references to the name of the license steward (except to note that
such modified license differs from this License).

10.4. Distributing Source Code Form that is Incompatible With Secondary
Licenses

If You choose to distribute Source Code Form that is Incompatible With
Secondary Licenses under the terms of this version of the License, the
notice described in Exhibit B of this License must be attached.

Exhibit A - Source Code Form License Notice
-------------------------------------------

  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at https://mozilla.org/MPL/2.0/.

If it is not possible or desirable to put the notice in a particular
file, then You may include the notice in a location (such as a LICENSE
file in a relevant directory) where a recipient would be likely to look
for such a notice.

You may add additional accurate notices of copyright ownership.

Exhibit B - "Incompatible With Secondary Licenses" Notice
---------------------------------------------------------

  This Source Code Form is "Incompatible With Secondary Licenses", as
  defined by the Mozilla Public License, v. 2.0.
"""
    license_path = os.path.join(output_path, 'LICENSE')
    with open(license_path, 'w') as f:
        f.write(license_content)
    print(f"License file created at: {license_path}")

def cleanup():
    shutil.rmtree(temp_dir)

def select_input():
    global input_path, output_path, temp_dir
    input_path = QFileDialog.getExistingDirectory(None, "Select Input Directory")
    if input_path:
        input_label.setText(f"Input: {input_path}")
        
        # Create output directory based on current date and time
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(script_dir, f"output_{current_time}")
        os.makedirs(output_path, exist_ok=True)
        
        temp_dir = os.path.join(output_path, 'temp')
        
        output_label.setText(f"Output: {output_path}")
        convert_button.setEnabled(True)


def start_conversion():
    global conversion_thread
    if not input_path:
        QMessageBox.warning(None, "Error", "Please select an input directory.")
        return

    expiry_selection = expiry_combo.currentText()
    conversion_thread = ConversionThread(expiry_selection)
    conversion_thread.progress.connect(update_progress)
    conversion_thread.finished.connect(conversion_finished)
    conversion_thread.error.connect(conversion_error)
    conversion_thread.start()

    convert_button.setEnabled(False)

def update_progress(value):
    progress_bar.setValue(value)

def conversion_finished():
    progress_bar.setValue(100)
    convert_button.setEnabled(True)
    QMessageBox.information(None, "Success", f"Conversion completed successfully!\nOutput directory: {output_path}")

def conversion_error(error_message):
    QMessageBox.critical(None, "Error", f"An error occurred: {error_message}")
    convert_button.setEnabled(True)

# Main application
app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("HTML to EXE Converter")
window.setGeometry(100, 100, 400, 300)

# Set the window icon
icon_path = os.path.join(script_dir, 'icon.jpg')
if os.path.exists(icon_path):
    app_icon = QIcon(icon_path)
    window.setWindowIcon(app_icon)
    app.setWindowIcon(app_icon)

layout = QVBoxLayout()

input_label = QLabel("Input: Not selected")
layout.addWidget(input_label)

output_label = QLabel("Output: Not selected")
layout.addWidget(output_label)

select_input_button = QPushButton("Select Website Folder to convert")
select_input_button.clicked.connect(select_input)
layout.addWidget(select_input_button)

convert_button = QPushButton("Convert")
convert_button.clicked.connect(start_conversion)
convert_button.setEnabled(False)
layout.addWidget(convert_button)

progress_bar = QProgressBar()
layout.addWidget(progress_bar)

expiry_options = {
    "1 minutes": 60,
    "1 hour": 3600,
    "1 day": 86400,
    "1 week": 604800,
    "1 month": 2592000,
    "1 year": 31536000,
    "Lifetime": None
}

expiry_label = QLabel("Select Expiry:")
layout.addWidget(expiry_label)

expiry_combo = QComboBox()
expiry_combo.addItems(expiry_options.keys())
layout.addWidget(expiry_combo)

container = QWidget()
container.setLayout(layout)
window.setCentralWidget(container)

def closeEvent(event):
    global conversion_thread
    if conversion_thread and conversion_thread.isRunning():
        conversion_thread.wait()
    event.accept()

window.closeEvent = closeEvent

if __name__ == "__main__":
    window.show()
    sys.exit(app.exec_())