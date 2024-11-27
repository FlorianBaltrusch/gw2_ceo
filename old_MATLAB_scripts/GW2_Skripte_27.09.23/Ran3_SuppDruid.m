%% Supp Druid Skript mit 3pc 2hL Harrier als Grundlage
%% Warnung aus
warning('off','MATLAB:table:ModifiedAndSavedVarnames')

%% Exotische Zahlen importieren
Daten = readtable('All_stats.xlsx');
% Pc4Maj1h = Daten.x3pcMaj1h;
Pc3Min2hL = Daten.StaffScourge; % Gilt auch für Druid

%% Allg. Buffs

Food = 70;
Sigil = 10*15; % Konzentration
Rune = 15*15; % Mönch

%% Klasenbuffs

LingeringMagic = 240;

%% Target und numbers
target = 1500 - Food - Sigil - Rune - LingeringMagic - sum(Pc3Min2hL);
disp('Target:');
disp(target);

numbers = - Pc3Min2hL; % Es wird gegen Magi (ohne Konz.) getauscht

%% Kombinationen finden und target \pm 1, wenn nichts gefunden wurde

while true

    % Erstelle eine leere Liste, um die Kombinationen aufzunehmen
    combinations = {};

    % Flag, um festzustellen, ob eine Kombination gefunden wurde
    combination_found = false;

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
                    combination_found = true;
                end
            end
        end
    end

    % Wenn eine Kombination gefunden wurde, beende die Schleife
    if combination_found
        break;
    else
        % Wenn keine Kombination gefunden wurde, erhöhe das target um eins,
        % wenn target negativ, sonst minus eins, wenn target positiv
        target = target + 1;
        disp(['Neues Target:' num2str(target)]);
    end
end
    % Drucke die gefundenen Kombinationen ohne Nullen aus

    Nullen = any(cell2mat(cellfun(@(x) any(x==0), combinations, 'UniformOutput', false)), 2);
    combinationsohnenullen = combinations(~Nullen);
    disp('Kombinationen ohne  Nullen:');
    disp(combinationsohnenullen);

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

%% Es gibt keine Magi Juwelen sondern nur Wappen, aber wir müssen mind. 2 tauschen

% % Initialisiere ein leeres Cell-Array für das modifizierte Array
% modifiziertesArray = {};
% 
% % Schleife durch die Zeilen des Namenliste-Arrays
% for i = 1:numel(Namenliste)
%     % Zähle das Vorkommen von 'S/G/B' und 'Access' in der aktuellen Zeile
%     zeile = Namenliste{i};
%     sgbs = 0;
%     access = 0;
%     for j = 1:numel(zeile)
%         worte = zeile{j};
%         sgbs = sgbs + sum(contains(worte, 'S/G/B'));
%         access = access + sum(contains(worte, 'Access'));
%     end
% 
%     % Überprüfe die Bedingungen und füge die Zeile dem modifizierten Array hinzu
%     if (sgbs == 0 || sgbs == 3) && (access == 0 || access == 2)
%         modifiziertesArray = [modifiziertesArray; {zeile}]; % Als separate Zelle hinzufügen
%     end
% end
% 
% disp('Namen ausgewählter Rüstungsteile:');
% for i = 1:numel(modifiziertesArray)
%     fprintf('{[ %s ]}\n', strjoin(modifiziertesArray{i}, ' '));
% end
% 
% %% Infusionsarray

% % Initialisiere ein leeres Cell-Array für das modifizierte Array
% Infusionsarray = {};
% 
% % Schleife durch die Zeilen des Namenliste-Arrays
% for i = 1:numel(modifiziertesArray)
%     % Zähle das Vorkommen von 'S/G/B' und 'Access' in der aktuellen Zeile
%     zeile = modifiziertesArray{i};
%     Infu = 0;
%     for j = 1:numel(zeile)
%         worte = zeile{j};
%         Infu = Infu + sum(contains(worte, 'Infu'));
%     end
% 
%     % Überprüfe die Bedingungen und füge die Zeile dem modifizierten Array hinzu
%     if (Infu == 2) % In dem Fall werden die Möglichkeiten mit 2 Heilkraft-Infusion angezeigt
%         Infusionsarray = [Infusionsarray; {zeile}]; % Als separate Zelle hinzufügen
%     end
% end
% 
% disp('Mit Kraft-Infusion:');
% for i = 1:numel(Infusionsarray)
%     fprintf('{[ %s ]}\n', strjoin(Infusionsarray{i}, ' '));
% end