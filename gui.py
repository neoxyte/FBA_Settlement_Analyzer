import PySimpleGUI as sg


# Very basic form.  Return values as a list
form = sg.FlexForm('Settlement Analyzer')  # begin with a blank form

layout = [
          [sg.Text('Please select Flat File')],
          [sg.Text('Flatfile:', size=(50, 1)), sg.FileBrowse()],
          #[sg.Radio("Use Helium 10 cost", "Radio1", default=False)],
          #[sg.Radio("Add Advertising Report", "Radio2", default=False)],
          [sg.Submit(), sg.Cancel()]
         ]


button, filename = form.Layout(layout).Read() 
print(button, filename)
form.close()