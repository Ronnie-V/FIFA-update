import pywikibot
import sqlite3
import re
import sys
from unidecode import unidecode

if len(sys.argv) > 1:
  datum = sys.argv[1]
else:
  exit(f'Gebruik: {sys.argv[0]} 20210403')

Targetdatabase = f'D://Wikipedia//Fifa-ranking.db'         
    
def open_db(name):
    print ('Connecting to',name)
    conn = sqlite3.connect(name)
    conn.row_factory = sqlite3.Row
    return conn
    
def get_monthname(month):   
    switcher = {
        u'1' : u'januari',
        u'2' : u'februari',
        u'3' : u'maart',
        u'4' : u'april',
        u'5' : u'mei',
        u'6' : u'juni',
        u'7' : u'juli',
        u'8' : u'augustus',
        u'9' : u'september',
        u'10' : u'oktober',
        u'11' : u'november',
        u'12' : u'december'
    }
    month = str(month)
    month = month.lstrip('0')
    return switcher.get(month.strip(),"") 

conn_uitvoer = open_db(Targetdatabase)

def LeesPositions(name):
  cpe = conn_uitvoer.cursor()
  cpe.execute(f'DELETE FROM `Posities` WHERE 1=1')
  f = open(name, 'r')
  CurPoints = ''
  Name = ''
  OldPoints = ''
  Pos = ''
  LineNr = 0
  for line in f:
    try:
      if LineNr == 0:
        Pos = line.strip()        
      elif LineNr == 2:
        Name = line.strip()  
      elif LineNr == 4:
        CurPoints = line.strip()  
      elif LineNr == 5:
        line = line.strip()
        if line.find('\t') > 0:
          line = line[:line.find('\t')]
        OldPoints = line.strip() 

    except:
      print (f'Error reading {name}: {LineNr} {line}')  
    if LineNr == 5:
      NLLand = ''
      try:
        SQL = f'SELECT `Nederlands` FROM `Landen` WHERE `Engels` = "{Name}"'
        cpe.execute( SQL )
        while True:
          row = cpe.fetchone()
          if row == None:
            break
          else:
            NLLand = row['Nederlands']
        cpe.execute(f'INSERT INTO `Posities` VALUES ({Pos}, "{Name}", {CurPoints}, {OldPoints}, 0, "{NLLand}")')
      except:
        print('Fout')
      LineNr = 0
    else:
      LineNr += 1
  conn_uitvoer.commit()

def GeefPositions():
  cpe = conn_uitvoer.cursor()
  cpd = conn_uitvoer.cursor()
  try:
    SQL = f'SELECT `EngelseLandsnaam`, `VorigeScore` FROM `Posities` ORDER BY `VorigeScore` DESC'
    cpe.execute( SQL )
    VorigeScore = 10000
    Plaats = 0
    Deltaplaats = 1
    while True:
      row = cpe.fetchone()
      if row == None:
        break
      else:
        Score = row['VorigeScore']
        Land  = row['EngelseLandsnaam'] 
        if Score == VorigeScore:
          Deltaplaats += 1
        else:
          Plaats = Plaats + Deltaplaats
          Deltaplaats = 1
        VorigeScore = Score
        SQL = f'UPDATE `Posities` SET `VorigePositie` = {Plaats} WHERE `EngelseLandsnaam` = "{Land}"'
        cpd.execute( SQL )
  except:
    pass      
  conn_uitvoer.commit()

def LeesInitialPositions(name):
  cpe = conn_uitvoer.cursor()
  f = open(name, 'r')
  for line in f:
    NL = line[:line.find('=')]
    line = line[line.find('=')+1:999].strip()
    pos = line[:line.find(' ')] 
    SQL = f'SELECT `EngelseLandsnaam` FROM `Posities` WHERE `Huidigepositie` = {pos}'
    cpe.execute( SQL )
    while True:
      row = cpe.fetchone()
      if row == None:
        break
      EngNaam = row['EngelseLandsnaam'].strip()
      try:
        cpe.execute(f'INSERT INTO `Landen` VALUES ("{EngNaam}" , "{NL}")')
      except:
        print (EngNaam, NL)
        pass    
  conn_uitvoer.commit()
  
def MaakFile(datum):
  jaar = datum[:4]
  maand = datum[4:6]
  dag = datum[6:8].lstrip('0')
  maand = get_monthname(maand)
  f = open(f'D://Wikipedia//FIFA-array_{datum}.txt', "w")
  f.write(f"| datum = {dag} {maand} {jaar}\n")
  cpe = conn_uitvoer.cursor()
  SQL = f'SELECT `HuidigePositie`, `VorigePositie`, `NederlandseLandsnaam` FROM `Posities` ORDER BY `HuidigePositie`'
  cpe.execute( SQL )
  while True:
    row = cpe.fetchone()
    if row == None:
      break
    HuidPos = row['HuidigePositie']
    VoriPos = row['VorigePositie']
    Naam = row['NederlandseLandsnaam'].strip()
    f.write(f"| {Naam} = {HuidPos} ")
    if HuidPos < VoriPos:
      f.write( "{{winst}} ")
      f.write(f"{VoriPos-HuidPos}")
      f.write( "\n")
    elif HuidPos > VoriPos:
      f.write( "{{verlies}} ")
      f.write(f"{HuidPos-VoriPos}")
      f.write( "\n")
    else:
      f.write( "{{stabiel}}\n")
  f.close()

LeesPositions(f'D://Wikipedia//FIFA-EN{datum}.txt')
# LeesInitialPositions('D://Wikipedia//FIFA-NL20210407.txt')
GeefPositions()
MaakFile(datum) 
