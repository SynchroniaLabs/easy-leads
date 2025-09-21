import FreeSimpleGUI as sg
from scraper import scraper

# Layout of the window
layout = [
    [sg.Text("Recherche"), sg.InputText(key='-QUERY-')],
    [sg.Text("Lieu"), sg.InputText(key='-LOCATION-')],
    [sg.Text("Emplacement de sauvegarde"), sg.InputText(key='-FOLDER-'), sg.FolderBrowse()],
    [sg.Button("Commencer la génération de prospects"), sg.Button("Annuler")]
]

def main():
    # Create the window
    window = sg.Window("SynchronIA - Générateur de prospects Google Maps", layout)

    # Event loop
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == "Annuler":
            break
        elif event == "Commencer la génération de prospects":
            print("Génération de prospects commencée!")
            scraper(values['-QUERY-'], values['-LOCATION-'], values['-FOLDER-'])
            print("Génération de prospects terminée!")
            
            # Fermer la fenêtre automatiquement après traitement
            window.close()
            break

    window.close()

if __name__ == "__main__":
    main()