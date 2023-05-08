import PySimpleGUI as sg

layout = [[sg.Text('Select two files to combine')],
          [sg.Input(key='-FILE1-', enable_events=True, visible=True), sg.FileBrowse('Browse', key='-BROWSE1-')],
          [sg.Input(key='-FILE2-', enable_events=True, visible=True), sg.FileBrowse('Browse', key='-BROWSE2-')],
          [sg.Button('Combine', key='-COMBINE-')]]

window = sg.Window('File Combiner', layout)

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    if event == '-COMBINE-':
        file1 = values['-FILE1-']
        file2 = values['-FILE2-']
        with open(file1, 'rb') as f1:
            data1 = f1.read()
        with open(file2, 'rb') as f2:
            data2 = f2.read()
        with open('combined_file.txt', 'wb') as f3:
            f3.write(data1 + data2)
        sg.popup('Files combined successfully!', title='Success')
window.close()