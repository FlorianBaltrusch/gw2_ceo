%% Weaver ganzzahlig machen
%% Warnung aus
warning('off','MATLAB:table:ModifiedAndSavedVarnames')

%% Exotische Zahlen importieren
Daten = readtable('All_stats.xlsx');
Pc4Maj2hL = Daten.x4pcMaj1hL;
Pc4Min2hL = Daten.x4pcMin1hL;
Pc3Min2hL = Daten.x3pcMin2hL;
Pc4Maj2hLOI = Daten.x4pcMaj1hLOI; % ohne Infusionen
Pc4Min2hLOI = Daten.x4pcMin1hLOI; % ohne Infusionen
Pc3Min2hLOI = Daten.x3pcMin2hLOI; % ohne Infusionen

target = 0.9; 
numbers = 0.13.* (abs(Pc4Min2hLOI - Pc3Min2hLOI)); % Unser Target ist -179,9. Wenn Drag = 1,9 und Valk = 1 ist, dann hätten wirs

%% Lange Berechnung

% Erstelle eine leere Liste, um die Kombinationen aufzunehmen
combinations = {};

% Iteriere solange, bis eine Kombination gefunden wurde, die das Ziel erreicht
while true
    % Filtern Sie die Zahlenliste, um alle Elemente zu entfernen, die größer als das Ziel sind
    numbers_filtered = numbers(numbers <= target);

    % Iteriere durch alle möglichen Anzahlen von Elementen in einer Kombination
    for num_elements = 1:length(numbers_filtered)
        % Erstelle alle möglichen Kombinationen mit num_elements Elementen
        all_combinations = nchoosek(numbers_filtered, num_elements);

        % Iteriere durch alle öKombinationen
        for i = 1:size(all_combinations, 1)
            combination = all_combinations(i, :);

            % Prüfe, ob die Kombination das Ziel erreicht und noch nicht in der Liste enthalten ist
            if sum(combination) == target
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

                % Beende die Schleife, wenn eine Kombination gefunden wurde, die das Ziel erreicht
                break;
            end
        end
    end

    % Erhöhe das Ziel um 1, falls keine Kombination gefunden wurde, die das Ziel erreicht
    if isempty(combinations)
        target = target +1;
        disp(target)
    else
        % Beende die Schleife, wenn eine Kombination gefunden wurde, die das Ziel erreicht
        break;
    end
end

% Alle Zeilen, die Nullen enthalten, entfernen
Nullen = any(cell2mat(cellfun(@(x) any(x==0), combinations, 'UniformOutput', false)), 2);
combinationsohnenullen = combinations(~Nullen);
disp(combinationsohnenullen);
disp(target);