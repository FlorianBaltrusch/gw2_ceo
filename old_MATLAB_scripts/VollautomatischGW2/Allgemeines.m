%% Warnung aus
warning('off','MATLAB:table:ModifiedAndSavedVarnames')
falscheeingabe = 'Nope!';

%% Allgemeine Buffs
AllgBuffs = readtable('AllgBuffs.xlsx');
Tabelle = readtable('Zuordnung.xlsx');

Base = sum(AllgBuffs.Base);
FerocityBase = sum(AllgBuffs.FeroBase);
Fury = sum(AllgBuffs.Fury);
Sigil = sum(AllgBuffs.Sigil);
JadeBot = sum(AllgBuffs.JadeBot);

Start = 2995 - Base - Fury;

%% Runen
Runen = readtable('RunesFood.xlsx');

Scholar = Runen.Scholar;
Dragonh = Runen.Dragonh;
Gole = Runen.Gole;
Deadeye = Runen.Deadeye;
Eagle = Runen.Eagle;
Infil = Runen.Infil;
Ranger = Runen.Ranger;

Butternut = Runen.Butternut;
Truffle = Runen.Truffle;
Curry = Runen.Curry;
%% Klassenwahl
while true
    fprintf('Bitte wählt Eure Klasse!\n[1] Elementarmagier\n[2] Mesmer\n[3] Nekromant\n[4] Ingenieur\n[5] Waldläufer\n[6] Dieb\n[7] Wächter\n[8] Widergänger\n[9] Krieger\n');
    Klasse = input('');
    if isnumeric(Klasse) && mod(Klasse, 1) == 0 && Klasse >= 1 && Klasse <= 9
        break;
    else
        fprintf('Bitte gebt eine natürliche Zahl kleiner als 10 ein.\n');
    end
end

%% DPS oder Open World
while true
    fprintf('Wo wollt Ihr spielen?\n[1] Raids/Strikes\n[2] Open World\n');
    Umgebung = input('');
    if isnumeric(Umgebung) && mod(Umgebung, 1) == 0 && Umgebung >= 1 && Umgebung <= 2
        break;
    else
        fprintf('Bitte gebt eine natürliche Zahl kleiner als 3 ein.\n');
    end
end

%% Waffentyp einhändig oder zweihändig
while true
    fprintf('Verwendet Ihr eine einhändige oder zweihändige Waffe?\n[1] Einhändig\n[2] Zweihändig\n');
    Waffentyp = input('');
    if isnumeric(Waffentyp) && mod(Waffentyp, 1) == 0 && Waffentyp >= 1 && Waffentyp <= 2
        break;
    else
        fprintf('Bitte gebt eine natürliche Zahl kleiner als 3 ein.\n');
    end
end

%% Gear Seltenheit
while true
    fprintf('Welche Seltenheit hat Eure Ausrüstung?\n[1] Vollständig exotisch\n[2] Exotisch mit einer legendären Waffe\n[3] Vollständig aufgestiegen\n');
    Seltenheit = input('');
    if isnumeric(Seltenheit) && mod(Seltenheit, 1) == 0 && Seltenheit >= 1 && Seltenheit <= 3
        break;
    else
        fprintf('Bitte gebt eine natürliche Zahl kleiner als 4 ein.\n');
    end
end

%% Food
while true
    fprintf('Welches Nahrungsmittel verwendet Ihr?\n[1] Mit 100 Präzision\n[2] Mit 70 Präzision\n[3] Ohne Präzision\n[4] Recommended\n');
    Nahrungsmittel = input('');
    if isnumeric(Nahrungsmittel) && mod(Nahrungsmittel, 1) == 0 && Nahrungsmittel >= 1 && Nahrungsmittel <= 4
    break;
    else
        fprintf('Bitte gebt eine natürliche Zahl kleiner als 5 ein.\n');
    end
end

if Nahrungsmittel == 1
    PreciFood = Curry(2);
    PowerFood = Curry(1);
    FeroFood = Curry(3);
elseif (Nahrungsmittel == 2) || (Nahrungsmittel == 4)
    PreciFood = Truffle(2);
    PowerFood = Truffle(1);
    FeroFood = Truffle(3);
elseif Nahrungsmittel == 3
    PreciFood = Butternut(2);
    PowerFood = Butternut(1);
    FeroFood = Butternut(3);
else 
    fprintf(falscheeingabe)
end

%% Utility 
while true
    fprintf('Verwendet Ihr die überlegenden Wetzsteine als Verbesserung?\n[1] Ja\n[2] Nein\n[3] Recommended\n');
    Wetzstein = input('');
    if isnumeric(Wetzstein) && mod(Wetzstein, 1) == 0 && Wetzstein >= 1 && Wetzstein <= 3
        break;
    else
        fprintf('Bitte gebt eine natürliche Zahl kleiner als 4 ein.\n');
    end
end

if Wetzstein == 1 || Wetzstein == 3
    Utility = 1;
elseif Wetzstein == 2
    Utility = 0;
else
    fprintf(falscheeingabe)
end

%% Might
while true
    fprintf('Habt Ihr 25 stacks Macht?\n[1] Ja\n[2] Nein\n[3] Recommended\n');
    Macht = input('');
    if isnumeric(Macht) && mod(Macht, 1) == 0 && Macht >= 1 && Macht <= 3
        break;
    else
        fprintf('Bitte gebt eine natürliche Zahl kleiner als 4 ein.\n');
    end
end

if Macht == 1 || Macht == 3
    Macht = 1;
elseif Macht == 2
    Macht = 0;
else
    printf(falscheeingabe)
end

%% Zahlen importieren
Daten = readtable('Stats_vollauto.xlsx');

Pc3Maj1h = Daten.x3pcMaj1h;
Pc3Maj2h = Daten.x3pcMaj2h;
Pc3Maj1hL = Daten.x3pcMaj1hL;
Pc3Maj2hL = Daten.x3pcMaj2hL;

Pc3Min1h = Daten.x3pcMin1h;
Pc3Min2h = Daten.x3pcMin2h;
Pc3Min1hL = Daten.x3pcMin1hL;
Pc3Min2hL = Daten.x3pcMin2hL;

Pc4Maj1h = Daten.x4pcMaj1h;
Pc4Maj2h = Daten.x4pcMaj2h;
Pc4Maj1hL = Daten.x4pcMaj1hL;
Pc4Maj2hL = Daten.x4pcMaj2hL;

Pc4Min1h = Daten.x4pcMin1h;
Pc4Min2h = Daten.x4pcMin2h;
Pc4Min1hL = Daten.x4pcMin1hL;
Pc4Min2hL = Daten.x4pcMin2hL;

%% Gear Auswahl, bei Maj L sind Infusionen dabei
if Umgebung == 1 && Waffentyp == 1 && Seltenheit == 1
    Highgear = Pc3Maj1h;
    Lowgear = Pc3Min1h;
    Vitality = Base + JadeBot;
elseif Umgebung == 1 && Waffentyp == 2 && Seltenheit == 1
    Highgear = Pc3Maj2h;
    Lowgear = Pc3Min2h;
    Vitality = Base + JadeBot;
elseif Umgebung == 1 && Waffentyp == 1 && Seltenheit == 2
    Highgear = Pc3Maj1hL;
    Lowgear = Pc3Min1hL;
    Vitality = Base + JadeBot;
elseif Umgebung == 1 && Waffentyp == 2 && Seltenheit == 2
    Highgear = Pc3Maj2hL;
    Lowgear = Pc3Min2hL;
    Vitality = Base + JadeBot;
elseif Umgebung == 2 && Waffentyp == 1 && Seltenheit == 1
    Highgear = Pc4Maj1h;
    Lowgear = Pc4Min1h;
    Vitality = Base + JadeBot + sum(Lowgear);
elseif Umgebung == 2 && Waffentyp == 2 && Seltenheit == 1
    Highgear = Pc4Maj2h;
    Lowgear = Pc4Min2h;
    Vitality = Base + JadeBot + sum(Lowgear);
elseif Umgebung == 2 && Waffentyp == 1 && Seltenheit == 2
    Highgear = Pc4Maj1hL;
    Lowgear = Pc4Min1hL;
    Vitality = Base + JadeBot + sum(Lowgear);
elseif Umgebung == 2 && Waffentyp == 2 && Seltenheit == 2
    Highgear = Pc4Maj2hL;
    Lowgear = Pc4Min2hL;
    Vitality = Base + JadeBot + sum(Lowgear);
else 
    fprintf(falscheeingabe)
end