%% Kombinationen das erste mal filtern
modifiziertesArray = {};
for i = 1:numel(Namenliste)
    zeile = Namenliste{i};
    sgbs = 0;
    access = 0;
    for j = 1:numel(zeile)
        worte = zeile{j};
        sgbs = sgbs + sum(contains(worte, 'S/G/B'));
        access = access + sum(contains(worte, 'Access'));
    end
    if (sgbs == 0 || sgbs == 3) && (access == 0 || access == 2)
        modifiziertesArray = [modifiziertesArray; {zeile}];
    end
end

% disp('Namen ausgewählter Rüstungsteile:');
% for i = 1:numel(modifiziertesArray)
%     fprintf('{[ %s ]}\n', strjoin(modifiziertesArray{i}, ' '));
% end

%% Kombinationen das zweite mal filtern
modifiziertesArray2 = {};
for i = 1:numel(modifiziertesArray)
    zeile = modifiziertesArray{i};
    accessCount = 0;
    lrCount = 0;
    amw2Count = 0;
    backCount = 0;
    for j = 1:numel(zeile)
        worte = zeile{j};
        accessCount = accessCount + sum(contains(worte, 'Access'));
        lrCount = lrCount + sum(contains(worte, 'L/R'));
        amw2Count = amw2Count + sum(contains(worte, 'Am/W2'));
        backCount = backCount + sum(contains(worte, 'Back'));
    end
    jewCount = sum(contains(zeile, 'Jew'));
    if accessCount + lrCount + amw2Count + backCount == jewCount || accessCount + lrCount + amw2Count == jewCount || backCount == jewCount 
        modifiziertesArray2 = [modifiziertesArray2; {zeile}];
    end
end
for i = 1:numel(modifiziertesArray)
    zeile = modifiziertesArray{i};
    jewCount = sum(contains(zeile, 'Jew'));
    if (jewCount == 0 || jewCount == 1 || jewCount == 6)
        modifiziertesArray2 = [modifiziertesArray2; {zeile}]; % Als separate Zelle hinzufügen
    end
end

disp('Namen ausgewählter Rüstungsteile mit sinnvoller Juwelenanzahl:');
for i = 1:numel(modifiziertesArray2)
    fprintf('{[ %s ]}\n', strjoin(modifiziertesArray2{i}, ' '));
end

%% Andere Informationen zum Build:
fprintf("\nIhr verwendet das %s-Sigill und die %s-Rune\n", VerwendetesSigil, VerwendeteRune);