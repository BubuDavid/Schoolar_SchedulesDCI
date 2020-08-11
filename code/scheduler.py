# Importing stuff
import requests
import lxml.html as lh
from bs4 import BeautifulSoup
import pandas as pd
import prettify

url='http://www.dci.ugto.mx/estudiantes/index.php/mcursos/horarios-licenciatura'
#Create a handle, page, to handle the contents of the website
page = requests.get(url)
# Creating a beautiful soup so we can read it as html
soup = BeautifulSoup(page.content, 'html.parser')
# print the code
#print(soup.prettify())

# Finding the table
tbs = soup.findAll('table')[1]
tds = tbs.findAll("td")

# Column names
columns = []
saved = []
for index, td in enumerate(tds[0:7]):
    columns.append(td.get_text())
columns[3] = columns[3] + "1"
columns[4] = columns[4] + "2"
columns[5] = columns[5] + "3"


# rows
rows = []
i = -1
for index, td in enumerate(tds[7:]):    
    if index % 7 == 0:
        rows.append([])
        i += 1
    
    rows[i].append(td.get_text().replace("MIÈRCOLES", "MIÉRCOLES"))


df = pd.DataFrame(rows, columns=columns) 
df = df.drop(columns = ["NO."])
#df.to_excel ("./Todas_Materias.xls", index = True, header=True)


# User thingy
subjects = []
user = input("Ingresa tu nombre por favor: ")
subject_file = open(f"./Users/{user}.txt", "r",  encoding='utf-8')
for subject in subject_file:
    subjects.append(subject[:-1])

# My schedule:
# subjects = [
#     "Ecuaciones Diferenciales Parciales",
#     "Electromagnetismo",
#     "Mecánica Analítica",
#     "Termodinámica",
#     "Física Cuántica"
# ]
# Uppering
subjects = [subject.upper() for subject in subjects]
all_subjects = []
print(subjects)

# Aislating my subjects
for subject in subjects:
    all_subjects.append(df[df["UNIDAD DE APRENDIZAJE"] == subject])

# Getting the indexesseses
s_index = []
for subject in all_subjects:
    s_index.append(list(subject.index))
s_index

# I'll create all the combinations and with a function 
# I'll check if that schedule is posible. 
import itertools
schedules_index = list(itertools.product(*s_index))
# Checking that there are not schedules repeated
for i in range(len(schedules_index)):
    for j in range(i+1, len(schedules_index)):
        if sorted(list(schedules_index[i])) == sorted(list(schedules_index[j])):
            print("Diablos", i, j)
print(len(schedules_index))

# Creando todos los horarios posibles
# Making all the schedules possibles
schedules = []
for i, indexes in enumerate(schedules_index):
    schedules.append(pd.DataFrame(columns=columns[1:]))
    for index in indexes:
        schedules[i] = schedules[i].append(df.iloc[index])
        schedules[i] = schedules[i].sort_index()

# How many schedules we generate?
print("Total generated", len(schedules))
# This code tell us if there is a schedule repeated.
# But we checked before so it is just to prove we are doing it okay 
for i in range(len(schedules)):
    for j in range(i+1, len(schedules)):
        if list(schedules[i].index) == list(schedules[j].index):
            print("Diablos", i, j)

# Function
def isPossible(dia1, dia2):
    if dia1 == "\xa0" or dia2 == "\xa0" or dia1 == "1 HORA EN LÌNEA" or dia2 == "1 HORA EN LÌNEA":
        return True
    dia1 = dia1.split("/")
    dia2 = dia2.split("/")    
    
    day1 = dia1[0]
    day2 = dia2[0]
    hour1 = dia1[1]
    hour2 = dia2[1]
      
    
    hour1 = list(range(int(hour1.split("-")[0]), int(hour1.split("-")[1])))
    hour2 = list(range(int(hour2.split("-")[0]), int(hour2.split("-")[1]))) 
    
    if day1 == day2:
        for h in hour1:
            if h in hour2:
                return False
    return True
    
    #print(day1, hour1)
    #print(day2, hour2)    

# Filter the schedules that are possible.
possibles_schedules = []
for i, schedule in enumerate(schedules):
    dias = list(schedule["DÍA/HORA/AULA1"]) + list(schedule["DÍA/HORA/AULA2"]) + list(schedule["DÍA/HORA/AULA3"])
    possible = True
    for i in range(len(dias)):
        for j in range(i+1, len(dias)):
            if isPossible(dias[i], dias[j]) == False:
                possible = False
    if possible == True:
        possibles_schedules.append(schedule)

print("Possibles schedules:", len(possibles_schedules))

# Creating excel
# Function to insert a day in the calendar
def insert_day(calendy, s, j, subject):
    m = list(s[f"DÍA/HORA/AULA{j}"])[0].split("/")
    day = m[0]
    if day == "\xa0" or day == "1 HORA EN LÌNEA":
        return
    hour = m[1]
    place = m[2]
    hour = list(range(int(hour.split("-")[0]), int(hour.split("-")[1])))
    hour = [f"{h}:00 hrs" for h in hour]
    #print(day)
    #print(hour)
    #print(place)

    for h in hour:
        if ("LAB" in place or "PENDIENTE" in place) and not "LAB" in subject:
            subject = subject + " LAB"
        if subject == "ECUACIONES DIFERENCIALES PARCIALES":
            subject = "EDP"
        
        calendy[day][h] = subject
            
    # Styling the cells

# Create a Pandas Excel writer using XlsxWriter as the engine.
writer = pd.ExcelWriter(f'./Users/{user}.xlsx', engine='xlsxwriter')

for i, schedule in enumerate(possibles_schedules):
    # Create a DataFrame with the format of a schedule
    hours = [f"{hour}:00 hrs" for hour in range(8,19)]
    columns = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", ""]
    # Creating the base
    calendy = pd.DataFrame(columns=columns, index = hours) 
    # Inserting each subject
    for subject in schedule["UNIDAD DE APRENDIZAJE"]:
        s = schedule[schedule["UNIDAD DE APRENDIZAJE"] == subject]
        for j in range(1,4):
            insert_day(calendy, s, j, subject)
    # Styling
    #calendy.style.apply(style_function)
    
    # Adding description
    dicc = {}

    for j, column in enumerate(list(schedule.columns)):
        dicc[column] = columns[j]
    df2 = schedule.rename(columns=dicc)
    calendy = pd.concat([calendy, df2])

    
    # At this point, the schedule is created, but we need to save it in a sheet.
    # Convert the dataframe to an XlsxWriter Excel object.
    calendy.to_excel(writer, sheet_name=f'Sheet{i}')

    # Get the xlsxwriter workbook and worksheet objects.
    workbook  = writer.book
    worksheet = writer.sheets[f'Sheet{i}']
    
    # Set the column width.
    worksheet.set_column('A:A', 11.11)
    worksheet.set_column('B:B', 20)
    worksheet.set_column('C:C', 20)
    worksheet.set_column('D:D', 20)
    worksheet.set_column('E:E', 20)
    worksheet.set_column('F:F', 20)
        

    
# Close the Pandas Excel writer and output the Excel file.
writer.save()