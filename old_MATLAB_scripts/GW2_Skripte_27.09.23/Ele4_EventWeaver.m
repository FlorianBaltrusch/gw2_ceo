%% Event Weaver Skript mit 4pc 2hL Dragon als Grundlage
%% Warnung aus
warning('off','MATLAB:table:ModifiedAndSavedVarnames')

%% Exotische Zahlen importieren
Daten = readtable('All_stats.xlsx');
Pc4Maj2hL = Daten.x4pcMaj2hL;
Pc4Min2hL = Daten.x4pcMin2hL;
Pc3Min2hL = Daten.x3pcMin2hL;
Pc4Maj2hLOI = Daten.x4pcMaj2hLOI; % ohne Infusionen
Pc4Min2hLOI = Daten.x4pcMin2hLOI; % ohne Infusionen
Pc3Min2hLOI = Daten.x3pcMin2hLOI; % ohne Infusionen

%% Allg. Buffs

Base = 1000;
Fury = 25*21;
Food = 70;
Sigil = 7*21; % Target ist -63 aka. 3% zu viel, d.h. kein Sigil

%% Klasenbuffs  

SignetofFire = 180;
ZephyrsSpeed = 5*21;
SuperiorElements = 15*21;
ElementsofRage1 = 0.13*(1000 + 235 + sum(Pc4Min2hLOI));

%% Target und numbers
target = 2995 - Base - Fury - Food - SignetofFire - ZephyrsSpeed - SuperiorElements - ElementsofRage1 - sum(Pc4Min2hL);
% disp('Target:');
% disp(target);

%% Weaver ganzzahlig machen
target = 1 - 0.29; % Wenn ElementsofRage1 = 238,29, dann ist es mit target = 0.1 danach x,39
neuenumbers = Pc3Min2hLOI - Pc4Min2hLOI;
ganzzahlignumbers = 0.13.* (Pc3Min2hLOI - Pc4Min2hLOI); % Unser Target ist -179,9. Wenn Drag = 1,9 und Valk = 1 ist, dann hätten wirs

% Erstelle eine leere Liste, um die Kombinationen aufzunehmen
Kombinationen = {};
 
% Iteriere solange, bis eine Kombination gefunden wurde, die das Ziel erreicht
while true
    % Filtern Sie die Zahlenliste, um alle Elemente zu entfernen, die größer als das Ziel sind
    numbers_filtered = ganzzahlignumbers(ganzzahlignumbers <= target);

    % Iteriere durch alle möglichen Anzahlen von Elementen in einer Kombination
    for num_elements = 1:length(numbers_filtered)
        % Erstelle alle möglichen Kombinationen mit num_elements Elementen
        alle_Kombinationen = nchoosek(numbers_filtered, num_elements);

        % Iteriere durch alle öKombinationen
        for i = 1:size(alle_Kombinationen, 1)
            Kombination = alle_Kombinationen(i, :);

            % Prüfe, ob die Kombination das Ziel erreicht und noch nicht in der Liste enthalten ist
            if sum(Kombination) == target
                % Iteriere durch alle bisherigen Kombinationen
                is_duplicate = false;
                for j = 1:size(Kombinationen, 1)
                    % Prüfe, ob die Kombination bereits in der Liste enthalten ist
                    if isequal(Kombination, Kombinationen{j, :})
                        is_duplicate = true;
                        break;
                    end
                end

                % Füge die Kombination zur Liste hinzu, wenn sie noch nicht enthalten ist
                if ~is_duplicate
                    Kombinationen = [Kombinationen; Kombination]; %#ok<AGROW>
                end

                % Beende die Schleife, wenn eine Kombination gefunden wurde, die das Ziel erreicht
                break;
            end
        end
    end

    % Erhöhe das Ziel um 1, falls keine Kombination gefunden wurde, die das Ziel erreicht
    if isempty(Kombinationen)
        target = target +1;
        disp(target)
    else
        % Beende die Schleife, wenn eine Kombination gefunden wurde, die das Ziel erreicht
        break;
    end
end

% Alle Zeilen, die Nullen enthalten, entfernen
Nullen = any(cell2mat(cellfun(@(x) any(x==0), Kombinationen, 'UniformOutput', false)), 2);
KombinationenohneNullen = Kombinationen(~Nullen);
disp(KombinationenohneNullen);
disp(target);

%% Welche Rüstungsteile sind walkürisch?

% Verwende cellfun, um die Multiplikation auf jedes Element anzuwenden
DragminusWalk = cellfun(@(x) round(x * 100/13), KombinationenohneNullen, 'UniformOutput', false);

% Das Ergebnis ist jetzt in resultCellArray gespeichert
disp(DragminusWalk);

% combinationsohenneullen = DragminusWalk
% numbers = neuenumbers da wo die Zahlen aus DragminusWalk drinne vorkommen
% Namenliste = Walknamenliste

Tabelle = readtable('Zuordnung.xlsx');
Namen = Tabelle.Namen;

% Initialisiere ein leeres Cell-Array, um die modifizierten Zeilen zu speichern
Walknamenliste = cell(size(DragminusWalk));

% Erstelle eine Map, um die Zuordnung von Zahlen zu Zeilen in neuenumbers zu speichern
zuordnungsMap = containers.Map(neuenumbers, 1:length(neuenumbers));

% Schleife durch die Zellen in ausgewaehlteZeilen2
for i = 1:numel(DragminusWalk)
    zeile = DragminusWalk{i}; % Aktuelle Zelle auswählen
    
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
            enda
    end
    
    % Speichere die modifizierte Zeile in Walknamenliste
    Walknamenliste{i} = modifizierteZeile;
    end
end

% Ausgabe von Walknamenliste in der gewünschten Formatierung
disp('Namen der walkürischen Rüstungsteile:');
for i = 1:numel(Walknamenliste)
    fprintf('{[ %s ]}\n', strjoin(Walknamenliste{i}, ' '));
end

%% Target mit walkürischen Rüstungen

Drag = Daten.Drag;
Walk = Daten.Walk;
ElementsofRage2 = 0.13*(1000 + 235 + sum(Drag) + sum(Walk));
target = 2995 - Base - Fury - Food - SignetofFire - ZephyrsSpeed - SuperiorElements - ElementsofRage2 - sum(Drag);
disp('Target:');
disp(target);

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

Mara = Daten.Mara;
numbers = Mara - Drag; % Min - Maj wenn target negativ ist, also Kraft Infu, wenn da kein Infu steht, weil Dragon Grundlage

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

%% Juwelenfilter 

% % Initialisiere ein leeres Cell-Array für modifiziertesArray2
% modifiziertesArray2 = {};
% 
% % Schleife durch die Zeilen des bereits erstellten modifizierten Arrays (modifiziertesArray)
% for i = 1:numel(modifiziertesArray)
%     % Hole die Zeile aus modifiziertesArray
%     zeile = modifiziertesArray{i};
% 
%     % Zähle das Vorkommen von 'Access', 'L/R' und 'Am/W2' in der aktuellen Zeile
%     accessCount = 0;
%     lrCount = 0;
%     amw2Count = 0;
%     backCount = 0;
%     for j = 1:numel(zeile)
%         worte = zeile{j};
%         accessCount = accessCount + sum(contains(worte, 'Access'));
%         lrCount = lrCount + sum(contains(worte, 'L/R'));
%         amw2Count = amw2Count + sum(contains(worte, 'Am/W2'));
%         backCount = backCount + sum(contains(worte, 'Back'));
%     end
% 
%     % Zähle die Anzahl von 'Jew' in der aktuellen Zeile
%     jewCount = sum(contains(zeile, 'Jew'));
% 
%     % Überprüfe die zusätzliche Regel für modifiziertesArray2
%     if ((accessCount + lrCount + amw2Count + backCount == jewCount) || (accessCount + lrCount + amw2Count == jewCount))
%         modifiziertesArray2 = [modifiziertesArray2; {zeile}]; % Als separate Zelle hinzufügen
%     end
% end
% 
% % Schleife durch die Zeilen des bereits erstellten modifizierten Arrays (modifiziertesArray)
% for i = 1:numel(modifiziertesArray)
%     % Hole die Zeile aus modifiziertesArray
%     zeile = modifiziertesArray{i};
% 
%     % Zähle die Anzahl von 'Jew' in der aktuellen Zeile
%     jewCount = sum(contains(zeile, 'Jew'));
% 
%     % Überprüfe die Bedingungen für modifiziertesArray2
%     if (jewCount == 0 || jewCount == 1 || jewCount == 6)
%         modifiziertesArray2 = [modifiziertesArray2; {zeile}]; % Als separate Zelle hinzufügen
%     end
% end
% 
% disp('Sinnvolle Juwelenanzahl:');
% for i = 1:numel(modifiziertesArray2)
%     fprintf('{[ %s ]}\n', strjoin(modifiziertesArray2{i}, ' '));
% end

%% Namensliste nach Geschmack filtern

% Initialisiere ein leeres Cell-Array für das modifizierte Array
Infusionsarray = {};

% Schleife durch die Zeilen des Namenliste-Arrays
for i = 1:numel(modifiziertesArray)
    % Zähle das Vorkommen von 'S/G/B' und 'Access' in der aktuellen Zeile
    zeile = modifiziertesArray{i};
    Infu = 0;
    for j = 1:numel(zeile)
        worte = zeile{j};
        Infu = Infu + sum(contains(worte, 'Infu'));
    end
    
    % Überprüfe die Bedingungen und füge die Zeile dem modifizierten Array hinzu
    if (Infu == 2) % In dem Fall werden die Möglichkeiten mit Präzi-Infusion angezeigt
        Infusionsarray = [Infusionsarray; {zeile}]; % Als separate Zelle hinzufügen
    end
end

disp('Mit Präzi-Infusion:');
for i = 1:numel(Infusionsarray)
    fprintf('{[ %s ]}\n', strjoin(Infusionsarray{i}, ' '));
end
