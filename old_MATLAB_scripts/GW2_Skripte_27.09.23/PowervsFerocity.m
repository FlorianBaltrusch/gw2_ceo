%% ACHTUNG! Es gibt Buffs, die nicht im Charakter Sheet stehen

% Mesmer: 
% FencersFinesse = 150 Ferocity
% SuperiorityComplex = 25*15 Ferocity (beide Teile werden nicht angezeigt)
% Chrono:
% Improved Alacrity = 10*15 Ferocity

% Ele:
% In Feuer einstimmen
% PowerOverwhelming = 150 Power (mit Macht)
% RagingStorm = 180 Ferocity (mit Wut)
% AeromancersTraining = 150 oder 300 (in Luft)
% Tempest:
% FreshAir = 250 Ferocity
% Weaver:
% 240 Power in Feuer aber auch 240 Ferocity in Luft


% Guardian: Alle werden angezeigt


%% Power vs. Ferocity allg.

Power = 2463 - 175; % Hier Wert aus Charakter Sheet ohne Rune eintragen
Ferocity = 1125 - 225 + 200 + 150; % Hier Wert aus Charakter Sheet ohne Rune eintragen

% Damit es den gleiche Effekt hat, Power um eins zu erhöhen wie Ferocity um
% eins zu erhöhen muss gelten:

% (Power + 1) * (1.5 + Ferocity/1500) = Power * (1.5 + (Ferocity + 1)/1500)

% Daraus folgt: 
% Power = Ferocity + 2250

%% Welche Rune?

% Power - Ferocity
Grenzscholar = 175 - 225; % Hat maximal Kraft (175)
Grenzdragonhunter = 100 - 300; % Mischding
Grenzgolemancer = -300; % Hat maximal Wildheit
Grenzdeadeye = 175 - 100; % Hat maximal Kraft (175)
Grenzeagle = -225; % Hat maximal Wildheit
Grenzinfiltriation = 175; % Hat maximal Kraft (175)
Grenzranger = -100; % Hat maximal Wildheit

% Golemancer, Eagel und Ranger sind Gleichwertig, da sie ihre 400 Punkte
% nur in Precision und Ferocity stecken. Das Maximum von Precision ist fest
% und er Rest geht dann in Wildheit, so wie wenn man Marauder gegen Dragon
% tauscht. 
% Genauso sind Scholor, Deadeye und Infiltration gleichwertig, da alle 175
% Power geben, und die festen 225 Punkte auf Precision und Ferocity
% aufgeteilt werden.

Grenzrune = Grenzscholar;
Schwelle = -2250 + Power + 750 - Ferocity; % 750 ist Might
% Negative Schwelle heißt, dass Power zu klein ist
disp('Kraftwert ohne Rune:');
disp(Schwelle);
Schwelle = -2250 + Power + 750 - Ferocity; % 750 ist Might
% Negative Schwelle heißt, dass Power zu klein ist

