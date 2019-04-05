%% Modified matlab script from wikipedia
% Licensed as CC0 by wikipedia user Jahobr
%
% References
% ----------
% https://de.wikipedia.org/wiki/Datei:Kennfeld_Wasserturbinen.svg
% by Jahobr 2017-01-10

flowRange   = [0.02 1000]; % x
heightRange = [0.2 2000]; % y

%% ##################### Data #########################

%% Pelton Turbine
%             flow  height
PelDubble =  [0.5   110 % Source Voith / Dubbel
              30    250
              50    700
              30    1000
              5     1900
              0.5   1900];
PelBieudron = [5    1900 % connect in with Dubble Area
               5    700  % connect in with Dubble Area
              50    700  % connect in with Dubble Area
              25    1900]; % 2010 Record [[w:en:Bieudron_Hydroelectric_Power_Station]]
PelAndritz = [0.038 60   % Source Andritz
              5     60
              12    300
              3.5   1000
              0.02  1000
              0.02  115];


%% Kaplan Turbine
%             flow    height
KapDubbel =  [1.5     2 % Source Voith / Dubbel
              50      2
              1400    16
              750     30
              50      70 % top
              12      70 % top
              1       12
              1       3];
KapAndritz = [1.1     2 % Source Andritz
              40      2
              40      4
              10.8    30
              4       30
              0.5     7
              0.5     4.5];

%% Francis Turbine
%             flow   height
FraDubbel =  [0.8    10 % Source Voith / Dubbel
              50     10
              1600   70
              340    340
              80     800
              5      800
              0.8    200];
FraAndritz = [0.33   7 % Source Andritz
              2      7
              8      40
              7      150
              2      150
              0.2    35
              0.2    11.5];

%% Cross-flow or Ossberger   
%             flow  height
Ossberger =  [0.8   2.5  % source http://www.ossberger.de/cms/fileadmin/user_upload/1-1-02.pdf
              7     3.5
              12    10   % right
              12    25   % right
              7     85
              4     120
              0.2   200  % top
              0.05  200  % top
              0.04  100  % left
              0.04  50]; % left

%% Wasserrad
%            flow          height
Wasserrad = [flowRange(1)  heightRange(1) % left bottom
             5             heightRange(1) % right bottom
             5             1              % right
             3             2    % corner zuppinger
             1.4           4.2  % RSW/MWS
             0.75          8    % OSW/RWS
             0.5           12   % top
             flowRange(1)  12]; % top

%% OSW
%       flow           height
OSW =  [flowRange(1)   2.6 % left bottom
        0.4            2.6
        0.75           8
        0.5            12
        flowRange(1)   12];

%% RSW
%      flow           height
RSW = [0.4            2.6 % left
       1.4            4.2 % right
       0.75           8]; % top

%% MSW
%      flow           height
MSW = [flowRange(1)   1.5
       3              2
       1.4            4.2
       0.4            2.6
       flowRange(1)   2.6];

%% Zulppinger
%             flow           height
Zulppinger = [flowRange(1)   0.5
              5              1
              3              2
              flowRange(1)   1.5];

%% USW
%      flow          height
USW = [flowRange(1)  heightRange(1)
       5             heightRange(1)
       5             1
       flowRange(1)  0.5];


%% Archimedes Screw
%        flow    height
Screw =  [0.25   1   % left bottom
          10     1   % right bottom
          10     9   % right top  
          0.25   9]; % left top

%% VLH Kaplan 
%       flow  height
VLH =  [10    1.5   % left bottom %   % http://www.vlh-turbine.com/gamma
        10    4.5   % right bottom
        27    4.5   % right top  
        27    1.5]; % left top  

%% DIVE-Turbine
DIVE =  [1.95  2   % left bottom %   % http://www.dive-turbine.de/pages/de/technologie/einsatzbereich.php
         30     2   % right bottom
         40     6   % right
         9.6    25  % right top  
         0.6    25  % left top  
         0.6    6]; % left   

clear flowRange heightRange
save -6 turbines.mat
