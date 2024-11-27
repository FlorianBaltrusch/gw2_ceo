%% Runen und Food Modifier
if Utility == 0 && Umgebung == 1
    Fullkraft = Runen.Pc3Infilmod(1);
    Halfkraft= Runen.Pc3Deadeyemod(1);
    Halfwild = Runen.Pc3Scholarmod(1);
    Fullwild = Runen.Pc3Dragonhmod(1);
elseif Utility == 1 && Umgebung == 1
    Fullkraft = sum(Runen.Pc3Infilmod(1));
    Halfkraft= sum(Runen.Pc3Deadeyemod(1));
    Halfwild = sum(Runen.Pc3Scholarmod(1));
    Fullwild = sum(Runen.Pc3Dragonhmod(1));
elseif Utility == 0 && Umgebung == 2
    Kraftmod = abs(Runen.Pc4Scholarmod(1));
    Mischmod = abs(Runen.Pc4Dragonhmod(1));
    Wildmod = abs(Runen.Pc4Golemod(1));
elseif Utility == 1 && Umgebung == 2
    Kraftmod = abs(sum(Runen.Pc4Scholarmod));
    Mischmod = abs(sum(Runen.Pc4Dragonhmod));
    Wildmod = abs(sum(Runen.Pc4Golemod));
else
    fprintf(falscheeingabe)
end

%% Wetzsteine Utility
if Utility == 0
elseif Utility == 1
    Power = Power + 0.03*Precision + 0.06*Ferocity;
else
    fprintf(falscheingabe);
end

%% Effective Power für 100% Crit
% (Power + 1)*(1.5 + Ferocity/1500) = Power*(1.5 + (Fercity + 1)/1500)
% => Power = Ferocity + 2250
EPBalance = Power - Ferocityequi - 2250; % Negative heißt zu wenig Kraft

if Umgebung == 1
    A3Pc = (Fullkraft + Halfkraft)/2;
    B3Pc = (Halfkraft + Halfwild)/2;
    C3Pc = (Halfwild + Fullwild)/2;
    if EPBalance <= -A3Pc
        Runetype = 'Fullkraft';
    elseif EPBalance > -A3Pc && EPBalance <= -B3Pc
        Runetype = 'Halfkraft';
    elseif EPBalance > -B3Pc && EPBalance <= -C3Pc
        Runetype = 'Halfwild';
    elseif EPBalance > -C3Pc
        Runetype = 'Fullwild';
    else
        fprintf(falscheingabe);
    end
elseif Umgebung == 2
    A4Pc = (Mischmod + Wildmod)/2; % 300 ohne Wetzsteine 4Pc
    B4Pc = (Kraftmod + Mischmod)/2; % 125 ohne Wetzsteine 4Pc
    if EPBalance > A4Pc
        Runetype = 'Wildheit';
    elseif EPBalance <= A4Pc && EPBalance > B4Pc
        Runetype = 'Mischung';
    elseif EPBalance <= B4Pc
        Runetype = 'Kraft';
    else
        fprintf(falscheingabe);
    end
else
    fprintf(falscheingabe);
end
% Ohne Dragonhunter
if Umgebung == 1
elseif Umgebung == 2
    AOD4Pc = (Kraftmod + Wildmod)/2;
    if EPBalance > AOD4Pc
        RunetypeOD = 'Wildheit';
    elseif EPBalance <= AOD4Pc
        RunetypeOD = 'Kraft';
    else
        fprintf(falscheingabe);
    end
else
    fprintf(falscheingabe);
end

%% Auswahl der Rune
if strcmp(Basegear, 'Dragon')
    if Testtarget < Scholar(2)
        Fall = 'Fall 1';
        fprintf('Leider sind genau 100 %% Crit Chance nicht erreichbar. Zieht in Betracht, weniger Modifier zu verwenden.\n')
    elseif Testtarget >= Scholar(2) && Testtarget < Gole(2)
        target = Testtarget;
        Fall = 'Fall 2';
    elseif Testtarget >= Gole(2) && Testtarget < Deadeye(2)
        target = [Testtarget, Testtarget - Gole(2)];
        Fall = 'Fall 3';
    elseif Testtarget >= Deadeye(2) && Testtarget < Eagle(2)
        target = [Testtarget, Testtarget - Gole(2), Testtarget - Deadeye(2)];
        Fall = 'Fall 4';
    elseif Testtarget >= Eagle(2) && Testtarget < Infil(2)
        target = [Testtarget, Testtarget - Deadeye(2), Testtarget - Eagle(2)];
        Fall = 'Fall 5';
    elseif Testtarget >= Infil(2) && Testtarget < Ranger(2)
        target = [Testtarget, Testtarget - Eagle(2), Testtarget - Infil(2)];
        Fall = 'Fall 6';
    elseif Testtarget >= Ranger(2)
        target = [Testtarget, Testtarget - Infil(2), Testtarget - Ranger(2)];
        Fall = 'Fall 7';
    else
        fprintf(falscheingabe)
    end
elseif strcmp(Basegear, 'Marauder')
    if Testtarget <= Scholar(2)
        target = [Testtarget, Testtarget - Gole(2)];
        Fall = 'Fall 8';
    elseif Testtarget > Scholar(2) && Testtarget <= Gole(2)
        target = [Testtarget - Gole(2), Testtarget - Deadeye(2)];
        Fall = 'Fall 9';
    elseif Testtarget > Gole(2) && Testtarget <= Deadeye(2)
        target = [Testtarget - Deadeye(2), Testtarget - Eagle(2)];
        Fall = 'Fall 10';
    elseif Testtarget > Deadeye(2) && Testtarget <= Eagle(2)
        target = [Testtarget - Eagle(2), Testtarget - Infil(2)];
        Fall = 'Fall 11';
    elseif Testtarget > Eagle(2) && Testtarget <= Infil(2)
        target = [Testtarget - Infil(2), Testtarget - Ranger(2)];
        Fall = 'Fall 12';
    elseif Testtarget > Infil(2) && Testtarget <= Ranger(2)
        target = Testtarget - Ranger(2);
        Fall = 'Fall 13';
    elseif Testtarget > Ranger(2)
        Fall = 'Fall 14';
        fprintf('Leider sind genau 100 %% Crit Chance nicht erreichbar. Zieht in Betracht, mehr Modifier zu verwenden.\n')
    else
        fprintf(falscheingabe)
    end
elseif strcmp(Basegear, 'Berserker')
    if Testtarget < Gole(2)
        target = Testtarget;
        Fall = 'Fall 15';
    elseif Testtarget >= Gole(2) && Testtarget < Deadeye(2)
        target = [Testtarget, Testtarget - Gole(2)];
        Fall = 'Fall 16'; % Dragonh = Gole
    elseif Testtarget >= Deadeye(2) && Testtarget < Eagle(2)
        target = [Testtarget, Testtarget - Gole(2), Testtarget - Deadeye(2)];
        Fall = 'Fall 17';
    elseif Testtarget >= Eagle(2) && Testtarget < Infil(2)
        target = [Testtarget - Gole(2), Testtarget - Deadeye(2), Testtarget - Eagle(2)];
        Fall = 'Fall 18';
    elseif Testtarget >= Infil(2) && Testtarget < Ranger(2)
        target = [Testtarget - Gole(2), Testtarget - Deadeye(2), Testtarget - Eagle(2), Testtarget - Infil(2)];
        Fall = 'Fall 19';
    elseif Testtarget >= Ranger(2)
        target = [Testtarget - Gole(2), Testtarget - Eagle(2), Testtarget - Infil(2), Testtarget - Ranger(2)];
        Fall = 'Fall 20';
    else
        fprintf(falscheingabe)
    end
else
    fprintf(falscheingabe)
end

%% Fallunterscheidung
if strcmp(Fall, 'Fall 1')
    fprintf('Verwendet full Dragon Gear oder weniger modifier.\n')
elseif strcmp(Fall, 'Fall 2')
    if strcmp(Runetype, 'Kraft')
        VerwendeteRune = 'Scholar';
    elseif strcmp(Runetype, 'Mischung') || strcmp(Runetype, 'Wildheit')
        VerwendeteRune = 'Dragonhunter';
    else
        fprintf(falscheingabe)
    end
elseif strcmp(Fall, 'Fall 3')
    if strcmp(Runetype, 'Kraft')
        VerwendeteRune = 'Scholar';
        target = target(1);
    elseif strcmp(Runetype, 'Mischung')
        VerwendeteRune = 'Dragonhunter';
        target = target(1);
    elseif strcmp(Runetype, 'Wildheit')
        VerwendeteRune = 'Golemancer';
        target = target(2);
    else
        fprintf(falscheingabe)
    end
elseif strcmp(Fall, 'Fall 4')
    if strcmp(Runetype, 'Kraft')
        VerwendeteRune = 'Deadeye';
        target = target(3);
    elseif strcmp(Runetype, 'Mischung')
        VerwendeteRune = 'Dragonhunter';
        target = target(1);
    elseif strcmp(Runetype, 'Wildheit')
        VerwendeteRune = 'Golemancer';
        target = target(2);
    else
        fprintf(falscheingabe)
    end
elseif strcmp(Fall, 'Fall 5')
    if strcmp(Runetype, 'Kraft')
        VerwendeteRune = 'Deadeye';
        target = target(2);
    elseif strcmp(Runetype, 'Mischung')
        VerwendeteRune = 'Dragonhunter';
        target = target(1);
    elseif strcmp(Runetype, 'Wildheit')
        VerwendeteRune = 'Eagle';
        target = target(3);
    else
        fprintf(falscheingabe)
    end
elseif strcmp(Fall, 'Fall 6')
    if strcmp(Runetype, 'Kraft')
        VerwendeteRune = 'Infiltration';
        target = target(3);
    elseif strcmp(Runetype, 'Mischung')
        VerwendeteRune = 'Dragonhunter';
        target = target(1);
    elseif strcmp(Runetype, 'Wildheit')
        VerwendeteRune = 'Eagle';
        target = target(2);
    else
        fprintf(falscheingabe)
    end
elseif strcmp(Fall, 'Fall 7')
    if strcmp(Runetype, 'Kraft')
        VerwendeteRune = 'Infiltration';
        target = target(2);
    elseif strcmp(Runetype, 'Mischung')
        VerwendeteRune = 'Dragonhunter';
        target = target(1);
    elseif strcmp(Runetype, 'Wildheit')
        VerwendeteRune = 'Ranger';
        target = target(3);
    else
        fprintf(falscheingabe)
    end
elseif strcmp(Fall, 'Fall 8')
    if strcmp(Runetype, 'Kraft')
        VerwendeteRune = 'Scholar';
        target = target(1);
    elseif strcmp(Runetype, 'Mischung')
        VerwendeteRune = 'Dragonhunter';
        target = target(1);
    elseif strcmp(Runetype, 'Wildheit')
        VerwendeteRune = 'Golemancer';
        target = target(2);
    else
        fprintf(falscheingabe)
    end
elseif strcmp(Fall, 'Fall 9')
    if strcmp(RunetypeOD, 'Kraft')
        VerwendeteRune = 'Deadeye';
        target = target(2);
    elseif strcmp(RunetypeOD, 'Wildheit')
        VerwendeteRune = 'Golemancer';
        target = target(1);
    else
        fprintf(falscheingabe)
    end
elseif strcmp(Fall, 'Fall 10')
    if strcmp(RunetypeOD, 'Kraft')
        VerwendeteRune = 'Deadeye';
        target = target(1);
    elseif strcmp(RunetypeOD, 'Wildheit')
        VerwendeteRune = 'Eagle';
        target = target(2);
    else
        fprintf(falscheingabe)
    end
elseif strcmp(Fall, 'Fall 11')
    if strcmp(RunetypeOD, 'Kraft')
        VerwendeteRune = 'Infiltration';
        target = target(2);
    elseif strcmp(RunetypeOD, 'Wildheit')
        VerwendeteRune = 'Eagle';
        target = target(1);
    else
        fprintf(falscheingabe)
    end
elseif strcmp(Fall, 'Fall 12')
    if strcmp(RunetypeOD, 'Kraft')
        VerwendeteRune = 'Infiltration';
        target = target(1);
    elseif strcmp(RunetypeOD, 'Wildheit')
        VerwendeteRune = 'Ranger';
        target = target(2);
    else
        fprintf(falscheingabe)
    end
elseif strcmp(Fall, 'Fall 13')
    VerwendeteRune = 'Ranger';
elseif strcmp(Fall, 'Fall 14')
    fprintf('Verwendet full Marauder Gear oder mehr modifier.\n')
elseif strcmp(Fall, 'Fall 15')
    if strcmp(Runetype, 'Fullkraft') || strcmp(Runetype, 'Halfkraft') || strcmp(Runetype, 'Halfwild')
        VerwendeteRune = 'Scholar';
    elseif strcmp(Runetype, 'Fullwild')
        VerwendeteRune = 'Dragonhunter';
    else
        fprintf(falscheingabe)
    end
elseif strcmp(Fall, 'Fall 16')
    if strcmp(Runetype, 'Fullkraft') || strcmp(Runetype, 'Halfkraft') || strcmp(Runetype, 'Halfwild')
        VerwendeteRune = 'Scholar';
        target = target(1);
    elseif strcmp(Runetype, 'Fullwild')
        VerwendeteRune = 'Golemancer';
        target = target(2);
    else
        fprintf(falscheingabe)
    end
elseif strcmp(Fall, 'Fall 17')
    if strcmp(Runetype, 'Fullkraft') || strcmp(Runetype, 'Halfkraft')
        VerwendeteRune = 'Deadeye';
        target = target(3);
    elseif strcmp(Runetype, 'Halfwild')
        VerwendeteRune = 'Scholar';
        target = target(1);
    elseif strcmp(Runetype, 'Fullwild')
        VerwendeteRune = 'Golemancer';
        target = target(2);
    else
        fprintf(falscheingabe)
    end
elseif strcmp(Fall, 'Fall 18')
    if strcmp(Runetype, 'Fullkraft') || strcmp(Runetype, 'Halfkraft')
        VerwendeteRune = 'Deadeye';
        target = target(2);
    elseif strcmp(Runetype, 'Halfwild')
        VerwendeteRune = 'Eagle';
        target = target(3);
    elseif strcmp(Runetype, 'Fullwild')
        VerwendeteRune = 'Golemancer';
        target = target(1);
    else
        fprintf(falscheingabe)
    end
elseif strcmp(Fall, 'Fall 19')
    if strcmp(Runetype, 'Fullkraft')
        VerwendeteRune = 'Infiltration';
        target = target(4);
    elseif strcmp(Runetype, 'Halfkraft')
        VerwendeteRune = 'Deadeye';
        target = target(2);
    elseif strcmp(Runetype, 'Halfwild')
        VerwendeteRune = 'Eagle';
        target = target(3);
    elseif strcmp(Runetype, 'Fullwild')
        VerwendeteRune = 'Golemancer';
        target = target(1);
    else
        fprintf(falscheingabe)
    end
elseif strcmp(Fall, 'Fall 20')
    if strcmp(Runetype, 'Fullkraft')
        VerwendeteRune = 'Infiltration';
        target = target(3);
    elseif strcmp(Runetype, 'Halfkraft')
        VerwendeteRune = 'Ranger';
        target = target(4);
    elseif strcmp(Runetype, 'Halfwild')
        VerwendeteRune = 'Eagle';
        target = target(2);
    elseif strcmp(Runetype, 'Fullwild')
        VerwendeteRune = 'Golemancer';
        target = target(1);
    else
        fprintf(falscheingabe)
    end
else
    fprintf(falscheingabe)
end