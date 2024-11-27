%% OW Minion Master Skript mit 4pc 2h Marauder als Grundlage
%% Warnung aus
warning('off','MATLAB:table:ModifiedAndSavedVarnames')

%% Exotische Zahlen importieren
Daten = readtable('All_stats.xlsx');
Pc4Maj2h = Daten.x4pcMaj2h;
Pc4Min2h = Daten.x4pcMin2h;

%% Allg. Buffs

Base = 1000;
Fury = 25*21;
Food = 70;
Sigil = 7*21;

%% Klasenbuffs

 DeathPerception = 15*21;

%% Target und numbers
target = 2995 - Base - Fury - Food - Sigil - DeathPerception - sum(Pc4Maj2h);
% disp('Target:');
% disp(target);

%% Rune je nach target

Scholar = 0; % Power/Ferocity (175/225)
% Dragonhunter = 0; % Ferocity/Power (300/100)
% Golemancer = 100; % Ferocity/Precision (300/100)
Deadeye = 125; % Power/Ferocity + (Precision) (175/100/125)
% Eagle = 175; % Precision/Ferocity (175/225)
Infiltration = 225; % Power/Precision (175/225)
% Ranger = 300; % Precision/Ferocity (300/100)

target = target - Scholar; % Anderer Rune, wenn man mit keiner Lösung zufrieden ist
disp('Target:');
disp(target);

numbers = Pc4Min2h - Pc4Maj2h; % Min - Maj wenn target negativ ist

% if target < 125
%     result = target - Scholar;
% elseif target < 175
%     result = target - Deadeye;
% elseif target < 225
%     result = target - Eagle;
% elseif target < 300
%     result = target - Infiltration;
% else
%     result = target - Ranger;
% end
%% Kombinationen finden

    % Erstelle eine leere Liste, um die Kombinationen aufzunehmen
    combinations = {};

    % Iteriere durch alle möglichen Kombinationen von Zahlen
    for num_elements = 1:length(numbers)
        % Erstelle alle möglichen Kombinationen mit num_elements Elementen
        all_combinations = nchoosek(numbers, num_elements);

        % Iteriere durch alle Kombinationen
        for i = 1:size(all_combinations, 1)
            combination = all_combinations(i, :);

            % Prüfe, ob die Kombination das target erreicht und noch nicht in der Liste enthalten ist
            if sum(combination) == target
                % Sortiere die Kombination, um Duplikate zu erkennen
                combination = sort(combination);

                % Iteriere durch alle bisherigen Kombinationen
                is_duplicate = false;
                for j = 1:size(combinations, 1)
                    % Prüfe, ob die Kombination bereits in der Liste enthalten ist
                    if isequal(combination, combinations{j, :})
                        is_duplicate = true;
                        break;
                    end
                end

                % Füge die Kombination zur Liste hinzu, wenn sie noch nicht enthalten ist
                if ~is_duplicate
                    combinations = [combinations; combination]; %#ok<AGROW>
                end
            end
        end
    end

    % Drucke die gefundenen Kombinationen ohne Nullen aus

    Nullen = any(cell2mat(cellfun(@(x) any(x==0), combinations, 'UniformOutput', false)), 2);
    combinationsohnenullen = combinations(~Nullen);
    disp('Kombinationen ohne  Nullen:');
    disp(combinationsohnenullen);


    %% combinationsohnenullen filtern

% andererVektor = Pc4Maj1h; % Der Vektor, wo vermutlich die Kraftwerte drinnestehen
% langesArray = combinationsohnenullen;
% 
% % Initialisiere Variablen für die Zeile(n) mit der höchsten Summe
% maxSum = -inf; % Anfangswert für die maximale Summe
% ausgewaehlteZeilen = {};
% 
% % Durchlaufe die Zeilen in langesArray
% for i = 1:numel(langesArray)
%     zeile = langesArray{i};
% 
%     % Initialisiere die Zeilensumme
%     zeilenSumme = 0;
% 
%     % Durchlaufe die Werte in der Zeile
%     for j = 1:numel(zeile)
%         wert = zeile(j);
% 
%         % Finde die Zeilennummer in andererVektor basierend auf numbers
%         zeilenNummer = find(numbers == wert, 1); % Nur den ersten gefundenen Wert verwenden
% 
%         % Überprüfe, ob ein Wert gefunden wurde
%         if ~isempty(zeilenNummer)
%             % Addiere den Wert aus andererVektor zur Zeilensumme
%             zeilenSumme = zeilenSumme + andererVektor(zeilenNummer);
%         else
%             fprintf('Wert %d wurde nicht in "numbers" gefunden.\n', wert);
%         end
%     end
% 
%     % Überprüfe, ob die Zeilensumme größer oder gleich der maximalen Summe ist
%     if zeilenSumme >= maxSum
%         % Wenn ja, aktualisiere die maximale Summe und speichere die Zeile
%         if zeilenSumme > maxSum
%             maxSum = zeilenSumme;
%             ausgewaehlteZeilen = {zeile};
%         else
%             % Wenn die Summe gleich der maximalen Summe ist, füge die Zeile hinzu
%             ausgewaehlteZeilen{end+1} = zeile;
%         end
%     end
% end
% 
% % Ergebnis anzeigen
% disp('Beste Kombinationen:');
% disp(ausgewaehlteZeilen');

    %% Namen hinzufügen

% Tabelle = readtable('Zuordnung.xlsx');
% Namen = Tabelle.Namen;
% 
% % Initialisiere ein leeres Cell-Array, um die modifizierten Zeilen zu speichern
% Namenliste = cell(size(ausgewaehlteZeilen));
% 
% % Erstelle eine Map, um die Zuordnung von Zahlen zu Zeilen in numbers zu speichern
% zuordnungsMap = containers.Map(numbers, 1:length(numbers));
% 
% % Schleife durch die Zellen in ausgewaehlteZeilen2
% for i = 1:numel(ausgewaehlteZeilen)
%     zeile = ausgewaehlteZeilen{i}; % Aktuelle Zelle auswählen
% 
%     % Initialisiere eine leere Zelle für die modifizierte Zeile
%     modifizierteZeile = cell(size(zeile));
% 
%     % Schleife durch die Elemente in der aktuellen Zelle
%     for j = 1:numel(zeile)
%         zahl = zeile(j); % Aktuelle Zahl auswählen
% 
%         % Überprüfe, ob die Zahl in der Zuordnungsmap vorhanden ist
%         if isKey(zuordnungsMap, zahl)
%             % Wenn die Zahl gefunden wird, ersetze sie durch das entsprechende Wort aus Namen
%             zeilenIndex = zuordnungsMap(zahl);
%             modifizierteZeile{j} = Namen{zeilenIndex};
%         else
%             % Wenn die Zahl nicht gefunden wird, belasse sie unverändert
%             modifizierteZeile{j} = num2str(zahl);
%         end
%     end
% 
%     % Speichere die modifizierte Zeile in Namenliste
%     Namenliste{i} = modifizierteZeile;
% end
% 
% % Ausgabe von Namenliste in der gewünschten Formatierung
% disp('Namen der Rüstungsteile:');
% for i = 1:numel(Namenliste)
%     fprintf('{[ %s ]}\n', strjoin(Namenliste{i}, ' '));
% end

 %% Namen hinzufügen

Tabelle = readtable('Zuordnung.xlsx');
Namen = Tabelle.Namen;

% Initialisiere ein leeres Cell-Array, um die modifizierten Zeilen zu speichern
Namenliste = cell(size(combinationsohnenullen));

% Erstelle eine Map, um die Zuordnung von Zahlen zu Zeilen in numbers zu speichern
zuordnungsMap = containers.Map(numbers, 1:length(numbers));

% Schleife durch die Zellen in ausgewaehlteZeilen2
for i = 1:numel(combinationsohnenullen)
    zeile = combinationsohnenullen{i}; % Aktuelle Zelle auswählen
    
    % Initialisiere eine leere Zelle für die modifizierte Zeile
    modifizierteZeile = cell(size(zeile));
    
    % Schleife durch die Elemente in der aktuellen Zelle
    for j = 1:numel(zeile)
        zahl = zeile(j); % Aktuelle Zahl auswählen
        
        % Überprüfe, ob die Zahl in der Zuordnungsmap vorhanden ist
        if isKey(zuordnungsMap, zahl)
            % Wenn die Zahl gefunden wird, ersetze sie durch das entsprechende Wort aus Namen
            zeilenIndex = zuordnungsMap(zahl);
            modifizierteZeile{j} = Namen{zeilenIndex};
        else
            % Wenn die Zahl nicht gefunden wird, belasse sie unverändert
            modifizierteZeile{j} = num2str(zahl);
        end
    end
    
    % Speichere die modifizierte Zeile in Namenliste
    Namenliste{i} = modifizierteZeile;
end

% Ausgabe von Namenliste in der gewünschten Formatierung
disp('Namen der Rüstungsteile:');
for i = 1:numel(Namenliste)
    fprintf('{[ %s ]}\n', strjoin(Namenliste{i}, ' '));
end


%% Namensliste nach Geschmack filtern

% Initialisiere ein leeres Cell-Array für das modifizierte Array
modifiziertesArray = {};

% Schleife durch die Zeilen des Namenliste-Arrays
for i = 1:numel(Namenliste)
    % Zähle das Vorkommen von 'S/G/B' und 'Access' in der aktuellen Zeile
    zeile = Namenliste{i};
    sgbs = 0;
    access = 0;
    for j = 1:numel(zeile)
        worte = zeile{j};
        sgbs = sgbs + sum(contains(worte, 'S/G/B'));
        access = access + sum(contains(worte, 'Access'));
    end
    
    % Überprüfe die Bedingungen und füge die Zeile dem modifizierten Array hinzu
    if (sgbs == 0 || sgbs == 3) && (access == 0 || access == 2)
        modifiziertesArray = [modifiziertesArray; {zeile}]; % Als separate Zelle hinzufügen
    end
end

disp('Namen ausgewählter Rüstungsteile:');
for i = 1:numel(modifiziertesArray)
    fprintf('{[ %s ]}\n', strjoin(modifiziertesArray{i}, ' '));
end

