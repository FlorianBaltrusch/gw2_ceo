%% Wahl der Elitespezialisierung
while true
    fprintf('Bitte wählt nun Eure Elitespezialisierung.\n[1] Kern-Spezialisierung\n[2] Sturmbote\n[3] Weber\n[4] Katalysierer\n');
    Spezialisierung = input('');
    if isnumeric(Spezialisierung) && mod(Spezialisierung, 1) == 0 && Spezialisierung >= 1 && Spezialisierung <= 4
        break;
    else
        fprintf('Bitte gebt eine natürliche Zahl kleiner als 5 ein.\n');
    end
end

if Spezialisierung == 1 || Spezialisierung == 2 || Spezialisierung == 3
    % CatMod = 1;
elseif Spezialisierung == 4
    fprintf('UPDATE 29.11.23 abwarten')
    return;
    % while true
    %     fprintf('Über viele Stapel "Elementar-Ermächtigung" verfügt Ihr?\n');
    %     ElementarErmaechtigung = input('');
    %     if isnumeric(ElementarErmaechtigung) && mod(ElementarErmaechtigung, 1) == 0 && ElementarErmaechtigung >= 0 && ElementarErmaechtigung <= 10
    %         break;
    %     else
    %         fprintf('Bitte gebt eine ganze Zahl zwischen 0 und 10 ein.\n');
    %     end
    % end
    % fprintf('Verwendet Ihr die Eigenschaft "Gestärkte Ermächtigung"?\n[1] Ja\n[2] Nein\n');
    % GestaerkteErmaechtigung = input('');
    % while true
    %     if isnumeric(GestaerkteErmaechtigung) && mod(GestaerkteErmaechtigung, 1) == 0 && GestaerkteErmaechtigung >= 1 && GestaerkteErmaechtigung <= 2
    %         break;
    %     else
    %         fprintf('Bitte gebt eine natürliche Zahl kleiner als 3 ein.\n');
    %     end
    % end
    % if GestaerkteErmaechtigung == 1 && ElementarErmaechtigung == 10
    %     CatMod = 1.2;
    % elseif GestaerkteErmaechtigung == 1 && ElementarErmaechtigung < 10
    %     Catmod = 1 + ElementarErmaechtigung/100;
    % elseif GestaerkteErmaechtigung == 2
    %     Catmod = 1 + ElementarErmaechtigung/100;
    % else
    %     fprintf(falscheingabe)
    % end
else
    fprintf(falscheingabe)
end

%% Ele Buffs
% Buffs, die man nur in einer Einstimmung hat, wurden vernachlässigt.
EleBuffs = readtable('EleBuffs.xlsx');
% Crit Chance
SignetofFire = sum(EleBuffs.SignetofFire);
ElementsofRage = 0.13*Vitality; % Weaver
ZephyrsSpeed = sum(EleBuffs.ZephyrsSpeed); % Luft
SuperiorElements = sum(EleBuffs.SuperiorElements); % Weaver
% Power
if Macht == 0
    Might = 0;
elseif Macht == 1
    Might = sum(EleBuffs.Might);
else
    fprintf(falscheingabe)
end
PowerOverwhelming1 = sum(EleBuffs.PowerOverwhelming1);
ElementalPolyphony1 = sum(EleBuffs.ElementalPolyphony1); % Weaver
% Crit Damage
RagingStorm = sum(EleBuffs.RagingStorm);
AeromancersTraining1 = sum(EleBuffs.AeromancersTraining1);
FreshAir = sum(EleBuffs.FreshAir);
ElementalPolyphony2 = sum(EleBuffs.ElementalPolyphony2);
% FerociousWinds = 0.07*Percision;

%% Bestimmung der Precision Modifier
while true
    fprintf('Verwendet Ihr das Siegel des Feuers?\n[1] Ja\n[2] Nein\n[3] Recommended\n');
    SiegeldesFeuers = input('');
    if isnumeric(SiegeldesFeuers) && mod(SiegeldesFeuers, 1) == 0 && SiegeldesFeuers >= 1 && SiegeldesFeuers <= 3
        break;
    else
        fprintf('Bitte gebt eine natürliche Zahl kleiner als 4 ein.\n');
    end
end

if SiegeldesFeuers == 1 || SiegeldesFeuers == 3
elseif SiegeldesFeuers == 2
    SignetofFire = 0;
else
    fprintf(falscheeingabe);
end

while true
    fprintf('Verwendet Ihr die Spezialisierung "Luft"?\n[1] Ja\n[2] Nein\n[3] Recommended\n');
    Luft = input('');
    if isnumeric(Luft) && mod(Luft, 1) == 0 && Luft >= 1 && Luft <= 3
        break;
    else
        fprintf('Bitte gebt eine natürliche Zahl kleiner als 4 ein.\n');
    end
end

if Luft == 1 || Luft == 3
    while true
        fprintf('Verwendet Ihr die Eigenschaft "Tobender Sturm"?\n[1] Ja\n[2] Nein\n[3] Recommended\n');
        TobenderSturm = input('');
        if isnumeric(TobenderSturm) && mod(TobenderSturm, 1) == 0 && TobenderSturm >= 1 && TobenderSturm <= 3
            break;
        else
            fprintf('Bitte gebt eine natürliche Zahl kleiner als 4 ein.\n');
        end
    end
    if TobenderSturm == 1 
    elseif TobenderSturm == 2 || TobenderSturm == 3
        RagingStorm = 0;
    else
        fprintf(falscheeingabe);
    end
    while true
        fprintf('Verwendet Ihr die Eigenschaft "Frische Luft"?\n[1] Ja\n[2] Nein\n');
        FrischeLuft = input('');
        if isnumeric(FrischeLuft) && mod(FrischeLuft, 1) == 0 && FrischeLuft >= 1 && FrischeLuft <= 2
            break;
        else
            fprintf('Bitte gebt eine natürliche Zahl kleiner als 3 ein.\n');
        end
    end
    if FrischeLuft == 1 
    elseif FrischeLuft == 2 
        FreshAir = 0;
    else
        fprintf(falscheeingabe);
    end
elseif Luft == 2
    ZephyrsSpeed = 0;
    RagingStorm = 0;
    AeromancersTraining1 = 0;
    FreshAir = 0; 
else
    fprintf(falscheeingabe);
end

if Spezialisierung == 1 || Spezialisierung == 2 || Spezialisierung == 4
    ElementalPolyphony1 = 0;
    ElementalPolyphony2 = 0;
    SuperiorElements = 0;
    ElementsofRage = 0;
elseif Spezialisierung == 3
    while true
        fprintf('Verwendet Ihr die Eigenschaft "Überlegene Elemente"?\n[1] Ja\n[2] Nein\n[3] Recommended\n');
        UeberlegeneElemente = input('');
        if isnumeric(UeberlegeneElemente) && mod(UeberlegeneElemente, 1) == 0 && UeberlegeneElemente >= 1 && UeberlegeneElemente <= 3
            break;
        else
            fprintf('Bitte gebt eine natürliche Zahl kleiner als 4 ein.\n');
        end
    end
    if UeberlegeneElemente == 1 || UeberlegeneElemente == 3
    elseif UeberlegeneElemente == 2
        SuperiorElements = 0;
    else
        fprintf(falscheeingabe);
    end
    while true
        fprintf('Verwendet Ihr die Eigenschaft "Elemente der Rage"?\n[1] Ja\n[2] Nein\n[3] Recommended\n');
        ElementederRage = input('');
        if isnumeric(ElementederRage) && mod(ElementederRage, 1) == 0 && ElementederRage >= 1 && ElementederRage <= 3
            break;
        else
            fprintf('Bitte gebt eine natürliche Zahl kleiner als 4 ein.\n');
        end
    end
    if ElementederRage == 1 || ElementederRage == 3
    elseif ElementederRage == 2
        ElementsofRage = 0;
    else
        fprintf(falscheeingabe);
    end
else
    fprintf(falscheeingabe);
end

%% Bestimung der Power Modifier
while true
    fprintf('Verwendet Ihr die Eigenschaft "Überwältigende Kraft"?\n[1] Ja\n[2] Nein\n[3] Recommended\n');
    UeberwaeltigendeKraft = input('');
    if isnumeric(UeberwaeltigendeKraft) && mod(UeberwaeltigendeKraft, 1) == 0 && UeberwaeltigendeKraft >= 1 && UeberwaeltigendeKraft <= 3
        break;
    else
        fprintf('Bitte gebt eine natürliche Zahl kleiner als 4 ein.\n');
    end
end

if (UeberwaeltigendeKraft == 1 || UeberwaeltigendeKraft == 3) && Macht == 0
    PowerOverwhelming1 = 0;
elseif (UeberwaeltigendeKraft == 1 || UeberwaeltigendeKraft == 3) && Macht == 1
elseif UeberwaeltigendeKraft == 2
    PowerOverwhelming1 = 0;
else
    fprintf(falscheeingabe);
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

%% Precision bestimmen für Ferocious Winds

%% Ferocious Winds
FerociousWinds = 0.07*Percision;

if Luft == 1 || Luft == 3
    while true
        fprintf('Verwendet Ihr die Eigenschaft "Wilde Winde"?\n[1] Ja\n[2] Nein\n[3] Recommended\n');
        WildeWinde = input('');
        if isnumeric(WildeWinde) && mod(WildeWinde, 1) == 0 && WildeWinde >= 1 && WildeWinde <= 3
            break;
        else
            fprintf('Bitte gebt eine natürliche Zahl kleiner als 4 ein.\n');
        end
    end
    if WildeWinde == 1 || WildeWinde == 3
    elseif WildeWinde == 2
        FerociousWinds = 0;
    else
        fprintf(falscheeingabe);
    end
elseif Luft == 2
    FerociousWinds = 0;
else
    fprintf(falscheeingabe);
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
