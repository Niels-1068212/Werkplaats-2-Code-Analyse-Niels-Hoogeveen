# wp2-2023-TestGPT

# Installatie
Om de applicatie te kunnen starten moet je een virtual environment aanmaken. 
- Ga naar Command prompt (Windows + R, typ daarna cmd)
Ga naar de main folder van deze aplicatie in je bestanden: .../wp2-2023-mvc-1e-teamhnr
Als je dat gedaan hebt, volg dan in je cmd het volgende stappenplan:
1. python -m venv venv
2. cd venv
3. cd Scripts
4. activate
5. cd ..
6. cd ..
7. pip install -r requirements.txt
- Run nu de app.py in je persoonlijke IDE
- Typ in je browser: http://127.0.0.1:5000/

# login admin
Login als admin account. Dit zijn de inloggegevens:
Username: rachaan
Wachtwoord: wachtwoord
Maak gerust een nieuwe admin aan hoor!

# login user
Login als user: 
Username: Niels
Wachtwoord: nielsiepielsie
Maak gerust een nieuwe gebruiker aan hoor!

# LET OP! API-Key moet nog ingevoerd worden voor de werking van OpenAi. 
De key kan je zetten in het document testgpt.py, zoek naar de in koeienletters bijgevoegde text:
"VOEG HIER JE API KEY IN"


# Korte beschrijving van de applicatie
Door middel van de applicatie die we hebben gebouwd is de gebruiker in staat om notities op te slaan, aan te passen en te verwijderen.
Aan de notitie kan een titel, een bron en een categorie worden meegegeven en krijgt de gebruiker de optie om de notitie openbaar te maken.
Als de gebruiker geen titel kiest zullen de eerste 20 woorden van de notitie worden gebruikt in de titel.
Op basis van die notities kan men vragen en antwoorden laten genereren door ChatGPT. Deze kunnen later worden aangepast of verwijderd.
En om alles mooi samen te vatten kan de gebruiker op de default page alle notities in een vogelvlucht bekijken, verwijderen en bewerken.

Een admin account heeft toegang tot alle leraren (ofwel gebruikers). De admin is in staat gebruikers toe te voegen of te verwijderen.
Ook kan een admin een nieuwe admin toewijzen, en krijgt een admin de rol het wachtwoord aan te passen van een leraar als die zijn wachtwoord is vergeten. 



# Bronnen

- Chatgpt prompts:
    "<html file> Ik vind de filter secties een beetje heel erg lelijk. Kan jij dat mooier maken door middel van bootstrap?"
    "Hoe zorg ik dat een dictionary of rowobject te downloaden zijn in svg-formaat"

- Websites:  
    SQLModel. (n.d.). *Create a table with SQL.*  
    https://sqlmodel.tiangolo.com/tutorial/create-db-and-table-with-db-browser/  

    Just a moment... (n.d.). Just a moment...   
    https://stackoverflow.com/questions/65484419/save-svg-file-from-wikipedia-as-svg-in-python  

    Otto, M., Thornton, J., & Contributors, B. (n.d.). *Bootstrap.* 
    https://getbootstrap.com/  
    
    Paris, L. (2021, July 31). *Baking flask cookies with your secrets. Medium.*  
    https://blog.paradoxis.nl/defeating-flasks-session-management-65706ba9d3ce  

    Pallets (2010). *Quickstart — Flask documentation (3.0.x).*  
    https://flask.palletsprojects.com/en/3.0.x/quickstart/  

    Test-Correct (n.d.). *Digitaal toetsen met Test-Correct: formatief en summatief.*  
    https://www.test-correct.nl/hubfs/raw_assets/public/test-correct/images/testcorrect-logo.svg  

    Pallets (2010). *Flaskr tutorial.*  
    https://flask.palletsprojects.com/ - https://flask.palletsprojects.com/en/3.0.x/tutorial/

    


