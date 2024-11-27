%% Mesmer Buffs
MesmerBuffs = readtable('MesmerBuffs.xlsx');
% Crit Chance
DangerTime = sum(MesmerBuffs.DangerTime); % Chrono, not recommended
QuietIntensity1 = sum(MesmerBuffs.QuietIntensity1); % Virtuoso, Minor
% Power
if Macht == 0
    Might = 0;
elseif Macht == 1
    Might = sum(MesmerBuffs.Might);
else
    fprintf(falscheingabe)
end
% Crit Damage
FencersFinesse = sum(MesmerBuffs.FencersFinesse);
SuperiorityComplex = sum(MesmerBuffs.SuperiorityComplex);
ImprovedAlacrity = sum(MesmerBuffs.ImprovedAlacrity); % Chrono
QuietIntensity2 = 0.1*Vitality; % Virtuoso, Minor

%% Wahl der Elitespezialisierung
while true
    fprintf('Bitte wählt nun Eure Elitespezialisierung.\n[1] Kern-Spezialisierung\n[2] Chronomant\n[3] Illusionist\n[4] Virtuose\n');
    Spezialisierung = input('');
    if isnumeric(Spezialisierung) && mod(Spezialisierung, 1) == 0 && Spezialisierung >= 1 && Spezialisierung <= 4
        break;
    else
        fprintf('Bitte gebt eine natürliche Zahl kleiner als 5 ein.\n');
    end
end

%% Bestimmung der Precision Modifier
ZeitderGefahren = 0; % Für Improved Alacrity

if Spezialisierung == 1
    DangerTime = 0;
    QuietIntensity1 = 0;
    QuietIntensity2 = 0;
    ImprovedAlacrity = 0;
elseif Spezialisierung == 2
    while true
        fprintf('Verwendet Ihr die Eigenschaft "Zeit der Gefahren"?\n[1] Ja\n[2] Nein\n[3] Recommended\n');
        ZeitderGefahren = input('');
        if isnumeric(ZeitderGefahren) && mod(ZeitderGefahren, 1) == 0 && ZeitderGefahren >= 1 && ZeitderGefahren <= 3
            break;
        else
            fprintf('Bitte gebt eine natürliche Zahl kleiner als 4 ein.\n');
        end
    end
    if ZeitderGefahren == 1
    elseif (ZeitderGefahren == 2) || (ZeitderGefahren == 3)
        DangerTime = 0;
    else 
        fprintf(falscheeingabe);
    end
    QuietIntensity1 = 0;
    QuietIntensity2 = 0;
elseif Spezialisierung == 3
    DangerTime = 0;
    QuietIntensity1 = 0;
    QuietIntensity2 = 0;
    ImprovedAlacrity = 0;
elseif Spezialisierung == 4
    DangerTime = 0;
    ImprovedAlacrity = 0;
else 
    fprintf(falscheeingabe);
end

%% Bestimung der Power Modifier

%% Bestimung der Ferocity Modifier
while true
    fprintf('Verwendet Ihr die Eigenschaft "Geschick des Fechters"?\n[1] Ja\n[2] Nein\n[3] Recommended\n');
    GeschickdesFechters = input('');
    if isnumeric(GeschickdesFechters) && mod(GeschickdesFechters, 1) == 0 && GeschickdesFechters >= 1 && GeschickdesFechters <= 3
        break;
    else
        fprintf('Bitte gebt eine natürliche Zahl kleiner als 4 ein.\n');
    end
end

if GeschickdesFechters == 1 || GeschickdesFechters == 3
elseif GeschickdesFechters == 2
    FencersFinesse = 0;
else
    fprintf(falscheingabe);
end

while true
    fprintf('Verwendet Ihr die Eigenschaft "Überlegenheitskomplex"?\n[1] Ja\n[2] Nein\n[3] Recommended\n');
    Ueberlegenheitskomplex = input('');
    if isnumeric(Ueberlegenheitskomplex) && mod(Ueberlegenheitskomplex, 1) == 0 && Ueberlegenheitskomplex >= 1 && Ueberlegenheitskomplex <= 3
        break;
    else
        fprintf('Bitte gebt eine natürliche Zahl kleiner als 4 ein.\n');
    end
end

if Ueberlegenheitskomplex == 1 || Ueberlegenheitskomplex == 3
elseif Ueberlegenheitskomplex == 2
    SuperiorityComplex = 1;
else
    fprintf(falscheingabe);
end

VerbesserterTatendrang = 0; % Für Danger Time

if ZeitderGefahren == 0 || ZeitderGefahren == 1
elseif ZeitderGefahren == 2 || ZeitderGefahren == 3
    while true
        fprintf('Verwendet Ihr die Eigenschaft "Verbesserter Tatendrang"?\n[1] Ja\n[2] Nein\n[3] Recommended\n');
        VerbesserterTatendrang = input('');
        if isnumeric(VerbesserterTatendrang) && mod(VerbesserterTatendrang, 1) == 0 && VerbesserterTatendrang >= 1 && VerbesserterTatendrang <= 3
            break;
        else
            fprintf('Bitte gebt eine natürliche Zahl kleiner als 4 ein.\n');
        end
    end
else
    fprintf(falscheingabe);
end

if VerbesserterTatendrang == 1 || VerbesserterTatendrang == 3
elseif VerbesserterTatendrang == 0 || VerbesserterTatendrang == 2
    ImprovedAlacrity = 0;
else
    fprintf(falscheingabe);
end

%% Bestimmung des Targets
Testtarget1 = Start - PreciFood - Sigil - DangerTime - QuietIntensity1 - sum(Highgear);
Testtarget2 = Start - PreciFood - Sigil - DangerTime - QuietIntensity1 - sum(Lowgear);

if Umgebung == 1
    Basegear = 'Berserker';
    Testtarget = Testtarget2;
elseif Umgebung == 2
    if abs(Testtarget1) < abs(Testtarget2)
        Basegear = 'Marauder';
        Testtarget = Testtarget1;
    elseif abs(Testtarget1) >= abs(Testtarget2)
        Basegear = 'Dragon';
        Testtarget = Testtarget2;
    else
        fprintf(falscheeingabe);
    end
else
    fprintf(falscheeingabe);
end

if strcmp(Basegear, 'Berserker') && Testtarget < 0
    Testtarget = Testtarget2 + Sigil;
    Sigil = 0;
    VerwendetesSigil = 'Impact/Night';
elseif strcmp(Basegear, 'Dragon') && Testtarget < 0
    Testtarget = Testtarget2 + Sigil;
    Sigil = 0;
    VerwendetesSigil = 'Impact/Night';
else
    VerwendetesSigil = 'Accuracy';
end

%% Stats ohne Rune aber Food
if strcmp(Basegear, 'Berserker') && Testtarget < 0
    Power = Base + Might + sum(Highgear) + PowerFood;
    Ferocityequi = FencersFinesse + ImprovedAlacrity + QuietIntensity2 + sum(Lowgear) + FeroFood;
    SuperiorityComplex = (SuperiorityComplex - 1)*(Ferocityequi + FerocityBase);
    Ferocityequi = Ferocityequi + SuperiorityComplex;
    Precision = Base + sum(Lowgear) + Testtarget + PreciFood;
    Ferocity = FencersFinesse + QuietIntensity2 + sum(Lowgear) + FeroFood;
elseif strcmp(Basegear, 'Berserker') && Testtarget >= 0
    Power = Base + Might + sum(Highgear) - Testtarget + PowerFood;
    Ferocityequi = FencersFinesse + ImprovedAlacrity + QuietIntensity2 + sum(Lowgear) + FeroFood;
    SuperiorityComplex = (SuperiorityComplex - 1)*(Ferocityequi + FerocityBase);
    Ferocityequi = Ferocityequi + SuperiorityComplex;
    Precision = Base + sum(Lowgear) + Testtarget + PreciFood;
    Ferocity = FencersFinesse + QuietIntensity2 + sum(Lowgear) + FeroFood;
elseif strcmp(Basegear, 'Marauder')
    Power = Base + Might + sum(Highgear) + PowerFood;
    Ferocityequi = FencersFinesse + ImprovedAlacrity + QuietIntensity2 + sum(Lowgear) - Testtarget + FeroFood;
    SuperiorityComplex = (SuperiorityComplex - 1)*(Ferocityequi + FerocityBase);
    Ferocityequi = Ferocityequi + SuperiorityComplex;
    Precision = Base + sum(Highgear) + Testtarget + PreciFood;
    Ferocity = FencersFinesse + QuietIntensity2 + sum(Lowgear) - Testtarget + FeroFood;
elseif strcmp(Basegear, 'Dragon')
    Power = Base + Might + sum(Highgear) + PowerFood;
    Ferocityequi = FencersFinesse + ImprovedAlacrity + QuietIntensity2 + sum(Highgear) - Testtarget + FeroFood;
    SuperiorityComplex = (SuperiorityComplex - 1)*(Ferocityequi + FerocityBase);
    Ferocityequi = Ferocityequi + SuperiorityComplex;
    Precision = Base + sum(Lowgear) + Testtarget + PreciFood;
    Ferocity = FencersFinesse + QuietIntensity2 + sum(Highgear) - Testtarget + FeroFood;
else
    fprintf(falscheingabe);
end
