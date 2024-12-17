from pathlib import Path
import hashlib
import os
from datetime import datetime
import csv
from time import strftime
import zipfile

import PySimpleGUI as sg


# --- GUI ---
data_headings = ['Path', 'Hash', 'Size (MB)', 'Created', 'Modified']
data_values = []
data_cols_width = [40, 30, 3, 5, 5]
tbl = [sg.Table(values=data_values, 
        headings=data_headings, 
        max_col_width=65, 
        col_widths=data_cols_width, 
        auto_size_columns=False, 
        #select_mode=sg.TABLE_SELECT_MODE_BROWSE, # allow user to select only one row
        #enable_events=True, # important to catch the event
        expand_x=True, expand_y=True,
        justification="left",
        key='-TABLE-'),
     ]

r1 = sg.Radio("MD5", "hash", key='-MD5-', default=True)
r2 = sg.Radio("SHA256", "hash", key='-SHA256-')
b1 = sg.Button("Browse Files", size=(15, None))
b2 = sg.Button("Browse Folder", size=(15, None))
b3 = sg.Button("Save", size=(15, None))
b4 = sg.Button("Clear")
c1 = sg.Checkbox("Include Files", key='-ZIP-', default=False)
pb = sg.ProgressBar(max_value=10, orientation='h', size=(200,22), key='-progress-', expand_x=True, visible=False)
t1 = sg.Text("", key='-SIZE-')
    
layout = [[r1, r2],
          [b1, b2, b4, pb],
          [tbl],
          [b3, c1, t1],
         ]

window = sg.Window("LiveDump", layout, size=(1200,600), finalize=True)




# --- functions ---
def get_hash(f, md5_checked):
    try:
        if md5_checked:
            h = hashlib.md5()
        else:
            h = hashlib.sha256()
        with open(f, "rb") as f:
            for chunk in iter(lambda: f.read(32768), b""): #4096 * 8 is faster!
                h.update(chunk)
        return h.hexdigest()
    except:
        return "ERROR"


def get_info(f):
    try:
        sz = round(os.path.getsize(f) / 1024 / 1024, 3)
        ct = os.path.getctime(f)
        ct = datetime.fromtimestamp(ct).strftime('%Y-%m-%d %H:%M:%S')
        mt = os.path.getmtime(f)
        mt = datetime.fromtimestamp(mt).strftime('%Y-%m-%d %H:%M:%S')
        return sz, ct, mt
    except:
        return "ERROR", "ERROR", "ERROR"


def write_csv(lst, output):
    with open(output, 'w', encoding="utf-8", newline='') as f:
            write = csv.writer(f)
            write.writerow(data_headings)
            write.writerows(lst)


ERRORS = []
SIZE = []


def main():
    while True:
        event, values = window.read()
        
        if event == "Browse Files":
            filenames = sg.popup_get_file('', no_window=True, multiple_files=True)
            if not filenames:
                continue
                
            window['-progress-'].update(visible=True) #, max=(len(filenames)))
            for i, f in enumerate(filenames):
                h = get_hash(f, values["-MD5-"])
                sz, ct, mt = get_info(f)
                SIZE.append(sz)
                window["-progress-"].update(current_count = i + 1, max=len(filenames))
                row = [f, h, sz, ct, mt]
                data_values.append(row)
            window['-TABLE-'].update(data_values)
            window['-progress-'].update(visible=False)
            window["-SIZE-"].update(f"Total size: {round(sum(SIZE),0)} MB")
            
        if event == "Browse Folder":
            folder_path = sg.popup_get_folder("Select a directory")
            folder_path = Path(folder_path)
            filenames = [f for f in folder_path.glob('**/*') if f.is_file()]
            for i, f in enumerate(filenames):
                h = get_hash(f, values["-MD5-"])
                sz, ct, mt = get_info(f)
                SIZE.append(sz)
                window["-progress-"].update(current_count = i + 1, max=len(filenames))
                row = [f, h, sz, ct, mt]
                data_values.append(row)
            window['-TABLE-'].update(data_values)
            window['-progress-'].update(visible=False)
            window["-SIZE-"].update(f"Total size: {round(sum(SIZE),0)} MB")
        
        
        if event == "Save":
            if any(data_values):
                output = strftime("%Y%m%d%H%M%S_report")
                try:
                    write_csv(data_values, output+".txt")
                except Exception as e:
                    sg.popup_auto_close(f"Error: {e}", title="Error")

                if values["-ZIP-"] == True:
                    file_pathes = [x[0] for x in data_values]
                    window['-progress-'].update(visible=True)
                    
                    with zipfile.ZipFile(output+".zip", "w" ) as ZipFile:
                        for i, f in enumerate(file_pathes):
                            try:
                                ZipFile.write(f, compress_type=zipfile.ZIP_DEFLATED)
                                window["-progress-"].update(current_count = i + 1, max=len(file_pathes))
                            except Exception as e:
                                ERRORS.append(f)
                                continue
                
                sg.popup_auto_close("Report saved!", title="Save")
                window['-progress-'].update(visible=False)
                
                if any(ERRORS):
                    write_csv(ERRORS, output+"_error_log.txt")
                    sg.popup_auto_close(f"An error occured during zipping. See '{output}_error_log.txt'", title="Warning!")
        
        if event == "Clear":
            if any(data_values):
                ch = sg.popup_yes_no("Continue?")
                if ch == "Yes":
                    del data_values[:]
                    window['-TABLE-'].update(data_values)
                    del SIZE[:]
                    window["-SIZE-"].update("")

        if event == sg.WIN_CLOSED:
            break

    window.close()


if __name__ == '__main__':
    main()