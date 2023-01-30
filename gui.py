import PySimpleGUI as sg


# Very basic form.  Return values as a list
output_form= sg.FlexForm('Settlement Analyzer')
layout = [
        [sg.Text('Please type a file name')],
        [sg.Input()],
        [sg.Submit(), sg.Cancel()]
        ]
button, output_name =  output_form.Layout(layout).Read() 
#output_filename= output_name['Browse']
print(output_name[0])
output_form.close()