%% Numbers
if target == 0
    numbers = Nullvektor;
    fprintf('Das war eine Punktlandung. Herzlichen Glückwunsch!')
elseif strcmp(Basegear, 'Dragon') && target < 0
    numbers = Nullvektor;
elseif strcmp(Basegear, 'Dragon') && target > 0
    numbers = Highgear - Lowgear;
elseif strcmp(Basegear, 'Marauder') && target < 0
    numbers = Lowgear - Highgear;
elseif strcmp(Basegear, 'Marauder') && target > 0
    numbers = Highgear - Lowgear;
elseif strcmp(Basegear, 'Berserker') && target < 0
    Highgear = Lowgear;
    Lowgear = Nullvektor;
    numbers = Lowgear - Highgear;
elseif strcmp(Basegear, 'Berserker') && target > 0
    numbers = Highgear - Lowgear;
else
    fprintf(falscheingabe);
end

%% Kombinationen finden
combinations = {};
for num_elements = 1:length(numbers)
    all_combinations = nchoosek(numbers, num_elements);
    for i = 1:size(all_combinations, 1)
        combination = all_combinations(i, :);
        if sum(combination) == target
            combination = sort(combination);
            is_duplicate = false;
            for j = 1:size(combinations, 1)
                if isequal(combination, combinations{j, :})
                    is_duplicate = true;
                    break;
                end
            end
            if ~is_duplicate
                combinations = [combinations; combination];
            end
        end
    end
end

%% Kombinationen anzeigen
    Nullen = any(cell2mat(cellfun(@(x) any(x==0), combinations, 'UniformOutput', false)), 2);
    combinationsohnenullen = combinations(~Nullen);
    % disp('Kombinationen ohne  Nullen:');
    % disp(combinationsohnenullen);

%% Namen hinzufügen
Namen = Tabelle.Namen;
Namenliste = cell(size(combinationsohnenullen));
zuordnungsMap = containers.Map(numbers, 1:length(numbers));
for i = 1:numel(combinationsohnenullen)
    zeile = combinationsohnenullen{i}; 
    modifizierteZeile = cell(size(zeile));
    for j = 1:numel(zeile)
        zahl = zeile(j); 
        if isKey(zuordnungsMap, zahl)
            zeilenIndex = zuordnungsMap(zahl);
            modifizierteZeile{j} = Namen{zeilenIndex};
        else
            modifizierteZeile{j} = num2str(zahl);
        end
    end
    Namenliste{i} = modifizierteZeile;
end

% disp('Namen der Rüstungsteile:');
% for i = 1:numel(Namenliste)
%     fprintf('{[ %s ]}\n', strjoin(Namenliste{i}, ' '));
% end