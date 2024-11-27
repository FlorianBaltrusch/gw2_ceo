%% Warnung aus
warning('off','MATLAB:table:ModifiedAndSavedVarnames')

%% Exotische Zahlen importieren
Daten = readtable('All_stats.xlsx');

%% 3pc

Pc3Maj1h = Daten.x3pcMaj1h;
Pc3Maj2h = Daten.x3pcMaj2h;
Pc3Maj1hL = Daten.x3pcMaj1hL;
Pc3Maj2hL = Daten.x3pcMaj2hL;

Pc3Min1h = Daten.x3pcMin1h;
Pc3Min2h = Daten.x3pcMin2h;
Pc3Min1hL = Daten.x3pcMin1hL;
Pc3Min2hL = Daten.x3pcMin2hL;

%% 4pc

Pc4Maj1h = Daten.x4pcMaj1h;
Pc4Maj2h = Daten.x4pcMaj2h;
Pc4Maj1hL = Daten.x4pcMaj1hL;
Pc4Maj2hL = Daten.x4pcMaj2hL;

Pc4Min1h = Daten.x4pcMin1h;
Pc4Min2h = Daten.x4pcMin2h;
Pc4Min1hL = Daten.x4pcMin1hL;
Pc4Min2hL = Daten.x4pcMin2hL;

%% Allg. Buffs

Base = 1000;
Fury = 25*21;
Food = 70;

%% Klassenbuffs

%% Ele

%% Mes

% Buffs
QuietIntensity = 15*21;


% Mes1 OW Chrono 4pc2h
Mes1target = 2995 - Base - Fury - Food - sum(Pc4Min2h);

% Mes2 DPS Chrono 3pc2h
Mes2target = 2995 - Base - Fury - Food - sum(Pc3Min2h);

% Mes3 WVW Chrono Support
% Mes4 Condi Mirage event farm

% Mes5 OW Virtuoso 4pc1h
Mes5target = 2995 - Base - Fury - Food - QuietIntensity - sum(Pc4Min1h);

% Mes6 DPS Virtuoso 3pc1h
Mes6target = 2995 - Base - Fury - Food -QuietIntensity - sum(Pc3Min2h);

%% Rune je nach target



%% Gear auswählen

numbers = Pc3Maj1h - Pc3Min1h;
% numbers = Pc3Maj2h - Pc3Min2h;
% numbers = Pc3Maj1hL - Pc3Min1hL;
% numbers = Pc3Maj2hL - Pc3Min2hL;

% numbers = Pc4Maj1h - Pc4Min1h;
% numbers = Pc4Maj2h - Pc4Min2h;
% numbers = Pc4Maj1hL - Pc4Min1hL;
% numbers = Pc4Maj2hL - Pc4Min2hL;

%% Target bestimmen

% target=Eletarget;


% target = Mes1target;
% target = Mes2target;
% target = Mes5target;
target = Mes6target;

% target = Nectarget;
% target = Engtarget;
% target = Rantarget;
% target = Thitarget;
% target = Guatarget;


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
    % disp(combinationsohnenullen);


    %% combinationsohnenullen filtern

andererVektor = Pc3Maj1h; % Der Vektor, wo vermutlich die Kraftwerte drinnestehen
langesArray = combinationsohnenullen;

% Initialisiere Variablen für die Zeile(n) mit der höchsten Summe
maxSum = -inf; % Anfangswert für die maximale Summe
ausgewaehlteZeilen = {};

% Durchlaufe die Zeilen in langesArray
for i = 1:numel(langesArray)
    zeile = langesArray{i};
    
    % Initialisiere die Zeilensumme
    zeilenSumme = 0;
    
    % Durchlaufe die Werte in der Zeile
    for j = 1:numel(zeile)
        wert = zeile(j);
        
        % Finde die Zeilennummer in andererVektor basierend auf numbers
        zeilenNummer = find(numbers == wert, 1); % Nur den ersten gefundenen Wert verwenden
        
        % Überprüfe, ob ein Wert gefunden wurde
        if ~isempty(zeilenNummer)
            % Addiere den Wert aus andererVektor zur Zeilensumme
            zeilenSumme = zeilenSumme + andererVektor(zeilenNummer);
        else
            fprintf('Wert %d wurde nicht in "numbers" gefunden.\n', wert);
        end
    end
    
    % Überprüfe, ob die Zeilensumme größer oder gleich der maximalen Summe ist
    if zeilenSumme >= maxSum
        % Wenn ja, aktualisiere die maximale Summe und speichere die Zeile
        if zeilenSumme > maxSum
            maxSum = zeilenSumme;
            ausgewaehlteZeilen = {zeile};
        else
            % Wenn die Summe gleich der maximalen Summe ist, füge die Zeile hinzu
            ausgewaehlteZeilen{end+1} = zeile;
        end
    end
end

% Ergebnis anzeigen
disp('Ausgewählte Zeilen aus langesArray:');
disp(ausgewaehlteZeilen');

    %% Namen hinzufügen

Tabelle = readtable('Zuordnung.xlsx');
Namen = Tabelle.Namen;

andererVektor = Pc3Min1h; % Der Vektor, wo vermutlich die Wildheit drinnesteht
kurzesArray = ausgewaehlteZeilen;

% Initialisiere ein leeres Cell-Array, um die modifizierten Zeilen zu speichern
Namenliste = cell(size(ausgewaehlteZeilen));

% Erstelle eine Map, um die Zuordnung von Zahlen zu Zeilen in numbers zu speichern
zuordnungsMap = containers.Map(numbers, 1:length(numbers));

% Schleife durch die Zellen in ausgewaehlteZeilen2
for i = 1:numel(ausgewaehlteZeilen)
    zeile = ausgewaehlteZeilen{i}; % Aktuelle Zelle auswählen
    
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
for i = 1:numel(Namenliste)
    fprintf('{[ %s ]}\n', strjoin(Namenliste{i}, ' '));
end

