%% Allgemeines
run('Allgemeines.m');

%% Klasse
if Seltenheit ~= 3 && Klasse ~= 8 && Klasse ~= 9
    if Klasse == 2
        run('Mesmer_vollauto.m');
    elseif Klasse == 1
        run('Ele_vollauto.m');
    elseif Klasse == 3
        run('Necro_vollauto.m');
    elseif Klasse == 7
        run('Guardian_vollauto.m');
    elseif Klasse == 4
        run('Engi_vollauto.m');
    elseif Klasse == 6
        run('Thief_vollauto.m');
    elseif Klasse == 5
        run('Ranger_vollauto.m');
    else
        fprintf(falscheeingabe);
    end
else
    fprintf('Ihr seid zu krass.\n');
end
clc;
%% Runenbestimmung
run('Rune.m')

%% Kombinationen finden
run('Kombinationen.m')

%% Kombinationen filtern
run('Filter.m')