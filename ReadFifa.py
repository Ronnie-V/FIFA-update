import pywikibot
import sqlite3
import re
import sys
from unidecode import unidecode

if len(sys.argv) > 2 and len(sys.argv[1]) == 1 and len(sys.argv[2]) == 8:
  sexe = sys.argv[1]
  datum = sys.argv[2]
else:
  exit(f'Gebruik: {sys.argv[0]} M 20220210')

Targetdatabase = 'D://Wikipedia//Fifa-ranking.db'         
    
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

def OpmaakScore(score):
  score = str(score).replace(".", ",")  
  x=0
  while x < 10 and score[-3:-2] != ',':
    score = score + '0'
    x += 1
  return (score)

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
        SQL = f'SELECT `Nederlands`, `Code` FROM `Landen` WHERE `Engels` = "{Name}"'
        cpe.execute( SQL )
        while True:
          row = cpe.fetchone()
          if row == None:
            break
          else:
            NLLand = row['Nederlands']
            Code = row['Code']
        cpe.execute(f'INSERT INTO `Posities` VALUES ({Pos}, "{Name}", {CurPoints}, {OldPoints}, 0, "{NLLand}", "{Code}")')
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
  
def MaakFile(datum, sexe):
  jaar = datum[:4]
  maand = datum[4:6]
  dag = datum[6:8].lstrip('0')
  maand = get_monthname(maand)
  f = open(f'D://Wikipedia//FIFA-array_{datum}.txt', "w")
  if sexe == 'M':
    f2 = open(f'D://Wikipedia//FIFA-topmen_{datum}.txt', "w")
  else:
    f2 = open(f'D://Wikipedia//FIFA-topwomen_{datum}.txt', "w")
  f.write(f"| datum = {dag} {maand} {jaar}\n")
  f2.write(f"== Top 20 van de ranglijst per {dag} {maand} {jaar} ==\n")
  f2.write( '{| class="wikitable"\n' )
  f2.write( '!width=45|{{Afkorting|Pos|Positie}} ||width=30|+/- ||width=250|Land ||width=50|Punten\n' )
  cpe = conn_uitvoer.cursor()
  SQL = f'SELECT `HuidigePositie`, `VorigePositie`, `NederlandseLandsnaam`, `HuidigeScore`, `Code` FROM `Posities` ORDER BY `HuidigePositie`'
  cpe.execute( SQL )
  while True:
    row = cpe.fetchone()
    if row == None:
      break
    HuidPos = row['HuidigePositie']
    VoriPos = row['VorigePositie']
    HuidSco = OpmaakScore(row['HuidigeScore']) 
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
    if HuidPos <= 20:
      if row['Code'] == '':
        Code = Naam
      else:
        Code = '{{'+row['Code']+'f'
        if sexe != 'M':
          Code = Code + 'v'
        Code = Code + '}}'
      f2.write( "|-\n")
      f2.write(f"| '''{HuidPos}''' || ")
      if HuidPos < VoriPos:
        f2.write( "{{winst}} <sup>")
        f2.write(f"{VoriPos-HuidPos}")
        f2.write( "</sup>")
      elif HuidPos > VoriPos:
        f2.write( "{{verlies}} <sub>")
        f2.write(f"{HuidPos-VoriPos}")
        f2.write( "</sub>")
      else:
        f2.write( "{{stabiel}}")
      f2.write(f" || {Code} || {HuidSco}\n")

  f2.write( '|-\n')
  if sexe == 'M':
    f2.write( '| colspan=4 align="center" | <small>[https://www.fifa.com/fifa-world-ranking/men Complete ranglijst op fifa.com]</small>\n')
  else:
    f2.write(f'| colspan=4 align="center" | <small>[https://www.fifa.com/fifa-world-ranking/women?dateId=ranking_{datum} Complete ranglijst op fifa.com]</small>\n')
  f2.write( '|}\n')
  f2.close()
  f.close()

LeesPositions(f'D://Wikipedia//FIFA-EN{datum}.txt')
# LeesInitialPositions('D://Wikipedia//FIFA-NL20210407.txt')
GeefPositions()
MaakFile(datum, sexe) 
